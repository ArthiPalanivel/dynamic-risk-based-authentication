# 🔐 Dynamic Risk-Based Authentication System

A Flask-based intelligent authentication system that dynamically evaluates user risk at login using **keystroke dynamics**, **face recognition**, and **behavioral modeling** — then decides the appropriate level of Multi-Factor Authentication (MFA) in real time.

---

## 🚀 Features

- **Keystroke Dynamics Analysis** — Captures typing patterns (dwell time, flight time) and compares them against the user's baseline profile
- **Face Recognition (DeepFace + FaceNet512)** — Verifies identity using cosine similarity on facial embeddings stored in the database
- **Quantum-Inspired Risk Engine** — Encodes multiple behavioral signals (keystroke, device, location, time, pattern, travel) as complex amplitudes and computes a weighted risk probability
- **Adaptive MFA** — Automatically selects the authentication step based on risk score:

| Risk Level | Action |
|---|---|
| < 0.25 | ✅ Allow login directly |
| 0.25 – 0.50 | 📧 OTP via Email |
| 0.50 – 0.75 | 📲 Push Notification Approval |
| > 0.75 | 🔒 Face Lock (Live Face Verification) |

- **Baseline Profiling** — Builds a personal behavioral baseline for each user during registration
- **Login History Tracking** — Stores every login attempt with risk scores, device ID, location, and decision
- **Password Reset Flow** — Secure OTP-based password reset with face re-enrollment option

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL (flask-mysqldb) |
| Face Recognition | DeepFace, FaceNet512, OpenCV |
| Behavioral Modeling | NumPy, Statistical Baseline Modeling |
| Frontend | HTML, CSS, JavaScript (Jinja2 Templates) |
| Auth & Security | bcrypt, python-dotenv |

---

## 📁 Project Structure

```
dynamic-risk-based-authentication/
│
├── app.py                        # App factory and entry point
├── config.py                     # Configuration (DB, secret keys)
├── extensions.py                 # Flask extensions
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
│
├── database/
│   ├── db.py                     # MySQL connection setup
│   └── schema.sql                # Database schema (users, login_history, otp)
│
├── models/
│   ├── baseline_model.py         # User behavioral baseline builder
│   ├── face_auth.py              # Face verification using DeepFace
│   ├── interaction_matrix.py     # Quantum interaction matrix for risk signals
│   ├── keystrokes_model.py       # Keystroke dynamics analyzer
│   ├── login_history_model.py    # Login record handler
│   └── quantum_risk_engine.py    # Core risk scoring engine
│
├── routes/
│   ├── auth_routes.py            # Register, login, logout, risk evaluation
│   ├── mfa_routes.py             # OTP and push notification MFA
│   └── dashboard_routes.py       # User dashboard
│
├── static/
│   └── js/
│       ├── keystroke.js          # Captures keystroke timing in browser
│       └── facelock.js           # Webcam capture for face verification
│
└── templates/                    # Jinja2 HTML templates
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── face_verification.html
    ├── otp.html
    └── ...
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/dynamic-risk-based-authentication.git
cd dynamic-risk-based-authentication
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

```.env
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=auth_db
SECRET_KEY=your_secret_key
```

### 4. Set Up the Database

Create the database in MySQL, then run the schema:
```bash
mysql -u root -p auth_db < database/schema.sql
```

### 5. Run the App
```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 🗄️ Database Schema

**`users`** — Stores user credentials, device fingerprint, registered location, behavioral baseline, and face embedding.

**`login_history`** — Logs every login attempt with keystroke score, risk score, device ID, location, and final decision (ALLOW / OTP / PUSH / FACE_LOCK).

**`otp_verifications`** — Manages OTP codes with expiry timestamps for MFA and password reset flows.

---

## 🔒 How the Risk Engine Works

1. At login, the system captures **keystroke timing** (dwell + flight time) from the browser
2. It also collects **device fingerprint**, **location**, **login time**, and **travel anomaly**
3. Each signal is encoded as a **complex amplitude** using a quantum-inspired model
4. A normalized state vector **ψ (psi)** is built across 6 features
5. An **interaction matrix** applies cross-feature correlations
6. The final **risk probability** (0–1) is computed using weighted measurement
7. Based on the score (and a hard keystroke rule), the system routes the user to the appropriate MFA step

---

## 📌 Note

This project was built as a portfolio project demonstrating adaptive authentication using behavioral biometrics and machine learning. It is not intended for production use without further security hardening.

---

## 👩‍💻 Author

Name: Arthi P  
LinkedIn: https://www.linkedin.com/in/arthi-palanivel-0b7437264
GitHub: https://github.com/ArthiPalanivel
