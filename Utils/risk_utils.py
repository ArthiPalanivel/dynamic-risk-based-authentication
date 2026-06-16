import numpy as np


# ==========================================
# NORMALIZATION HELPERS
# ==========================================

def normalize_score(raw_score, max_value=100.0):
    """
    Converts raw anomaly score into 0–1 range.
    Prevents overflow and keeps system stable.
    """
    if raw_score is None:
        return 0.0

    return float(np.clip(raw_score / max_value, 0.0, 1.0))


# ==========================================
# STABILITY FACTORS
# ==========================================

def get_stability_factor(feature_name, anomaly_score):
    """
    Determines phase stability for quantum encoding.
    Higher stability → stronger phase effect.
    """

    base_stability = {
        "keystroke": 0.4,
        "device": 0.3,
        "location": 0.2,
        "time": 0.2,
        "face": 0.5
    }

    stability = base_stability.get(feature_name, 0.2)

    # If anomaly is high, increase stability slightly
    if anomaly_score > 0.7:
        stability += 0.1

    return min(stability, 1.0)


# ==========================================
# BUILD FEATURE DICTIONARY
# ==========================================

def build_feature_vector(
    keystroke_risk,
    device_anomaly,
    location_anomaly,
    time_risk,
    face_risk
):
    """
    Prepares feature dictionary for QuantumRiskEngine.
    All inputs should be raw scores (0–100 or boolean).
    """

    keystroke_norm = normalize_score(keystroke_risk)
    time_norm = normalize_score(time_risk)
    face_norm = normalize_score(face_risk)

    device_norm = 1.0 if device_anomaly else 0.0
    location_norm = 1.0 if location_anomaly else 0.0

    features = {
        "keystroke": (
            keystroke_norm,
            get_stability_factor("keystroke", keystroke_norm)
        ),
        "device": (
            device_norm,
            get_stability_factor("device", device_norm)
        ),
        "location": (
            location_norm,
            get_stability_factor("location", location_norm)
        ),
        "time": (
            time_norm,
            get_stability_factor("time", time_norm)
        ),
        "face": (
            face_norm,
            get_stability_factor("face", face_norm)
        )
    }

    return features
