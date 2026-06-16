CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(150),
    password_hash VARCHAR(255),
    registered_device_id VARCHAR(255),
    registered_location VARCHAR(255),
    baseline_keystroke FLOAT,
    baseline_typing_speed FLOAT,
    baseline_risk_score FLOAT,
    face_image_path VARCHAR(255),
    face_embedding LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE login_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    device_id VARCHAR(255),
    location VARCHAR(255),
    keystroke_score FLOAT,
    typing_speed FLOAT,
    risk_score FLOAT,
    status VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE otp_verifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    otp_code VARCHAR(10),
    expires_at DATETIME,
    verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
