import os

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

from ai.agent import run_agent


st.set_page_config(
    page_title="Streamify Analytics",
    page_icon="🎵",
    layout="wide",
)


DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "streamify",
    "user": "streamify",
    "password": os.getenv("STREAMIFY_PG_PASSWORD"),
}


@st.cache_data(ttl=60)
def load_stream_data():
    query = """
        SELECT
            f.ts,
            u.userid,
            u.firstname,
            u.lastname,
            u.gender,
            u.level,
            a.name AS artist,
            s.title AS song,
            l.city,
            l.statename,
            d.date
        FROM fact_streams f
        JOIN dim_users u
            ON f.userkey = u.userkey
        JOIN dim_artists a
            ON f.artistkey = a.artistkey
        JOIN dim_songs s
            ON f.songkey = s.songkey
        JOIN dim_location l
            ON f.locationkey = l.locationkey
        JOIN dim_datetime d
            ON f.datekey = d.datekey
        ORDER BY f.ts;
    """

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    df["ts"] = pd.to_datetime(df["ts"])
    df["date"] = pd.to_datetime(df["date"])

    return df


def main():

    st.title("🎵 Streamify Analytics")

    st.caption(
        "Interactive analytics dashboard for the Streamify data engineering pipeline."
    )

    try:
        df = load_stream_data()

    except Exception as exc:
        st.error("Unable to load Streamify data from PostgreSQL.")
        st.exception(exc)
        st.stop()

    # -------------------------
    # Sidebar filters
    # -------------------------
    st.sidebar.header("Filters")

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    selected_dates = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = selected_dates
        end_date = selected_dates

    levels = sorted(df["level"].dropna().unique().tolist())

    selected_levels = st.sidebar.multiselect(
        "User level",
        options=levels,
        default=levels,
    )

    genders = sorted(df["gender"].dropna().unique().tolist())

    selected_genders = st.sidebar.multiselect(
        "Gender",
        options=genders,
        default=genders,
    )

    states = sorted(df["statename"].dropna().unique().tolist())

    selected_states = st.sidebar.multiselect(
        "State",
        options=states,
        default=states,
    )

    cities = sorted(df["city"].dropna().unique().tolist())

    selected_cities = st.sidebar.multiselect(
        "City",
        options=cities,
        default=cities,
    )

    # -------------------------
    # Apply filters
    # -------------------------
    filtered_df = df[
        (df["date"].dt.date >= start_date)
        & (df["date"].dt.date <= end_date)
        & (df["level"].isin(selected_levels))
        & (df["gender"].isin(selected_genders))
        & (df["statename"].isin(selected_states))
        & (df["city"].isin(selected_cities))
    ].copy()

    # -------------------------
    # KPI calculations
    # -------------------------
    total_streams = len(filtered_df)

    unique_users = filtered_df["userid"].nunique()

    unique_artists = filtered_df["artist"].nunique()

    unique_songs = filtered_df["song"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Streams",
        f"{total_streams:,}",
    )

    col2.metric(
        "Unique Users",
        f"{unique_users:,}",
    )

    col3.metric(
        "Unique Artists",
        f"{unique_artists:,}",
    )

    col4.metric(
        "Unique Songs",
        f"{unique_songs:,}",
    )

    st.divider()

    # -------------------------
    # Hourly Stream Spike Analysis
    # -------------------------
    from ai.tools import analyze_hourly_stream_spikes

    st.divider()

    st.subheader("📈 Hourly Stream Spike Analysis")

    st.caption(
        "Identifies unusually high hourly streaming activity using a z-score threshold."
    )

    spike_results = analyze_hourly_stream_spikes()

    if spike_results:

        average_streams = spike_results[0]["average_streams"]

        highest_hour = max(
            spike_results,
            key=lambda row: row["streams"],
        )

        detected_spikes = [
            row
            for row in spike_results
            if row["is_spike"]
        ]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average hourly streams",
            f"{average_streams:.2f}",
        )

        col2.metric(
            "Highest hourly streams",
            highest_hour["streams"],
        )

        col3.metric(
            "Detected spikes",
            len(detected_spikes),
        )

        if detected_spikes:

            st.markdown("### 🔎 Detected Activity Spikes")

            spike_df = pd.DataFrame(detected_spikes)

            spike_df = spike_df[
                [
                    "hour",
                    "streams",
                    "average_streams",
                    "z_score",
                ]
            ].rename(
                columns={
                    "hour": "Hour",
                    "streams": "Streams",
                    "average_streams": "Average",
                    "z_score": "Z-Score",
                }
            )

            st.dataframe(
                spike_df,
                hide_index=True,
                width="stretch",
            )

            st.info(
                "A spike is flagged when hourly stream activity reaches "
                "a z-score of 2 or higher. This identifies statistical "
                "spikes in the available dataset and does not establish "
                "a cause for the increased activity."
            )

        else:

            st.info(
                "No hourly stream spikes were detected in the available data."
            )
    # -------------------------
    # AI Analytics Assistant
    # -------------------------
    st.subheader("🤖 AI Analytics Assistant")

    st.caption(
        "Ask questions about your Streamify data using natural language."
    )

    question = st.text_input(
        "Ask Streamify AI",
        placeholder="Example: Where are most of our streams coming from?",
    )

    if st.button("Analyze", type="primary"):

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            with st.spinner("Analyzing Streamify data..."):

                try:

                    answer = run_agent(question)

                    question_lower = question.lower()

                    # --------------------------------
                    # Investigation Trace
                    # --------------------------------
                    is_state_level_question = (
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
                    )

                    if is_state_level_question:

                        from ai.tools import (
                            get_streams_by_state,
                            analyze_state_user_levels,
                        )

                        # Step 1:
                        # Retrieve overall streaming activity by state.
                        state_data = get_streams_by_state()

                        # Step 2:
                        # Compare paid and free streaming activity.
                        level_analysis = analyze_state_user_levels()

                        st.markdown("### 🔎 Investigation Trace")

                        st.write(
                            "1. Retrieved streaming activity by state."
                        )

                        st.write(
                            "2. Compared paid and free streaming activity across states."
                        )

                        st.write(
                            "3. Generated the answer from verified database results."
                        )

                        # --------------------------------
                        # Verified Evidence
                        # --------------------------------
                        st.markdown("### 📋 Verified Evidence")

                        st.caption(
                            "Evidence retrieved directly from the Streamify PostgreSQL database."
                        )

                        evidence_df = pd.DataFrame(
                            state_data[:5]
                        )

                        evidence_df = evidence_df.rename(
                            columns={
                                "state": "State",
                                "stream_count": "Streams",
                            }
                        )

                        st.dataframe(
                            evidence_df,
                            hide_index=True,
                            width="stretch",
                        )

                        paid_count = sum(
                            1
                            for row in level_analysis
                            if row["higher_streaming_level"] == "paid"
                        )

                        free_count = sum(
                            1
                            for row in level_analysis
                            if row["higher_streaming_level"] == "free"
                        )

                        equal_count = sum(
                            1
                            for row in level_analysis
                            if row["higher_streaming_level"] == "equal"
                        )

                        col1, col2, col3 = st.columns(3)

                        col1.metric(
                            "Paid higher",
                            paid_count,
                        )

                        col2.metric(
                            "Free higher",
                            free_count,
                        )

                        col3.metric(
                            "Equal",
                            equal_count,
                        )

                    # --------------------------------
                    # Final Answer
                    # --------------------------------
                    st.markdown("### 💡 AI Insight")

                    st.write(answer)

                except Exception as exc:

                    st.error(
                        "The AI analytics assistant could not process the question."
                    )

                    st.exception(exc)

    st.divider()

    if filtered_df.empty:

        st.warning(
            "No data matches the selected filters."
        )

        st.stop()

    # -------------------------
    # Streams over time
    # -------------------------
    st.subheader("Streams Over Time")

    hourly = (
        filtered_df
        .set_index("ts")
        .resample("1h")
        .size()
        .reset_index(name="streams")
    )

    fig = px.line(
        hourly,
        x="ts",
        y="streams",
        title="Streams Over Time",
        markers=True,
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Streams",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # User level
    # -------------------------
    st.subheader("Streams by User Level")

    level_counts = (
        filtered_df["level"]
        .value_counts()
        .reset_index()
    )

    level_counts.columns = [
        "level",
        "streams",
    ]

    fig = px.bar(
        level_counts,
        x="level",
        y="streams",
        title="Streams by User Level",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # Gender
    # -------------------------
    st.subheader("Streams by Gender")

    gender_counts = (
        filtered_df["gender"]
        .value_counts()
        .reset_index()
    )

    gender_counts.columns = [
        "gender",
        "streams",
    ]

    fig = px.bar(
        gender_counts,
        x="gender",
        y="streams",
        title="Streams by Gender",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # State
    # -------------------------
    st.subheader("Streams by State")

    state_counts = (
        filtered_df["statename"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    state_counts.columns = [
        "state",
        "streams",
    ]

    fig = px.bar(
        state_counts,
        x="streams",
        y="state",
        orientation="h",
        title="Top 10 States by Streams",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # Artists
    # -------------------------
    st.subheader("Most Active Artists")

    artist_counts = (
        filtered_df["artist"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    artist_counts.columns = [
        "artist",
        "streams",
    ]

    fig = px.bar(
        artist_counts,
        x="streams",
        y="artist",
        orientation="h",
        title="Top 10 Artists by Streams",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # Songs
    # -------------------------
    st.subheader("Most Streamed Songs")

    song_counts = (
        filtered_df["song"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    song_counts.columns = [
        "song",
        "streams",
    ]

    fig = px.bar(
        song_counts,
        x="streams",
        y="song",
        orientation="h",
        title="Top 10 Songs by Streams",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    # -------------------------
    # Data Engineering Pipeline
    # -------------------------
    st.divider()

    st.subheader("🔄 Streamify Data Engineering Pipeline")

    st.caption(
        "End-to-end flow from event generation to analytical insights."
    )

    pipeline = [
        (
            "🎵 Eventsim",
            "Generates simulated music streaming events",
        ),
        (
            "📨 Kafka",
            "Ingests streaming events",
        ),
        (
            "⚡ Spark",
            "Processes streaming data",
        ),
        (
            "🗄️ Data Lake",
            "Stores processed event data",
        ),
        (
            "🐘 PostgreSQL",
            "Stores structured analytical data",
        ),
        (
            "🔧 dbt",
            "Transforms data into analytics-ready models",
        ),
        (
            "📊 Streamlit",
            "Presents interactive analytics",
        ),
    ]

    pipeline_cols = st.columns(
        len(pipeline)
    )

    for col, (stage, description) in zip(
        pipeline_cols,
        pipeline,
    ):

        with col:

            st.markdown(
                f"### {stage}"
            )

            st.caption(
                description
            )

    # -------------------------
    # Data details
    # -------------------------
    with st.expander(
        "View filtered stream data"
    ):

        display_columns = [
            "ts",
            "userid",
            "firstname",
            "lastname",
            "gender",
            "level",
            "artist",
            "song",
            "city",
            "statename",
        ]

        st.dataframe(
            filtered_df[display_columns],
            width="stretch",
        )


if __name__ == "__main__":
    main()
