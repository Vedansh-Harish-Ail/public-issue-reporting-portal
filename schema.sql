
CREATE TABLE IF NOT EXISTS panchayath (
    id SERIAL PRIMARY KEY,
    name TEXT,
    district TEXT,
    state TEXT
);

CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password_hash TEXT,
    panchayath_id INTEGER REFERENCES panchayath(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    mobile TEXT,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    panchayath_id INTEGER REFERENCES panchayath(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    category TEXT,
    description TEXT,
    location TEXT,
    photo_path TEXT,
    status TEXT DEFAULT 'Pending',
    tracking_id TEXT UNIQUE,
    rejection_reason TEXT,
    reporter_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notices ( 
    id SERIAL PRIMARY KEY,
    panchayath_id INTEGER REFERENCES panchayath(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    banner_path TEXT,
    expiry_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    panchayath_id INTEGER REFERENCES panchayath(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
