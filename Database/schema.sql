CREATE DATABASE quantum_auth;
USE quantum_auth;
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(150),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    ip_address VARCHAR(45),
    device_info VARCHAR(255),
    location VARCHAR(100), 
    typing_time FLOAT NOT NULL DEFAULT 0,
	keystroke_pattern JSON NULL,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    flight_time FLOAT NOT NULL DEFAULT 0,
    risk_score FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE typing_samples (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    typing_time FLOAT NOT NULL,
    flight_time FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE keystroke_patterns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pattern_vector TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_baseline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    trust_score FLOAT DEFAULT 70,
    avg_typing_time FLOAT NOT NULL,
    std_typing_time FLOAT NOT NULL,
    avg_flight_time FLOAT NOT NULL,
    std_flight_time FLOAT NOT NULL,

    device_hash VARCHAR(255) NOT NULL,
    login_hour FLOAT NOT NULL,
    face_embedding VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE login_attempts (
    username VARCHAR(255) PRIMARY KEY,
    user_id INT,
    attempts INT DEFAULT 0,
    lock_until DATETIME
);
ALTER TABLE login_history
ADD COLUMN dwell_time FLOAT;

ALTER TABLE users ADD COLUMN face_embedding LONGTEXT;

ALTER TABLE user_baseline 
MODIFY face_embedding LONGTEXT;
