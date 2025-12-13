-- schema.sql

CREATE DATABASE IF NOT EXISTS panchayath_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE panchayath_portal;

CREATE TABLE panchayath (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL,
  UNIQUE KEY uniq_panchayath (name, district, state)
);

CREATE TABLE admin (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  panchayath_id INT NOT NULL,
  FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE
);

CREATE TABLE issues (
  id INT AUTO_INCREMENT PRIMARY KEY,
  panchayath_id INT NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  photo_path VARCHAR(255),
  location VARCHAR(255),
  status ENUM('Pending','In Progress','Completed') DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE,
  INDEX idx_issues_panchayath (panchayath_id, status, category)
);

CREATE TABLE notices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  panchayath_id INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  description TEXT NOT NULL,
  category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE,
  INDEX idx_notices_panchayath (panchayath_id, category)
);

-- Optional seed data
INSERT INTO panchayath (name, district, state) VALUES
('Thrissur Municipal', 'Thrissur', 'Kerala'),
('Irinjalakuda', 'Thrissur', 'Kerala');

-- Example admin (replace with real hash later)
-- UPDATE with generated password hash in app setup.
