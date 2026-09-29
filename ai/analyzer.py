from ai.tools import get_streams_by_user_level
from ai.llm import ask_llm


def analyze_user_levels():
    data = get_streams_by_user_level()

    paid_streams = 0
    free_streams = 0

    for row in data:
        if row["user_level"] == "paid":
            paid_streams = row["stream_count"]
        elif row["user_level"] == "free":
            free_streams = row["stream_count"]

    difference = paid_streams - free_streams

    prompt = f"""
You are an analytics assistant for a music streaming platform.

These are verified database results calculated by Python:

- Paid users generated {paid_streams} streams.
- Free users generated {free_streams} streams.
- Paid users generated {difference} more streams than free users.

Rewrite these facts in 2 simple sentences.

Rules:
- Preserve every number exactly.
- The number {difference} is a stream-count difference, NOT a percentage.
- Do not calculate anything.
- Do not add percentages.
- Do not invent information.
"""

    return ask_llm(prompt)


if __name__ == "__main__":
    print(analyze_user_levels())
