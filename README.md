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
├── app.py                        
├── config.py                     
├── extensions.py                 
├── requirements.txt            
├── .env.example                  
│
├── database/
│   ├── db.py                     
│   └── schema.sql                
│
├── models/
│   ├── baseline_model.py         
│   ├── face_auth.py              
│   ├── interaction_matrix.py     
│   ├── keystrokes_model.py       
│   ├── login_history_model.py    
│   └── quantum_risk_engine.py    
│
├── routes/
│   ├── auth_routes.py            
│   ├── mfa_routes.py             
│   └── dashboard_routes.py       
│
├── static/
│   └── js/
│       ├── keystroke.js          
│       └── facelock.js           
│
└── templates/                    
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

## 📸 Screenshots

### 🏠 Home Page
<img width="1918" height="970" alt="Home Page" src="https://github.com/user-attachments/assets/e6b647c1-16c1-48b3-aa50-5085731ecc5e" />

### 📝 Register Page
<img width="1901" height="971" alt="Register Page" src="https://github.com/user-attachments/assets/71049595-6595-44a2-9de0-5afd82a99e7e" />

### 🔑 Login Page
<img width="1918" height="972" alt="Login Page" src="https://github.com/user-attachments/assets/5f9ce770-846a-43ba-8603-bed32ebb0cdc" />

### 📊 Dashboard
<img width="1913" height="910" alt="Dashboard Page" src="https://github.com/user-attachments/assets/fc963944-a139-4c70-828a-c6d834798e94" />

### 📧 OTP Verification
<img width="1918" height="970" alt="OTP Page" src="https://github.com/user-attachments/assets/cfcc559e-d7e9-4e9a-9c2f-16c693298803" />

### 🔒 Face Verification
<img width="1917" height="900" alt="Face Verification Page" src="https://github.com/user-attachments/assets/b06af74e-99d8-4d2f-9512-561d9ab888e0" />

### 📲 Push Notification Approval
<img width="1912" height="914" alt="Push Notification Page" src="https://github.com/user-attachments/assets/e9afb4df-ae86-495d-9f2b-0ce7fbab1e3f" />


> 💡 **Authentication Flow:** Home → Register → Login (keystroke capture) → Risk Evaluation → MFA (OTP / Push / Face Lock) → Dashboard

---

## 📌 Note

This project was built as a portfolio project demonstrating adaptive authentication using behavioral biometrics and machine learning. It is not intended for production use without further security hardening.

---

## 👩‍💻 Author

- **Name:** Arthi P
- **LinkedIn:** https://www.linkedin.com/in/arthi-palanivel-0b7437264
- **GitHub:** https://github.com/ArthiPalanivel
