import numpy as np
import base64
import json
import cv2
from deepface import DeepFace
from database.db import mysql


def verify_face(user_id, base64_image):
    """
    Verify face using stored embeddings (DB)
    """

    if not base64_image:
        return {"status": False, "reason": "No image provided"}

    try:
        # Decode base64 image
        header, encoded = base64_image.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Generate embedding
        embedding = DeepFace.represent(
            img_path=img,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=False
        )[0]["embedding"]

    except Exception as e:
        print("Face processing error:", e)
        return {"status": False, "reason": "Processing failed"}

    # Fetch stored embedding
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT face_embedding FROM user_baseline WHERE user_id=%s",
        (user_id,)
    )
    result = cur.fetchone()
    cur.close()

    if not result or not result[0]:
        return {"status": False, "reason": "No stored face"}

    stored_embedding = np.array(json.loads(result[0]))

    # Cosine similarity
    dot = np.dot(stored_embedding, embedding)
    norm_a = np.linalg.norm(stored_embedding)
    norm_b = np.linalg.norm(embedding)

    if norm_a == 0 or norm_b == 0:
        return {"status": False, "reason": "Invalid embedding"}

    similarity = dot / (norm_a * norm_b)

    print(f"Face similarity: {similarity:.3f}")

    return {
    "status": similarity >= 0.80,
    "confidence": float(similarity),
    "risk": 1 - similarity
}
