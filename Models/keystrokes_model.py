import math
import numpy as np
import MySQLdb.cursors
from database.db import mysql


# mahalanobic function
def mahalanobis_distance(sample, mean, std):

    sample = np.array(sample)
    mean = np.array(mean)
    std = np.array(std)

    variance = std ** 2
    variance[variance == 0] = 0.0001

    diff = sample - mean

    distance = np.sqrt(np.sum((diff ** 2) / variance))

    return distance


# Save one typing attempt
def save_typing_sample(user_id, typing_time, flight_time):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO typing_samples (user_id, typing_time, flight_time)
        VALUES (%s, %s, %s)
    """, (user_id, typing_time, flight_time))

    mysql.connection.commit()
    cursor.close()


# Get last 3 samples for baseline creation
def get_last_ten_samples(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT typing_time, flight_time
        FROM typing_samples
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))
    
    rows = cur.fetchall()
    cur.close()

    return [{"typing_time": r[0], "flight_time": r[1]} for r in rows]

# Compare Typing Pattern Using Cosine Similarity
def cosine_similarity(vec1, vec2):

    v1 = np.array(vec1)
    v2 = np.array(vec2)

    dot = np.dot(v1, v2)

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot / (norm1 * norm2)


# Calculate deviation during login
def calculate_typing_deviation(current_typing_time, current_flight_time,
                               mean_typing, std_typing,
                               mean_flight, std_flight):

    # Prevent divide by zero
    std_typing = std_typing if std_typing > 0 else 0.001
    std_flight = std_flight if std_flight > 0 else 0.001

    typing_z = abs(current_typing_time - mean_typing) / std_typing
    flight_z = abs(current_flight_time - mean_flight) / std_flight

    # Combine features
    combined_z = (typing_z + flight_z) / 2

    return combined_z
