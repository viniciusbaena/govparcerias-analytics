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

-- v0.7: dossiê financeiro, documental e de engenharia com proveniência obrigatória
CREATE TABLE IF NOT EXISTS source_record (
  id BIGSERIAL PRIMARY KEY,
  source_system TEXT NOT NULL,
  source_endpoint TEXT NOT NULL,
  source_external_id TEXT NOT NULL,
  official_url TEXT,
  collected_at TIMESTAMPTZ NOT NULL,
  payload_hash CHAR(64) NOT NULL,
  connector_version TEXT NOT NULL,
  raw_payload JSONB NOT NULL,
  validation_status TEXT NOT NULL,
  UNIQUE(source_system, source_endpoint, source_external_id, payload_hash)
);
CREATE TABLE IF NOT EXISTS instrument_dossier (
  id BIGSERIAL PRIMARY KEY,
  instrument_number TEXT NOT NULL UNIQUE,
  proposal_number TEXT,
  instrument_type TEXT,
  status TEXT,
  object_text TEXT,
  grantor_name TEXT,
  recipient_name TEXT,
  recipient_document TEXT,
  municipality_ibge TEXT,
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS financial_summary (
  instrument_id BIGINT PRIMARY KEY REFERENCES instrument_dossier(id),
  global_amount NUMERIC(20,2), transfer_amount NUMERIC(20,2), counterpart_amount NUMERIC(20,2),
  financial_counterpart NUMERIC(20,2), goods_services_counterpart NUMERIC(20,2), investment_income NUMERIC(20,2),
  committed_amount NUMERIC(20,2), released_amount NUMERIC(20,2), paid_amount NUMERIC(20,2), executed_amount NUMERIC(20,2),
  checking_balance NUMERIC(20,2), investment_balance NUMERIC(20,2),
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS amendment_resource (
  id BIGSERIAL PRIMARY KEY, instrument_id BIGINT NOT NULL REFERENCES instrument_dossier(id), amendment_number TEXT,
  amendment_year INTEGER, amendment_type TEXT, author_name TEXT, parliamentarian_code TEXT, parliamentarian_name TEXT,
  party TEXT, parliamentarian_state CHAR(2), amendment_amount NUMERIC(20,2), gnd3_amount NUMERIC(20,2), gnd4_amount NUMERIC(20,2),
  beneficiary_name TEXT, beneficiary_document TEXT, source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS bank_account (
  id BIGSERIAL PRIMARY KEY, instrument_id BIGINT NOT NULL REFERENCES instrument_dossier(id), bank_name TEXT, branch_number TEXT,
  branch_city TEXT, branch_state CHAR(2), account_number TEXT, account_type TEXT, account_name TEXT, opened_at DATE,
  status TEXT, checking_balance NUMERIC(20,2), checking_balance_at DATE, investment_balance NUMERIC(20,2), investment_balance_at DATE,
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS bank_transaction (
  id BIGSERIAL PRIMARY KEY, bank_account_id BIGINT NOT NULL REFERENCES bank_account(id), movement_at TIMESTAMPTZ,
  transaction_type TEXT, operation_type TEXT, amount NUMERIC(20,2), depositor_name TEXT, depositor_masked_id TEXT,
  beneficiary_name TEXT, beneficiary_masked_id TEXT, origin_bank TEXT, origin_branch TEXT, origin_account TEXT,
  destination_bank TEXT, destination_branch TEXT, destination_account TEXT, history TEXT,
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS engineering_work (
  id BIGSERIAL PRIMARY KEY, instrument_id BIGINT NOT NULL REFERENCES instrument_dossier(id), official_work_id TEXT,
  work_name TEXT, work_type TEXT, address TEXT, latitude NUMERIC(10,7), longitude NUMERIC(10,7), status TEXT,
  physical_progress NUMERIC(7,4), financial_progress NUMERIC(7,4), planned_start DATE, actual_start DATE,
  planned_end DATE, actual_end DATE, technical_responsible TEXT, art_rrt TEXT, contractor_name TEXT,
  contractor_document TEXT, execution_contract_number TEXT, execution_contract_amount NUMERIC(20,2),
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS inspection (
  id BIGSERIAL PRIMARY KEY, work_id BIGINT NOT NULL REFERENCES engineering_work(id), inspected_at TIMESTAMPTZ,
  inspection_type TEXT, responsible_body TEXT, inspector_name TEXT, participants JSONB, verified_progress NUMERIC(7,4),
  findings TEXT, pending_items TEXT, recommendations TEXT, remediation_due_at DATE, latitude NUMERIC(10,7), longitude NUMERIC(10,7),
  source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE TABLE IF NOT EXISTS official_document (
  id BIGSERIAL PRIMARY KEY, instrument_id BIGINT REFERENCES instrument_dossier(id), work_id BIGINT REFERENCES engineering_work(id),
  inspection_id BIGINT REFERENCES inspection(id), title TEXT NOT NULL, document_type TEXT NOT NULL, issued_at DATE,
  issuer TEXT, official_url TEXT NOT NULL, file_hash CHAR(64), mime_type TEXT, file_size BIGINT, classification TEXT,
  extracted_text TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, source_record_id BIGINT NOT NULL REFERENCES source_record(id)
);
CREATE INDEX IF NOT EXISTS idx_document_search ON official_document USING gin (to_tsvector('portuguese', coalesce(title,'') || ' ' || coalesce(extracted_text,'')));

-- v0.9: carteira administrativa e visão territorial, separadas da base oficial
CREATE TABLE IF NOT EXISTS portfolio_version (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  source_file_name TEXT NOT NULL,
  source_file_sha256 CHAR(64) NOT NULL,
  imported_at TIMESTAMPTZ NOT NULL,
  record_count INTEGER NOT NULL,
  provenance_note TEXT NOT NULL,
  UNIQUE(name, version)
);
CREATE TABLE IF NOT EXISTS portfolio_municipality (
  portfolio_version_id BIGINT NOT NULL REFERENCES portfolio_version(id),
  municipality_ibge CHAR(7) NOT NULL,
  municipality_name TEXT NOT NULL,
  recipient_document CHAR(14) NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  source_row INTEGER NOT NULL,
  PRIMARY KEY(portfolio_version_id, municipality_ibge),
  UNIQUE(portfolio_version_id, recipient_document)
);
CREATE INDEX IF NOT EXISTS ix_portfolio_municipality_name ON portfolio_municipality(municipality_name);
COMMENT ON TABLE portfolio_municipality IS 'Recorte administrativo fornecido pela equipe. Não substitui validação cadastral em fonte pública oficial.';
