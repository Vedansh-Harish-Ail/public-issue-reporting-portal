-- schema.sql (Updated to match current production structure)

CREATE TABLE IF NOT EXISTS panchayath (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    district TEXT,
    state TEXT
);

CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT,
    panchayath_id INTEGER,
    FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    mobile TEXT,
    password_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panchayath_id INTEGER,
    user_id INTEGER,
    category TEXT,
    description TEXT,
    location TEXT,
    photo_path TEXT,
    status TEXT DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notices ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panchayath_id INTEGER,
    title TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (panchayath_id) REFERENCES panchayath(id) ON DELETE CASCADE
);

-- Seed Initial Data
-- INSERT INTO panchayath (name, district, state) VALUES ('Demo Panchayath', 'Demo District', 'Demo State');
-- INSERT INTO admin (username, password_hash, panchayath_id) VALUES ('admin', 'pbkdf2:sha256:260000$...', 1);
