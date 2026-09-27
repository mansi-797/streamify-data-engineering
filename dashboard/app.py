import os

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st


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
            f.userkey,
            f.artistkey,
            f.songkey,
            f.locationkey,
            u.userid,
            u.firstname,
            u.lastname,
            u.gender,
            u.level,
            a.name AS artist,
            s.title AS song,
            l.city,
            l.statename,
            d.date,
            d.dayofweek,
            d.month,
            d.year,
            d.weekendflag
        FROM fact_streams f
        LEFT JOIN dim_users u
            ON f.userkey = u.userkey
        LEFT JOIN dim_artists a
            ON f.artistkey = a.artistkey
        LEFT JOIN dim_songs s
            ON f.songkey = s.songkey
        LEFT JOIN dim_location l
            ON f.locationkey = l.locationkey
        LEFT JOIN dim_datetime d
            ON f.datekey = d.datekey
        ORDER BY f.ts
    """

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    df["ts"] = pd.to_datetime(df["ts"])
    return df


def main():
    st.title("🎵 Streamify Analytics")
    st.caption("Interactive analytics built from the Streamify dbt analytical layer.")

    if not DB_CONFIG["password"]:
        st.error("STREAMIFY_PG_PASSWORD is not set.")
        st.stop()

    try:
        df = load_stream_data()
    except Exception as exc:
        st.error("Could not connect to the Streamify PostgreSQL database.")
        st.exception(exc)
        st.stop()

    if df.empty:
        st.warning("No stream data is currently available.")
        st.stop()

    # -------------------------
    # Sidebar filters
    # -------------------------
    st.sidebar.header("Filters")

    min_date = df["ts"].min().date()
    max_date = df["ts"].max().date()

    selected_dates = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = df[
            (df["ts"].dt.date >= start_date)
            & (df["ts"].dt.date <= end_date)
        ].copy()
    else:
        filtered_df = df.copy()

    levels = sorted(df["level"].dropna().unique().tolist())
    selected_levels = st.sidebar.multiselect(
        "User level",
        levels,
        default=levels,
    )

    genders = sorted(df["gender"].dropna().unique().tolist())
    selected_genders = st.sidebar.multiselect(
        "Gender",
        genders,
        default=genders,
    )

    states = sorted(df["statename"].dropna().unique().tolist())
    selected_states = st.sidebar.multiselect(
        "State",
        states,
        default=states,
    )

    cities = sorted(df["city"].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect(
        "City",
        cities,
        default=cities,
    )

    if selected_levels:
        filtered_df = filtered_df[
            filtered_df["level"].isin(selected_levels)
        ]

    if selected_genders:
        filtered_df = filtered_df[
            filtered_df["gender"].isin(selected_genders)
        ]

    if selected_states:
        filtered_df = filtered_df[
            filtered_df["statename"].isin(selected_states)
        ]

    if selected_cities:
        filtered_df = filtered_df[
            filtered_df["city"].isin(selected_cities)
        ]

    # -------------------------
    # KPI cards
    # -------------------------
    total_streams = len(filtered_df)
    unique_users = filtered_df["userkey"].nunique()
    unique_artists = filtered_df["artistkey"].nunique()
    unique_songs = filtered_df["songkey"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Streams", f"{total_streams:,}")
    col2.metric("Unique Users", f"{unique_users:,}")
    col3.metric("Unique Artists", f"{unique_artists:,}")
    col4.metric("Unique Songs", f"{unique_songs:,}")

    st.divider()

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
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

    time_fig = px.line(
        hourly,
        x="ts",
        y="streams",
        markers=True,
        labels={
            "ts": "Time",
            "streams": "Streams",
        },
    )

    time_fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
    )

    st.plotly_chart(time_fig, use_container_width=True)

    # -------------------------
    # User analysis
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Streams by User Level")

        level_df = (
            filtered_df
            .groupby("level")
            .size()
            .reset_index(name="streams")
            .sort_values("streams", ascending=False)
        )

        level_fig = px.bar(
            level_df,
            x="level",
            y="streams",
            text="streams",
            labels={
                "level": "User Level",
                "streams": "Streams",
            },
        )

        st.plotly_chart(level_fig, use_container_width=True)

    with col2:
        st.subheader("Streams by Gender")

        gender_df = (
            filtered_df
            .groupby("gender")
            .size()
            .reset_index(name="streams")
            .sort_values("streams", ascending=False)
        )

        gender_fig = px.bar(
            gender_df,
            x="gender",
            y="streams",
            text="streams",
            labels={
                "gender": "Gender",
                "streams": "Streams",
            },
        )

        st.plotly_chart(gender_fig, use_container_width=True)

    # -------------------------
    # Geographic analysis
    # -------------------------
    st.subheader("Streams by State")

    state_df = (
        filtered_df
        .groupby("statename")
        .size()
        .reset_index(name="streams")
        .sort_values("streams", ascending=False)
        .head(10)
    )

    state_fig = px.bar(
        state_df,
        x="streams",
        y="statename",
        orientation="h",
        text="streams",
        labels={
            "statename": "State",
            "streams": "Streams",
        },
    )

    state_fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=450,
    )

    st.plotly_chart(state_fig, use_container_width=True)

    # -------------------------
    # Artists and songs
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Most Active Artists")

        artist_df = (
            filtered_df
            .groupby("artist")
            .size()
            .reset_index(name="streams")
            .sort_values("streams", ascending=False)
            .head(10)
        )

        artist_fig = px.bar(
            artist_df,
            x="streams",
            y="artist",
            orientation="h",
            text="streams",
            labels={
                "artist": "Artist",
                "streams": "Streams",
            },
        )

        artist_fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=450,
        )

        st.plotly_chart(artist_fig, use_container_width=True)

    with col2:
        st.subheader("Most Streamed Songs")

        song_df = (
            filtered_df
            .groupby("song")
            .size()
            .reset_index(name="streams")
            .sort_values("streams", ascending=False)
            .head(10)
        )

        song_fig = px.bar(
            song_df,
            x="streams",
            y="song",
            orientation="h",
            text="streams",
            labels={
                "song": "Song",
                "streams": "Streams",
            },
        )

        song_fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=450,
        )

        st.plotly_chart(song_fig, use_container_width=True)

    # -------------------------
    # Data details
    # -------------------------
    with st.expander("View filtered stream data"):
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
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
