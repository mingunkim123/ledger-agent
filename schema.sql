-- ============================================
-- 가계부 에이전트 - MVP DB 스키마 (PostgreSQL)
-- ============================================

-- 확장 (UUID 생성용)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- --------------------------------------------
-- 1. transactions (거래 내역)
-- --------------------------------------------
CREATE TABLE transactions (
    tx_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        TEXT NOT NULL,
    occurred_date  DATE NOT NULL,
    type           TEXT NOT NULL CHECK (type IN ('expense', 'income')),
    amount         INTEGER NOT NULL CHECK (amount > 0),
    currency       TEXT NOT NULL DEFAULT 'KRW',
    category       TEXT NOT NULL,
    subcategory    TEXT NOT NULL DEFAULT '기타',
    merchant       TEXT,
    memo           TEXT,
    source_text    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 조회용 인덱스
CREATE INDEX idx_transactions_user_date ON transactions (user_id, occurred_date DESC);
CREATE INDEX idx_transactions_user_category ON transactions (user_id, category);
CREATE INDEX idx_transactions_user_subcategory ON transactions (user_id, subcategory);

-- --------------------------------------------
-- 2. idempotency_keys (중복 방지)
-- --------------------------------------------
CREATE TABLE idempotency_keys (
    user_id    TEXT NOT NULL,
    idem_key   TEXT NOT NULL,
    tx_id      UUID NOT NULL REFERENCES transactions(tx_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, idem_key)
);

-- --------------------------------------------
-- 3. audit_logs (감사 로그)
-- --------------------------------------------
CREATE TABLE audit_logs (
    event_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    TEXT NOT NULL,
    action     TEXT NOT NULL CHECK (action IN ('create', 'update', 'delete', 'undo')),
    tx_id      UUID REFERENCES transactions(tx_id) ON DELETE SET NULL,
    before_snapshot JSONB,
    after_snapshot  JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_logs_user_created ON audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_logs_tx ON audit_logs (tx_id);

-- --------------------------------------------
-- updated_at 자동 갱신 트리거
-- --------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at();
