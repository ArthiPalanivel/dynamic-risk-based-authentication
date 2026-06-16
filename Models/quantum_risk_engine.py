import numpy as np
from models.interaction_matrix import InteractionMatrix

class QuantumRiskEngine:

    def __init__(self):
        self.interactions = InteractionMatrix()

    def encode_feature(self, score, stability_factor):
        """
        Convert anomaly score into complex amplitude.
        """
        magnitude = np.sqrt(score)
        phase = np.pi * stability_factor
        return magnitude * np.exp(1j * phase)

    def build_state(self, features):
        
        amplitudes = []

        order = ["keystroke","device","location","time","pattern","travel"]

        for key in order:
            score, stability = features[key]
            amp = self.encode_feature(score, stability)
            amplitudes.append(amp)

        psi = np.array(amplitudes, dtype=complex)

        norm = np.linalg.norm(psi)
        if norm > 0:
            psi = psi / norm

        return psi
    
    def amplify(self, x):
        return 1 / (1 + np.exp(-6 * (x - 0.5)))

    def measure_risk(self, psi):

        interacted = self.interactions.apply(psi)

        probabilities = np.abs(interacted) ** 2

        weights = np.array([0.35, 0.18, 0.15, 0.10, 0.12, 0.10])

        weighted_risk = np.sum(probabilities * weights)

        return float(np.clip(self.amplify(weighted_risk.real), 0, 1))
    
    def evaluate(self, features):

        psi = self.build_state(features)
        risk_probability = self.measure_risk(psi)

        # ===============================
        # HARD KEYSTROKE SECURITY RULE
        # ===============================

        keystroke_score = features["keystroke"][0]

        if keystroke_score > 0.8:
            return {
                "probability": risk_probability,
                "decision": "FACE_LOCK"
            }

        if keystroke_score > 0.6:
            return {
                "probability": risk_probability,
                "decision": "OTP"
            }

        # ===============================
        # Normal risk decision
        # ===============================

        if risk_probability < 0.25:
            decision = "ALLOW"

        elif risk_probability < 0.5:
            decision = "OTP"

        elif risk_probability < 0.75:
            decision = "PUSH"

        else:
            decision = "FACE_LOCK"

        return {
            "probability": risk_probability,
            "decision": decision
        }
