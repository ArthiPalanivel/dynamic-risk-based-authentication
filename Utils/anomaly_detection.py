import json
import numpy as np
from flask import current_app
from database.db import mysql


# ==========================================
# TIME ANOMALY
# ==========================================

def is_time_anomaly(user_id):
    """
    Checks if login time is outside user's normal pattern.
    Returns: (flag, risk_score 0-100)
    """

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT login_time FROM login_history WHERE user_id=%s",
        (user_id,)
    )
    rows = cur.fetchall()
    hours = [row[0].hour for row in rows if row[0] is not None]
    cur.close()

    if not hours:
        return False, 0

    mean_hour = np.mean(hours)
    std_hour = np.std(hours)

    from datetime import datetime
    current_hour = datetime.now().hour

    deviation = abs(current_hour - mean_hour)

    if std_hour == 0:
        risk = 100 if deviation > 2 else 0
    else:
        z_score = deviation / std_hour
        risk = min(z_score * 20, 100)

    return bool(risk > 30), float(risk)


# ==========================================
# KEYSTROKE ANOMALY
# ==========================================

def is_keystroke_anomaly(user_id, typing_time, flight_time):
    """
    Checks typing rhythm deviation.
    Returns: (flag, risk_score 0-100)
    """

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT typing_time, flight_time
        FROM typing_samples
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        return False, 0

    typing_avg = np.mean([r[0] for r in rows])
    flight_avg = np.mean([r[1] for r in rows])

    typing_dev = abs(typing_time - typing_avg)
    flight_dev = abs(flight_time - flight_avg)

    risk = min((typing_dev + flight_dev) * 5, 100)

    return bool(risk > 30), float(risk)


# ==========================================
# KEYSTROKE PATTERN ANOMALY
# ==========================================

def is_pattern_anomaly(user_id, pattern_vector):

    if not pattern_vector:
        return False, 0

    try:
        input_vector = np.array(pattern_vector, dtype=float)
    except:
        return True, 80

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT pattern_vector FROM keystroke_patterns WHERE user_id=%s",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        return False, 0

    distances = []

    for r in rows:

        try:
            vec = np.array(json.loads(r[0]), dtype=float)

            min_len = min(len(vec), len(input_vector))

            if min_len < 2:
                continue

            vec_trim = vec[:min_len]
            input_trim = input_vector[:min_len]

            dist = np.linalg.norm(vec_trim - input_trim)

            distances.append(dist)

        except:
            continue

    if not distances:
        return False, 0

    avg_distance = np.mean(distances)

    risk = min(avg_distance * 1.2, 100)

    return bool(risk > 35), float(risk)
