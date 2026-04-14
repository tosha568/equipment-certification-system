CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    login VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INT REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- ORGANIZATIONS
-- =========================
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    contact_person VARCHAR(255),
    address TEXT,
    notes TEXT
);

-- =========================
-- MANUFACTURERS
-- =========================
CREATE TABLE manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    address TEXT,
    notes TEXT
);

-- =========================
-- EQUIPMENT TYPES
-- =========================
CREATE TABLE equipment_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- =========================
-- SAMPLE STATUSES
-- =========================
CREATE TABLE sample_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- =========================
-- PROCESS STATUSES
-- =========================
CREATE TABLE process_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INT
);

-- =========================
-- APPLICATIONS
-- =========================
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    application_number VARCHAR(100) NOT NULL,
    organization_id INT REFERENCES organizations(id),
    created_by_user_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);

-- =========================
-- EQUIPMENT
-- =========================
CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    application_id INT REFERENCES applications(id),
    manufacturer_id INT REFERENCES manufacturers(id),
    equipment_type_id INT REFERENCES equipment_types(id),
    sample_status_id INT REFERENCES sample_statuses(id),
    current_process_status_id INT REFERENCES process_statuses(id),
    name VARCHAR(255),
    serial_number VARCHAR(100),
    created_by_user_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- STATUS HISTORY
-- =========================
CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id),
    old_status_id INT REFERENCES process_statuses(id),
    new_status_id INT REFERENCES process_statuses(id),
    changed_by_user_id INT REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);

-- =========================
-- CERTIFICATION DECISIONS
-- =========================
CREATE TABLE certification_decisions (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id),
    decision_by_user_id INT REFERENCES users(id),
    decision_role_id INT REFERENCES roles(id),
    decision VARCHAR(100),
    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);