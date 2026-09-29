from ai.db import get_connection


def get_streams_by_user_level():
    conn = get_connection()

    try:
        query = """
            SELECT
                u.level,
                COUNT(*) AS stream_count
            FROM fact_streams f
            JOIN dim_users u
                ON f.userkey = u.userkey
            GROUP BY u.level
            ORDER BY stream_count DESC;
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            {
                "user_level": row[0],
                "stream_count": row[1],
            }
            for row in rows
        ]

    finally:
        conn.close()


def get_streams_by_state():
    conn = get_connection()

    try:
        query = """
            SELECT
                l.statename,
                COUNT(*) AS stream_count
            FROM fact_streams f
            JOIN dim_location l
                ON f.locationkey = l.locationkey
            GROUP BY l.statename
            ORDER BY stream_count DESC;
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            {
                "state": row[0],
                "stream_count": row[1],
            }
            for row in rows
        ]

    finally:
        conn.close()


def get_top_artists():
    conn = get_connection()

    try:
        query = """
            SELECT
                a.name AS artist,
                COUNT(*) AS stream_count
            FROM fact_streams f
            JOIN dim_artists a
                ON f.artistkey = a.artistkey
            GROUP BY a.name
            ORDER BY stream_count DESC
            LIMIT 10;
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            {
                "artist": row[0],
                "stream_count": row[1],
            }
            for row in rows
        ]

    finally:
        conn.close()


def get_top_songs():
    conn = get_connection()

    try:
        query = """
            SELECT
                s.title AS song,
                COUNT(*) AS stream_count
            FROM fact_streams f
            JOIN dim_songs s
                ON f.songkey = s.songkey
            GROUP BY s.title
            ORDER BY stream_count DESC
            LIMIT 10;
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            {
                "song": row[0],
                "stream_count": row[1],
            }
            for row in rows
        ]

    finally:
        conn.close()


def get_streams_by_state_and_user_level():
    conn = get_connection()

    try:
        query = """
            SELECT
                l.statename,
                u.level,
                COUNT(*) AS stream_count
            FROM fact_streams f
            JOIN dim_location l
                ON f.locationkey = l.locationkey
            JOIN dim_users u
                ON f.userkey = u.userkey
            GROUP BY
                l.statename,
                u.level
            ORDER BY
                l.statename,
                stream_count DESC;
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            {
                "state": row[0],
                "user_level": row[1],
                "stream_count": row[2],
            }
            for row in rows
        ]

    finally:
        conn.close()


def analyze_state_user_levels():
    """
    Compare paid and free streaming activity for every state.

    Python performs the numerical analysis so that the LLM
    receives verified results instead of calculating raw data.
    """

    data = get_streams_by_state_and_user_level()

    state_totals = {}

    for row in data:
        state = row["state"]
        level = row["user_level"]
        streams = row["stream_count"]

        if state not in state_totals:
            state_totals[state] = {
                "paid": 0,
                "free": 0,
            }

        if level in state_totals[state]:
            state_totals[state][level] = streams

    results = []

    for state, levels in state_totals.items():

        paid = levels["paid"]
        free = levels["free"]

        difference = paid - free

        if paid > free:
            higher_level = "paid"
        elif free > paid:
            higher_level = "free"
        else:
            higher_level = "equal"

        results.append(
            {
                "state": state,
                "paid_streams": paid,
                "free_streams": free,
                "difference": difference,
                "higher_streaming_level": higher_level,
            }
        )

    results.sort(
        key=lambda row: abs(row["difference"]),
        reverse=True,
    )

    return results
def analyze_hourly_stream_spikes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        WITH hourly AS (
            SELECT
                DATE_TRUNC('hour', ts) AS hour,
                COUNT(*) AS streams
            FROM fact_streams
            GROUP BY 1
        ),
        statistics AS (
            SELECT
                AVG(streams) AS avg_streams,
                STDDEV_POP(streams) AS stddev_streams
            FROM hourly
        )
        SELECT
            h.hour,
            h.streams,
            s.avg_streams,
            s.stddev_streams,
            CASE
                WHEN s.stddev_streams = 0 THEN 0
                ELSE (h.streams - s.avg_streams) / s.stddev_streams
            END AS z_score
        FROM hourly h
        CROSS JOIN statistics s
        ORDER BY h.hour;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    results = []

    for row in rows:
        hour, streams, avg_streams, stddev_streams, z_score = row

        results.append({
            "hour": hour,
            "streams": streams,
            "average_streams": round(float(avg_streams), 2),
            "stddev_streams": round(float(stddev_streams), 2),
            "z_score": round(float(z_score), 2),
            "is_spike": round(float(z_score), 2) >= 2,
        })

    return results
