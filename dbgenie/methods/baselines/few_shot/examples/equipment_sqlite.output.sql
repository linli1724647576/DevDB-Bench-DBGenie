CREATE TABLE members (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipment (
    id INTEGER PRIMARY KEY,
    equipment_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    condition_status TEXT NOT NULL DEFAULT 'GOOD' CHECK (
        condition_status IN ('GOOD', 'NEEDS_SERVICE', 'OUT_OF_SERVICE', 'RETIRED')
    ),
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    acquired_on TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'CONFIRMED', 'CHECKED_OUT', 'COMPLETED', 'CANCELLED')
    ),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ends_at > starts_at),
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE RESTRICT,
    FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE RESTRICT
);

CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY,
    equipment_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (
        status IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
    ),
    notes TEXT,
    cost NUMERIC NOT NULL DEFAULT 0 CHECK (cost >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE RESTRICT
);

CREATE INDEX ix_members_active_email
    ON members (is_active, email);

CREATE INDEX ix_equipment_category_available_name
    ON equipment (category, is_available, name);

CREATE INDEX ix_reservations_member_status_start
    ON reservations (member_id, status, starts_at);

CREATE INDEX ix_reservations_equipment_time
    ON reservations (equipment_id, starts_at, ends_at);

CREATE INDEX ix_maintenance_equipment_service
    ON maintenance_records (equipment_id, service_date DESC);
