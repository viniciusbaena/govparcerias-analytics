CREATE TABLE source_sync (id bigserial PRIMARY KEY, source_name text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz, status text NOT NULL, records_read bigint DEFAULT 0, error_message text);
CREATE TABLE municipality (ibge_code char(7) PRIMARY KEY, name text NOT NULL, state char(2) NOT NULL, population bigint, latitude numeric, longitude numeric, official_site text, mayor_name text, source_url text, verified_at timestamptz);
CREATE TABLE program (id bigint PRIMARY KEY, code text, name text, agency_name text, situation text, raw_data jsonb NOT NULL, source_updated_at timestamptz);
CREATE TABLE partnership (id bigint PRIMARY KEY, instrument_number text, municipality_ibge char(7) REFERENCES municipality(ibge_code), program_id bigint REFERENCES program(id), object text, situation text, global_value numeric(18,2), transfer_value numeric(18,2), counterpart_value numeric(18,2), start_date date, end_date date, raw_data jsonb NOT NULL, source_updated_at timestamptz);
CREATE INDEX idx_partnership_municipality ON partnership(municipality_ibge);
CREATE INDEX idx_partnership_situation ON partnership(situation);
CREATE INDEX idx_partnership_end_date ON partnership(end_date);
