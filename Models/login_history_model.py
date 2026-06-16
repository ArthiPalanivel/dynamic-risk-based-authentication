from datetime import datetime
import statistics

class LoginHistoryModel:
    def __init__(self):
        self.history = []

    def add_login(self, timestamp, ip, device, success, risk_score):
        self.history.append({
            "time": timestamp,
            "ip": ip,
            "device": device,
            "success": success,
            "risk": risk_score
        })

    def get_login_times(self):
        return [entry["time"].hour for entry in self.history]

    def typical_login_hour(self):
        hours = self.get_login_times()
        if not hours:
            return None
        return int(statistics.mean(hours))

    def is_unusual_time(self, current_time):
        typical = self.typical_login_hour()
        if typical is None:
            return False
        
        return abs(current_time.hour - typical) > 5

    def new_device_detected(self, device):
        devices = [entry["device"] for entry in self.history]
        return device not in devices

    def failed_attempts(self, window=5):
        return sum(1 for entry in self.history[-window:] if not entry["success"])

    def risk_trend(self):
        if not self.history:
            return 0
        risks = [entry["risk"] for entry in self.history]
        return sum(risks) / len(risks)
