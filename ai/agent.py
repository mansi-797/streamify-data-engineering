from ai.tools import (
    get_streams_by_user_level,
    get_streams_by_state,
    get_top_artists,
    get_top_songs,
    analyze_state_user_levels,
)
from ai.llm import ask_llm


def run_agent(question):
    question_lower = question.lower()

    # --------------------------------
    # MULTI-STEP STATE + USER LEVEL
    # INVESTIGATION
    # --------------------------------
    if (
        (
            "state" in question_lower
            or "states" in question_lower
            or "where" in question_lower
            or "location" in question_lower
        )
        and (
            "paid" in question_lower
            or "free" in question_lower
            or "user level" in question_lower
            or "user levels" in question_lower
        )
    ):

        # Step 1: Find overall streaming activity by state.
        state_data = get_streams_by_state()

        # Step 2: Compare paid and free streaming activity.
        level_analysis = analyze_state_user_levels()

        # Keep the most relevant verified evidence.
        top_states = state_data[:5]

        paid_higher = [
            row
            for row in level_analysis
            if row["higher_streaming_level"] == "paid"
        ]

        free_higher = [
            row
            for row in level_analysis
            if row["higher_streaming_level"] == "free"
        ]

        equal = [
            row
            for row in level_analysis
            if row["higher_streaming_level"] == "equal"
        ]

        # Show the largest differences in each direction.
        largest_paid_advantage = sorted(
            paid_higher,
            key=lambda row: row["difference"],
            reverse=True,
        )[:3]

        largest_free_advantage = sorted(
            free_higher,
            key=lambda row: abs(row["difference"]),
            reverse=True,
        )[:3]

        # Build a deterministic answer from verified database results.
        # No LLM is used here because these are factual database results.
        lines = []

        lines.append("Top states by total streams:")

        for row in top_states:
            lines.append(
                f"- {row['state']}: {row['stream_count']} streams"
            )

        lines.append("")

        lines.append(
            f"Paid users generate more streams in "
            f"{len(paid_higher)} states."
        )

        lines.append(
            f"Free users generate more streams in "
            f"{len(free_higher)} states."
        )

        lines.append(
            f"Paid and free users have equal streams in "
            f"{len(equal)} states."
        )

        lines.append("")

        lines.append(
            "States with the largest paid-stream advantage:"
        )

        for row in largest_paid_advantage:
            lines.append(
                f"- {row['state']}: "
                f"paid {row['paid_streams']} streams, "
                f"free {row['free_streams']} streams."
            )

        lines.append("")

        lines.append(
            "States with the largest free-stream advantage:"
        )

        for row in largest_free_advantage:
            lines.append(
                f"- {row['state']}: "
                f"paid {row['paid_streams']} streams, "
                f"free {row['free_streams']} streams."
            )

        return "\n".join(lines)

    # --------------------------------
    # USER LEVEL ANALYSIS
    # --------------------------------
    if (
        "user level" in question_lower
        or "paid users" in question_lower
        or "free users" in question_lower
        or "paid vs free" in question_lower
    ):

        data = get_streams_by_user_level()

        paid_streams = 0
        free_streams = 0

        for row in data:

            if row["user_level"] == "paid":
                paid_streams = row["stream_count"]

            elif row["user_level"] == "free":
                free_streams = row["stream_count"]

        difference = paid_streams - free_streams

        if paid_streams > free_streams:
            higher_level = "paid"

        elif free_streams > paid_streams:
            higher_level = "free"

        else:
            higher_level = "equal"

        prompt = f"""
You are the Streamify Data Analyst.

User question:
{question}

Verified database analysis:

Paid streams: {paid_streams}
Free streams: {free_streams}
Difference: {difference}
Higher streaming level: {higher_level}

Explain these verified results.

Rules:
- Preserve all numbers exactly.
- Do not calculate anything.
- Do not add percentages.
- Do not invent information.
- The numbers represent streams, not users.
- Answer in 2 or 3 simple sentences.
"""

        return ask_llm(prompt)

    # --------------------------------
    # GEOGRAPHY ANALYSIS
    # --------------------------------
    if (
        "state" in question_lower
        or "location" in question_lower
        or "geography" in question_lower
        or "where" in question_lower
    ):

        data = get_streams_by_state()

        top_states = data[:10]

        prompt = f"""
You are the Streamify Data Analyst.

User question:
{question}

Verified database results:

{top_states}

Answer using only these results.

Rules:
- Do not invent numbers.
- Do not calculate percentages.
- Do not claim causes that are not shown by the data.
- Keep the answer concise.
"""

        return ask_llm(prompt)

    # --------------------------------
    # ARTIST ANALYSIS
    # --------------------------------
    if (
        "artist" in question_lower
        or "artists" in question_lower
        or "popular artist" in question_lower
    ):

        data = get_top_artists()

        prompt = f"""
You are the Streamify Data Analyst.

User question:
{question}

Verified database results:

{data}

Explain the relevant results.

Rules:
- Use only the provided results.
- Do not invent numbers.
- Do not calculate percentages.
- Keep the answer concise.
"""

        return ask_llm(prompt)

    # --------------------------------
    # SONG ANALYSIS
    # --------------------------------
    if (
        "song" in question_lower
        or "songs" in question_lower
        or "popular song" in question_lower
        or "most streamed" in question_lower
    ):

        data = get_top_songs()

        prompt = f"""
You are the Streamify Data Analyst.

User question:
{question}

Verified database results:

{data}

Explain the relevant results.

Rules:
- Use only the provided results.
- Do not invent numbers.
- Do not calculate percentages.
- Keep the answer concise.
"""

        return ask_llm(prompt)

    # --------------------------------
    # FALLBACK
    # --------------------------------
    return (
        "I can currently analyze Streamify data for user levels, "
        "states, artists, songs, and state-level paid vs free comparisons."
    )


if __name__ == "__main__":

    question = input(
        "Ask a question about the Streamify data: "
    )

    print("\nAI Analysis:\n")

    print(run_agent(question))
