import json
import math
import statistics
from database.db import mysql
from config import get_db_connection


def calculate_baseline(samples):
    typing_times = [s['typing_time'] for s in samples]
    flight_times = [s['flight_time'] for s in samples]

    mean_typing = sum(typing_times) / len(typing_times)
    mean_flight = sum(flight_times) / len(flight_times)

    variance = sum((x - mean_typing) ** 2 for x in typing_times) / len(typing_times)
    std_typing = math.sqrt(variance)

    return mean_typing, std_typing, mean_flight



def save_user_baseline(user_id, samples, device_hash, login_hour, face_embedding):

    typing_times = [s["typing_time"] for s in samples]
    flight_times = [s["flight_time"] for s in samples]

    avg_typing = sum(typing_times) / len(typing_times)
    avg_flight = sum(flight_times) / len(flight_times)

    std_typing = statistics.stdev(typing_times) if len(typing_times) > 1 else 0
    std_flight = statistics.stdev(flight_times) if len(flight_times) > 1 else 0
    
    cur = mysql.connection.cursor()

    cur.execute("""
    INSERT INTO user_baseline
    (user_id, avg_typing_time, avg_flight_time,
    std_typing_time, std_flight_time,
    device_hash, login_hour, face_embedding)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        avg_typing,
        avg_flight,
        std_typing,
        std_flight,
        device_hash,
        login_hour,
        json.dumps(face_embedding)
    ))

    mysql.connection.commit()
    cur.close()


def update_user_baseline(user_id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT typing_time, flight_time
        FROM typing_samples
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 20
    """, (user_id,))

    samples = cur.fetchall()

    if len(samples) < 5:
        cur.close()
        return

    typing_times = [s[0] for s in samples]
    flight_times = [s[1] for s in samples]

    avg_typing = sum(typing_times) / len(typing_times)
    avg_flight = sum(flight_times) / len(flight_times)

    std_typing = statistics.stdev(typing_times)
    std_flight = statistics.stdev(flight_times)

    cur.execute("""
        UPDATE user_baseline
        SET avg_typing_time=%s,
            avg_flight_time=%s,
            std_typing_time=%s,
            std_flight_time=%s
        WHERE user_id=%s
    """, (
        avg_typing,
        avg_flight,
        std_typing,
        std_flight,
        user_id
    ))

    mysql.connection.commit()
    cur.close()
