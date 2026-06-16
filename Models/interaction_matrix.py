import numpy as np

class InteractionMatrix:
    def __init__(self):
        # 6 features → 6x6 matrix
        self.matrix = np.eye(6, dtype=complex)

        # ===============================
        # Feature interactions (IMPORTANT)
        # ===============================

        # keystroke ↔ pattern
        self.matrix[0][4] = 0.15
        self.matrix[4][0] = 0.15

        # device ↔ location
        self.matrix[1][2] = 0.20
        self.matrix[2][1] = 0.20

        # location ↔ travel
        self.matrix[2][5] = 0.25
        self.matrix[5][2] = 0.25

        # time ↔ pattern
        self.matrix[3][4] = 0.10
        self.matrix[4][3] = 0.10

    def apply(self, psi):

        base_matrix = np.eye(6, dtype=complex)

        # Static interactions
        base_matrix[0][4] = base_matrix[4][0] = 0.15
        base_matrix[1][2] = base_matrix[2][1] = 0.20
        base_matrix[2][5] = base_matrix[5][2] = 0.25
        base_matrix[3][4] = base_matrix[4][3] = 0.10

        # ===============================
        # 🔥 Dynamic interactions
        # ===============================

        # Location risk → amplify travel
        if abs(psi[2]) > 0.5:
            base_matrix[2][5] = min(base_matrix[2][5] + 0.1, 0.5)
            base_matrix[5][2] = min(base_matrix[5][2] + 0.1, 0.5)

        # Keystroke anomaly → amplify pattern
        if abs(psi[0]) > 0.5:
            base_matrix[0][4] = min(base_matrix[0][4] + 0.1, 0.5)
            base_matrix[4][0] = min(base_matrix[4][0] + 0.1, 0.5)

        # Device + Location combo (VERY IMPORTANT)
        if abs(psi[1]) > 0.5 and abs(psi[2]) > 0.5:
            base_matrix[1][2] = min(base_matrix[1][2] + 0.15, 0.6)
            base_matrix[2][1] = min(base_matrix[2][1] + 0.15, 0.6)

        return np.dot(base_matrix, psi)
