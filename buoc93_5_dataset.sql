CREATE TABLE IF NOT EXISTS ai_real_room_dataset (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    district VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    price NUMERIC(14,2) NOT NULL CHECK (price > 0),
    area NUMERIC(10,2) NOT NULL CHECK (area > 0),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    source_url TEXT NOT NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    location_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_method TEXT,
    verification_note TEXT,
    CONSTRAINT valid_latitude CHECK (
        latitude IS NULL OR latitude BETWEEN -90 AND 90
    ),
    CONSTRAINT valid_longitude CHECK (
        longitude IS NULL OR longitude BETWEEN -180 AND 180
    )
);

CREATE INDEX IF NOT EXISTS idx_ai_real_room_district
ON ai_real_room_dataset(district);
