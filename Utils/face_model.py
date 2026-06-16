import os
from deepface import DeepFace

model = DeepFace.build_model("Facenet")
# Force CPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

model_loaded = False

def load_face_model():
    global model_loaded

    if not model_loaded:
        print("🔵 Loading FaceNet model...")
        DeepFace.build_model("Facenet")
        print("🟢 FaceNet model loaded successfully.")
        model_loaded = True
