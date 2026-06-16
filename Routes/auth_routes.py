import random
import numpy as np
import json
import bcrypt
import time
import base64

from flask import flash, Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime

from utils.email_service import send_otp_email
from database.db import mysql
from utils.device_fingerprint import generate_device_hash
 
from utils.ip_location import get_location
from utils.impossible_travel import impossible_travel


from models.quantum_risk_engine import QuantumRiskEngine
from models.keystrokes_model import save_typing_sample, get_last_ten_samples, cosine_similarity
from models.baseline_model import save_user_baseline, update_user_baseline


# Make sure these exist in your project
from utils.anomaly_detection import (
    is_time_anomaly,
    is_keystroke_anomaly,
    is_pattern_anomaly
)

from routes.dashboard_routes import dashboard_bp

from deepface import DeepFace



auth_bp = Blueprint("auth", __name__)


def normalize(value, mean, std):
    std = max(std, 0.05)   # prevent explosion
    return (value - mean) / std

# =====================================================
# FACE VERIFICATION HELPER
# =====================================================
def verify_face_embedding(user_id, base64_image):
    # Lazy imports (loads only when face verification runs)
    
    import cv2
    import numpy as np
    
    if not base64_image:
        return False

    try:
        header, encoded = base64_image.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        embedding = DeepFace.represent(
            img_path=img,
            model_name = "Facenet512",
            detector_backend="opencv",
            enforce_detection=True
        )[0]["embedding"]

    except Exception as e:
        print("Face processing error:", e)
        return False
    
    if embedding is None or len(embedding) == 0:
        return False

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT face_embedding FROM user_baseline WHERE user_id=%s",
        (user_id,)
    )
    result = cur.fetchone()
    cur.close()

    if not result or not result[0]:
        return False

    stored_vector = np.array(json.loads(result[0]))

    dot_product = np.dot(stored_vector, embedding)
    norm_a = np.linalg.norm(stored_vector)
    norm_b = np.linalg.norm(embedding)

    if norm_a == 0 or norm_b == 0:
        return False

    similarity = dot_product / (norm_a * norm_b)

    print(f"Face similarity: {similarity:.3f}")
    
    return similarity >= 0.7


# =====================================================
# HOME
# =====================================================
@auth_bp.route("/")
def home():
    return  render_template("home.html")


# =====================================================
# REGISTER
# =====================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    from deepface import DeepFace
    import cv2  

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password1 = request.form["password1"]
        password2 = request.form["password2"]
        password3 = request.form["password3"]

        if not (password1 == password2 == password3):
            flash("Passwords do not match!", "danger")
            return render_template("register.html")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username already exists!", "danger")
            return render_template("register.html")
        
        hashed_password = bcrypt.hashpw(
            password1.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
            (username, email, hashed_password)
        )
        mysql.connection.commit()
        user_id = cur.lastrowid

        # Keystroke samples
        save_typing_sample(user_id, float(request.form.get("typing1", 0)), float(request.form.get("flight1", 0)))
        save_typing_sample(user_id, float(request.form.get("typing2", 0)), float(request.form.get("flight2", 0)))
        save_typing_sample(user_id, float(request.form.get("typing3", 0)), float(request.form.get("flight3", 0)))

        samples = get_last_ten_samples(user_id)

        if not samples:
            raise ValueError("No typing samples found")
            
        # Face enrollment
        face_images = request.form.getlist("face_images")

        if len(face_images) < 3:
            flash("Please capture 3 face samples.", "danger")
            return render_template("register.html")
        
        embeddings_list = []

        for face_image in face_images:
            header, encoded = face_image.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            embedding = DeepFace.represent(
                img_path=img,
                model_name="Facenet512",
                detector_backend="opencv",
                enforce_detection=True
            )[0]["embedding"]

            embeddings_list.append(embedding)

        avg_embedding = np.mean(embeddings_list, axis=0).tolist()

        device_hash = generate_device_hash(request)
        login_hour = datetime.now().hour

        save_user_baseline(
            user_id,
            samples,
            device_hash,
            login_hour,
            avg_embedding
        )

        cur.close()

        flash("Registration completed successfully!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/test")
def test():
    return "Auth routes working"

# =====================================================
# LOGIN
# =====================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        if "username" not in request.form:
            return render_template("login.html")
        
        username = request.form["username"]

        current_time = time.time()

        lock_key = f"lock_until_{username}"

        if lock_key in session and current_time < session[lock_key]:
            remaining = int(session[lock_key] - current_time)
            flash(f"Account locked. Try again in {remaining} seconds.", "danger")
            return render_template("login.html")

        password = request.form["password"]

        dwell_time = float(request.form.get("dwell_time", 0.15))
        flight_time = float(request.form.get("flight_time", 0.12))

        print("Dwell:", dwell_time)
        print("Flight:", flight_time)

        keystroke_pattern = request.form.get("keystroke_pattern")

        if keystroke_pattern:
            try:
                keystroke_pattern = json.loads(keystroke_pattern)
            except:
                keystroke_pattern = None

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
 
        if user and bcrypt.checkpw(password.encode("utf-8"), user[3].encode("utf-8")):
            
            user_id = user[0]

            ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
            device_info = request.headers.get("User-Agent")


            # ===============================
            # FETCH BASELINE FIRST
            # ===============================
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT avg_typing_time, avg_flight_time,
                std_typing_time, std_flight_time,trust_score
            FROM user_baseline
            WHERE user_id=%s
            """, (user_id,))
            baseline = cur.fetchone()
            cur.close()

            if not baseline:
                avg_typing, avg_flight, std_typing, std_flight = dwell_time, flight_time, 0.1, 0.1
            else:
                avg_typing, avg_flight, std_typing, std_flight, _ = baseline

            # ===============================
            # BUILD FEATURE VECTOR
            # ===============================
            norm_dwell = normalize(dwell_time, avg_typing, std_typing)
            norm_flight = normalize(flight_time, avg_flight, std_flight)
            
            ratio = min(dwell_time / (flight_time + 0.0001), 5)

            feature_vector = [
                norm_dwell,
                norm_flight,
                ratio,
                dwell_time * flight_time   # interaction feature
            ]

            # ===============================
            # COMPARE WITH SAMPLES
            # ===============================
            samples = get_last_ten_samples(user_id)

            if len(samples) < 5:
                print("Learning phase — skipping security checks")

                session["user_id"] = user_id
                session["username"] = user[1]

                # Reset failed attempts after successful login
                session.pop(f"attempts_{user[1]}", None)
                session.pop(f"lock_until_{user[1]}", None)

                cur = mysql.connection.cursor()

                cur.execute("""
                INSERT INTO login_history
                (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    dwell_time,
                    flight_time,
                    ip_address,
                    device_info,
                    json.dumps(keystroke_pattern) if keystroke_pattern else None
                ))

                mysql.connection.commit()
                cur.close()

                save_typing_sample(user_id, dwell_time, flight_time)

                return redirect(url_for("dashboard.dashboard"))

            else:
                similarities = []

                for sample in samples:

                    sample_dwell = normalize(sample["typing_time"], avg_typing, std_typing)
                    sample_flight = normalize(sample["flight_time"], avg_flight, std_flight)

                    sample_ratio = sample["typing_time"] / (sample["flight_time"] + 0.0001)

                    sample_vector = [
                        sample_dwell,
                        sample_flight,
                        sample_ratio,
                        sample["typing_time"] * sample["flight_time"]
                    ]

                    sim = cosine_similarity(feature_vector, sample_vector)
                    similarities.append(sim)

                if similarities:
                    similarity = sum(similarities) / len(similarities)   # average
                    consistency = np.std(similarities)                  # variation
                else:
                    similarity = 0
                    consistency = 1


            confidence = similarity

            high_risk_flag = False

            print("Typing similarity:", similarity)
            print("Consistency:", consistency)

            if similarity > 0.75 and consistency < 0.15:
                print("Trusted user - skipping MFA")
 
                if baseline and baseline[4] is not None:
                    trust_score = min(100, baseline[4] + 5)
                else:
                    trust_score = 55   

                session["user_id"] = user_id
                session["username"] = user[1]
 
                session.pop(f"attempts_{user[1]}", None)
                session.pop(f"lock_until_{user[1]}", None)
 
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO login_history
                    (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
                    VALUES (%s, NOW(), %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    dwell_time,
                    flight_time,
                    ip_address,
                    device_info,
                    json.dumps(keystroke_pattern) if keystroke_pattern else None
                ))
                cur.execute("""
                    UPDATE user_baseline
                    SET trust_score=%s
                    WHERE user_id=%s
                """, (trust_score, user_id))
                mysql.connection.commit()
                cur.close()
 
                save_typing_sample(user_id, dwell_time, flight_time)
                update_user_baseline(user_id)

                return redirect(url_for("dashboard.dashboard"))
            # ===============================
            # STATUS
            # ===============================
            # Initialize trust score
            if baseline and baseline[4] is not None:
                trust_score = baseline[4]
            else:
                trust_score = 50

            # Typing contribution
            if confidence > 0.75:
                trust_score += 30
            elif confidence > 0.45:
                trust_score += 10
            else:
                trust_score -= 30

            print("Keystroke Confidence:", confidence)


            # STRONG DECISION
            if similarity < 0.35:
                print("Strong typing mismatch")
                high_risk_flag = True

            elif similarity < 0.55:
                print("Moderate typing deviation")

            elif consistency > 0.20:
                print("Inconsistent typing behavior")
                        
            # ===============================
            # 🔥 HEAVY OPERATIONS START HERE
            # ===============================
            if "location_cache" not in session:
                session["location_cache"] = get_location(ip_address)

            current_location = session["location_cache"]
            # ===============================
            # PREVIOUS LOGIN FOR TRAVEL CHECK
            # ===============================

            cur = mysql.connection.cursor()

            cur.execute("""
            SELECT ip_address, login_time
            FROM login_history
            WHERE user_id=%s
            ORDER BY login_time DESC
            LIMIT 1
            """, (user_id,))

            last_login = cur.fetchone()

            travel_anomaly = 0.0

            if last_login:

                prev_ip = last_login[0]
                prev_time = last_login[1]

                prev_location = get_location(prev_ip)

                time_diff = (datetime.now() - prev_time).total_seconds() / 3600

                if impossible_travel(prev_location, current_location, time_diff):
                    travel_anomaly = 1.0

            cur.execute("SELECT COUNT(*) FROM login_history WHERE user_id=%s", (user_id,))
            login_count = cur.fetchone()[0]

            if login_count < 2:
                ip_anomaly = 0.0
                device_anomaly = 0.0
            
            else:
        
                cur.execute("""
                SELECT ip_address 
                FROM login_history 
                WHERE user_id=%s
                ORDER BY login_time DESC
                LIMIT 10
                """, (user_id,))
                previous_ips = [row[0] for row in cur.fetchall()]
                
                ip_anomaly = 1.0 if ip_address not in previous_ips else 0.0

                cur.execute("""
                SELECT device_info
                FROM login_history
                WHERE user_id=%s
                ORDER BY login_time DESC
                LIMIT 10
                """, (user_id,))
                previous_devices = [row[0] for row in cur.fetchall()]
            
                device_anomaly = 1.0 if device_info not in previous_devices else 0.0

            cur.close()

            time_flag, time_risk = is_time_anomaly(user_id)
            key_flag, key_risk = is_keystroke_anomaly(user_id, dwell_time, flight_time)

            # Fix tuple issue
            if isinstance(time_risk, tuple):
                time_risk = time_risk[0]

            if isinstance(key_risk, tuple):
                key_risk = key_risk[0]

            time_risk = float(time_risk)
            key_risk = float(key_risk)

            # =========================================
            # HARD KEYSTROKE SECURITY CHECK
            # =========================================

            cur = mysql.connection.cursor()

            cur.execute("""
            SELECT avg_typing_time, std_typing_time, 
                avg_flight_time, std_flight_time,trust_score
            FROM user_baseline
            WHERE user_id=%s
            """, (user_id,))

            baseline = cur.fetchone()
            cur.close()

            if baseline:

                avg_typing, std_typing, avg_flight, std_flight, _ = baseline

            if trust_score is None:
                trust_score = 50

            # Z-score calculations
            typing_z = abs(dwell_time - avg_typing) / (std_typing + 0.0001)
            flight_z = abs(flight_time - avg_flight) / (std_flight + 0.0001)

            keystroke_z = (typing_z + flight_z) / 2

            print("Typing Z-score:", typing_z)
            print("Flight Z-score:", flight_z)
            print("Combined Z:", keystroke_z)

            # SECURITY DECISION
            if keystroke_z > 8:
                print("Extreme typing deviation detected!")
                high_risk_flag = True   

            pattern_anomaly = 0.0
            if keystroke_pattern:
                pattern_vector = [
                    keystroke_pattern.get("avg_dwell",0),
                    keystroke_pattern.get("avg_flight",0),
                    keystroke_pattern.get("dwell_var",0),
                    keystroke_pattern.get("flight_var",0)
                ]

                pattern_flag, pattern_risk = is_pattern_anomaly(user_id, pattern_vector)
                
                if isinstance(pattern_risk, tuple):
                    pattern_risk = pattern_risk[0]

                pattern_risk = float(pattern_risk)
                
                pattern_anomaly = min(pattern_risk / 100.0, 1.0)
 
            features = {
                "keystroke": (1 - confidence, 0.30),
                "device": (device_anomaly, 0.15),
                "location": (ip_anomaly, 0.15),
                "time": (min(time_risk / 100.0, 1.0), 0.10),
                "pattern": (pattern_anomaly, 0.30),
                "travel": (travel_anomaly, 0.15)
            }
                
            use_risk_engine = similarity < 0.7 or high_risk_flag

            if use_risk_engine:
                risk_engine = QuantumRiskEngine()
                result = risk_engine.evaluate(features)
            else:
                result = {
                    "decision": "ALLOW",
                    "probability": 0.1
                }

            decision = result["decision"]
            risk_probability = result["probability"]

            print("=== RISK BREAKDOWN ===")
            for k, v in features.items():
                print(f"{k}: score={v[0]:.2f}, stability={v[1]}")

            last_risk = session.get("last_risk", 0)

            if abs(risk_probability - last_risk) > 0.5:
                print("Sudden risk spike detected!")
                high_risk_flag = True

            session["last_risk"] = risk_probability
            
            trust_score = (0.7 * trust_score) + (0.3 * (1 - risk_probability) * 100)

            trust_score = max(0, min(100, trust_score))
            print("Quantum Risk Probability:", result["probability"])
            print("Decision:", decision)

            ai_decision = result["decision"]

            def final_decision(ai_decision, trust_score, high_risk_flag):
                if high_risk_flag:
                    return "FACE"

                if ai_decision == "ALLOW":
                    return "ALLOW" if trust_score > 60 else "PUSH"

                if ai_decision == "OTP":
                    return "PUSH"

                if ai_decision in ["FACE", "FACE_LOCK"]:
                    return "FACE"

                return "BLOCK"

            decision = final_decision(ai_decision, trust_score, high_risk_flag)

            if decision == "BLOCK":
                session.clear()
                flash("High risk login blocked", "danger")
                return redirect(url_for("auth.login"))

            # ===============================
            # FINAL DECISION ENGINE
            # ===============================

            if high_risk_flag and decision != "BLOCK":
                decision = "FACE"

            if decision != "ALLOW":

                session["temp_user_id"] = user_id
                session["temp_username"] = user[1]

                # 🔥 STORE DATA FOR POST-MFA LOGGING
                session["dwell_time"] = dwell_time
                session["flight_time"] = flight_time
                session["ip_address"] = ip_address
                session["device_info"] = device_info
                session["keystroke_pattern"] = keystroke_pattern

                if decision == "PUSH":

                    # OTP + PUSH
                    otp = str(random.randint(100000, 999999))
                    session["otp"] = otp
                    session["otp_time"] = time.time()
                    send_otp_email(user[2], otp)

                    session["next_step"] = "push"
                    return redirect(url_for("auth.verify_otp"))
                
                elif decision == "FACE":
                    
                    # OTP + FACE
                    otp = str(random.randint(100000, 999999))
                    session["otp"] = otp
                    session["otp_time"] = time.time()
                    send_otp_email(user[2], otp)

                    session["require_face"] = True
                    session["next_step"] = "face"
                    return redirect(url_for("auth.verify_otp"))

                else:
                     # OTP only
                    otp = str(random.randint(100000, 999999))
                    session["otp"] = otp
                    session["otp_time"] = time.time()
                    send_otp_email(user[2], otp)

                    return redirect(url_for("auth.verify_otp"))
            # SAFE LOGIN
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO login_history
                (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, (
                user_id,
                dwell_time,
                flight_time,
                ip_address,
                device_info,
                json.dumps(keystroke_pattern) if keystroke_pattern else None
            ))

            save_typing_sample(user_id, dwell_time, flight_time)

            # ===============================
            # STORE LEARNING DATA
            # ===============================

            cur.execute("""
            SELECT COUNT(*) FROM keystroke_patterns
            WHERE user_id=%s
            """, (user_id,))

            count = cur.fetchone()[0]

            if count < 5 and keystroke_pattern:

                pattern_vector = [
                    keystroke_pattern.get("avg_dwell",0),
                    keystroke_pattern.get("avg_flight",0),
                    keystroke_pattern.get("dwell_var",0),
                    keystroke_pattern.get("flight_var",0)
                ]

                cur.execute("""
                    INSERT INTO keystroke_patterns (user_id, pattern_vector)
                    VALUES (%s, %s)
                """, (user_id, json.dumps(pattern_vector)))

            # update trust score EVERY login    
            cur.execute("""
                UPDATE user_baseline
                SET trust_score=%s
                WHERE user_id=%s
                """, (trust_score, user_id))

            mysql.connection.commit()
            cur.close()

            # Update typing baseline (adaptive learning)
            update_user_baseline(user_id)
            
            session["user_id"] = user_id
            session["username"] = user[1]

            return redirect(url_for("dashboard.dashboard"))

        # WRONG PASSWORD

        key = f"attempts_{username}"

        # Initialize if not exists
        if key not in session:
            session[key] = 0

        session[key] += 1
    
        # Lock after 3 attempts
        if session[key] >= 3:
            session[f"lock_until_{username}"] = time.time() + 120  # 2 minutes
            session[key] = 0  # reset attempts after lock
            flash("Too many failed attempts. Account locked for 2 minutes.", "danger")
            return render_template("login.html")

        flash("Invalid username or password.", "danger")
        return render_template("login.html")
    
    return render_template("login.html")

             
#======================================================
# FORGOT PASSWORD
#======================================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("Email not found", "danger")
            return render_template("forgot_password.html")

        otp = str(random.randint(100000, 999999))

        session["reset_user_id"] = user[0]
        session["reset_username"] = user[1]
        session["reset_email"] = email

        session["reset_otp"] = otp
        session["reset_time"] = time.time()

        send_otp_email(email, otp)

        return redirect(url_for("auth.verify_reset_otp"))

    return render_template("forgot_password.html")


# =====================================================
# VERIFY OTP
# =====================================================
@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        # OTP expiry check (2 minutes)
        if time.time() - session.get("otp_time", 0) > 120:
            session.clear()
            return "OTP expired. Please login again."
        if request.form["otp"] == session.get("otp"):
            session["otp_verified"] = True
            session.pop("otp", None)
            session.pop("otp_time", None)

            next_step = session.get("next_step")

            if next_step == "push":
                return redirect(url_for("auth.push_approval"))

            elif next_step == "face":
                return redirect(url_for("auth.face_verification"))
           
            # Only OTP case
            user_id = session.get("temp_user_id")

            if not user_id:
                return redirect(url_for("auth.login"))

            # ✅ FETCH USERNAME FROM DB (FIX)
            cur = mysql.connection.cursor()
            cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()

            cur.execute("""
            INSERT INTO login_history
            (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, (
                user_id,
                session.get("dwell_time"),
                session.get("flight_time"),
                session.get("ip_address"),
                session.get("device_info"),
                json.dumps(session.get("keystroke_pattern")) if session.get("keystroke_pattern") else None
            ))
            mysql.connection.commit()
            cur.close()


            username = user[0] if user else "User"

            session.clear()
            session["user_id"] = user_id
            session["username"] = username

            return redirect(url_for("dashboard.dashboard"))
        else:
            return "Invalid OTP ❌"

    return render_template("otp.html")


# =====================================================
# VERIFY RESET OTP
# =====================================================
@auth_bp.route("/verify-reset-otp", methods=["GET","POST"])
def verify_reset_otp():

    if request.method == "POST":

        otp = request.form["otp"]

        if time.time() - session.get("reset_time",0) > 120:
            session.clear()
            flash("OTP expired", "danger")
            return redirect(url_for("auth.login"))

        if otp == session.get("reset_otp"):

            session["otp_verified_reset"] = True

            return redirect(url_for("auth.reset_face_verification"))

        flash("Invalid OTP", "danger")

    return render_template("reset_otp.html")

# =====================================================
# PUSH OTP
# =====================================================
@auth_bp.route("/push-approval", methods=["GET","POST"])
def push_approval():

    if "temp_user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        decision = request.form.get("decision")

        if decision == "approve":

            user_id = session.get("temp_user_id")

            cur = mysql.connection.cursor()

            # ✅ FETCH USERNAME FROM DB
            cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()
 
            cur.execute("""
            INSERT INTO login_history
            (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, (
                user_id,
                session.get("dwell_time"),
                session.get("flight_time"),
                session.get("ip_address"),
                session.get("device_info"),
                json.dumps(session.get("keystroke_pattern")) if session.get("keystroke_pattern") else None
            ))
            mysql.connection.commit()
            cur.close()

            username = user[0] if user else "User"

            session.clear()
            session["user_id"] = user_id
            session["username"] = username

            return redirect(url_for("dashboard.dashboard"))

        else:
            session.clear()
            flash("Login denied.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("push_approval.html")

# =====================================================
# FACE VERIFICATION
# =====================================================
@auth_bp.route("/face-verification", methods=["GET", "POST"])
def face_verification():

    if not (session.get("otp_verified") and session.get("require_face")):
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":

        incoming_embedding = request.form.get("face_embedding")

        if verify_face_embedding(session.get("temp_user_id"), incoming_embedding):

            user_id = session.get("temp_user_id")
             
            # Store login history
            cur = mysql.connection.cursor()

            # ✅ FETCH USERNAME FROM DB
            cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()

            cur.execute("""
            INSERT INTO login_history
            (user_id, login_time, dwell_time, flight_time, ip_address, device_info, keystroke_pattern)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, (
                user_id,
                session.get("dwell_time"),
                session.get("flight_time"),
                session.get("ip_address"),
                session.get("device_info"),
                json.dumps(session.get("keystroke_pattern")) if session.get("keystroke_pattern") else None
            ))
            mysql.connection.commit()
            cur.close()

            username = user[0] if user else "User"

            session.clear()
            session["user_id"] = user_id
            session["username"] = username

            return redirect(url_for("dashboard.dashboard"))

        else:
            flash("Face verification failed", "danger")
            session.clear()
            return redirect(url_for("auth.login"))

    return render_template("face_verification.html")


# =====================================================
# RESET FACE VERIFICATION
# =====================================================
@auth_bp.route("/reset-face-verification", methods=["GET","POST"])
def reset_face_verification():

    if not session.get("otp_verified_reset"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        face_image = request.form.get("face_embedding")

        if verify_face_embedding(session["reset_user_id"], face_image):

            session["face_verified_reset"] = True

            return redirect(url_for("auth.reset_password"))

        else:
            flash("Face verification failed", "danger")
            return redirect(url_for("auth.login"))

    return render_template("reset_face.html")

#======================================================
# RESET PASSWORD
#======================================================
@auth_bp.route("/reset-password", methods=["GET","POST"])
def reset_password():

    if not session.get("face_verified_reset"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            flash("Passwords do not match", "danger")
            return render_template("reset_password.html")

        hashed_password = bcrypt.hashpw(
            password1.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur = mysql.connection.cursor()

        cur.execute("""
        UPDATE users
        SET password_hash=%s
        WHERE id=%s
        """, (hashed_password, session["reset_user_id"]))

        mysql.connection.commit()
        cur.close()

        session.clear()

        flash("Password reset successful!", "success")

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")

#======================================================
# Continuous Check API
#======================================================
@auth_bp.route("/continuous-check", methods=["POST"])
def continuous_check():

    if "user_id" not in session:
        return {"status": "logout"}

    user_id = session["user_id"]

    dwell_time = float(request.json.get("dwell_time", 0))
    flight_time = float(request.json.get("flight_time", 0))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT avg_typing_time, std_typing_time,
               avg_flight_time, std_flight_time
        FROM user_baseline
        WHERE user_id=%s
    """, (user_id,))

    baseline = cur.fetchone()
    cur.close()

    if not baseline:
        return {"status": "ok"}

    avg_typing, std_typing, avg_flight, std_flight = baseline

    typing_z = abs(dwell_time - avg_typing) / (std_typing + 0.0001)
    flight_z = abs(flight_time - avg_flight) / (std_flight + 0.0001)

    keystroke_z = (typing_z + flight_z) / 2

    print("Continuous typing Z:", keystroke_z)

    if keystroke_z > 3:
        return {"status": "step_up"}

    return {"status": "ok"}

# =====================================================
# LOGOUT
# =====================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
