CREATE TABLE source_sync (id bigserial PRIMARY KEY, source_name text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz, status text NOT NULL, records_read bigint DEFAULT 0, error_message text);
CREATE TABLE municipality (ibge_code char(7) PRIMARY KEY, name text NOT NULL, state char(2) NOT NULL, population bigint, latitude numeric, longitude numeric, official_site text, mayor_name text, source_url text, verified_at timestamptz);
CREATE TABLE program (id bigint PRIMARY KEY, code text, name text, agency_name text, situation text, raw_data jsonb NOT NULL, source_updated_at timestamptz);
CREATE TABLE partnership (id bigint PRIMARY KEY, instrument_number text, municipality_ibge char(7) REFERENCES municipality(ibge_code), program_id bigint REFERENCES program(id), object text, situation text, global_value numeric(18,2), transfer_value numeric(18,2), counterpart_value numeric(18,2), start_date date, end_date date, raw_data jsonb NOT NULL, source_updated_at timestamptz);
CREATE INDEX idx_partnership_municipality ON partnership(municipality_ibge);
CREATE INDEX idx_partnership_situation ON partnership(situation);
CREATE INDEX idx_partnership_end_date ON partnership(end_date);

-- Infraestrutura incremental v0.6
CREATE TABLE IF NOT EXISTS sync_run (
  id BIGSERIAL PRIMARY KEY, source VARCHAR(80) NOT NULL, status VARCHAR(30) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL, finished_at TIMESTAMPTZ,
  records_read INTEGER NOT NULL DEFAULT 0, records_changed INTEGER NOT NULL DEFAULT 0,
  details JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS snapshot (
  id BIGSERIAL PRIMARY KEY, entity VARCHAR(100) NOT NULL, external_key VARCHAR(180) NOT NULL,
  fingerprint CHAR(64) NOT NULL, payload JSONB NOT NULL, captured_at TIMESTAMPTZ NOT NULL,
  UNIQUE(entity,external_key,fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_snapshot_lookup ON snapshot(entity,external_key,captured_at DESC);
CREATE TABLE IF NOT EXISTS detected_change (
  id BIGSERIAL PRIMARY KEY, entity VARCHAR(100) NOT NULL, external_key VARCHAR(180) NOT NULL,
  field VARCHAR(120) NOT NULL, before JSONB, after JSONB, detected_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_change_time ON detected_change(detected_at DESC);
CREATE TABLE IF NOT EXISTS alert (
  id BIGSERIAL PRIMARY KEY, type VARCHAR(60) NOT NULL, level VARCHAR(20) NOT NULL,
  title VARCHAR(240) NOT NULL, message TEXT NOT NULL, context JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL, resolved BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_alert_active ON alert(resolved,level,created_at DESC);
