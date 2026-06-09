-- 테스트용 사용자 결제 확인 데이터 Seed SQL
-- docker/database/init/1_seed_payments_test.sql

-- 1. 테스트 사용자 추가 (멱등)
INSERT INTO users (user_id, email, display_name, role, status, created_at)
VALUES 
    ('8a514d86-0421-4f11-8be8-27b003666b69', 'test_user1@example.com', '테스트유저1', 'user', 'active', NOW() - INTERVAL '10 days'),
    ('3b8f10e4-9db2-4876-96a9-8ea51368dfcf', 'test_user2@example.com', '테스트유저2', 'user', 'active', NOW() - INTERVAL '10 days')
ON CONFLICT (user_id) DO NOTHING;

-- 2. payments 데이터 삽입

-- 2.1. 구독 결제 완료 건 (오늘 결제 성공)
INSERT INTO payments (
    payment_id, user_id, product_type, plan_id, pg_provider, pg_transaction_id, 
    last_transaction_key, order_name, payment_method, total_amount, balance_amount, 
    amount, status, paid_at, requested_at, approved_at, created_at
)
VALUES (
    'aa514d86-0421-4f11-8be8-27b003666b01', 
    '8a514d86-0421-4f11-8be8-27b003666b69', 
    'subscription', 
    (SELECT plan_id FROM plans WHERE plan_code = 'pro' LIMIT 1), 
    'toss', 'pg_tx_001', 'tx_key_001', 'Pro 구독 플랜', '카드', 2900, 2900, 
    2900, 'success', NOW(), NOW() - INTERVAL '5 minutes', NOW(), NOW()
)
ON CONFLICT (payment_id) DO NOTHING;

-- 2.2. 크레딧 결제 완료 건 (오늘 결제 성공)
INSERT INTO payments (
    payment_id, user_id, product_type, credit_plan_id, pg_provider, pg_transaction_id, 
    last_transaction_key, order_name, payment_method, total_amount, balance_amount, 
    amount, status, paid_at, requested_at, approved_at, created_at
)
VALUES (
    'aa514d86-0421-4f11-8be8-27b003666b02', 
    '8a514d86-0421-4f11-8be8-27b003666b69', 
    'credit', 
    (SELECT credit_plan_id FROM credit_plans WHERE credit_plan_code = 'credit_100' LIMIT 1), 
    'toss', 'pg_tx_002', 'tx_key_002', '100 Credits', '간편결제', 5000, 5000, 
    5000, 'success', NOW(), NOW() - INTERVAL '10 minutes', NOW(), NOW()
)
ON CONFLICT (payment_id) DO NOTHING;

-- 크레딧 결제에 따른 크레딧 ledger 기록 (멱등)
INSERT INTO credit_ledger (ledger_id, user_id, amount, balance_after, entry_type, source_type, source_id, description, created_at)
VALUES (
    'bb514d86-0421-4f11-8be8-27b003666b02',
    '8a514d86-0421-4f11-8be8-27b003666b69',
    100, 100, 'purchase', 'payment', 'aa514d86-0421-4f11-8be8-27b003666b02',
    '100 Credits 충전 결제', NOW()
)
ON CONFLICT (ledger_id) DO NOTHING;

-- 2.3. 환불 처리된 결제 건 (과거 결제 후 환불)
INSERT INTO payments (
    payment_id, user_id, product_type, credit_plan_id, pg_provider, pg_transaction_id, 
    last_transaction_key, order_name, payment_method, total_amount, balance_amount, 
    amount, status, paid_at, requested_at, approved_at, refunded_at, created_at
)
VALUES (
    'aa514d86-0421-4f11-8be8-27b003666b03', 
    '3b8f10e4-9db2-4876-96a9-8ea51368dfcf', 
    'credit', 
    (SELECT credit_plan_id FROM credit_plans WHERE credit_plan_code = 'credit_100' LIMIT 1), 
    'toss', 'pg_tx_003', 'tx_key_003', '100 Credits', '카드', 5000, 0, 
    5000, 'refunded', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day 5 minutes', NOW() - INTERVAL '1 day', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 day'
)
ON CONFLICT (payment_id) DO NOTHING;

-- 2.4. 결제 실패 건
INSERT INTO payments (
    payment_id, user_id, product_type, plan_id, pg_provider, pg_transaction_id, 
    last_transaction_key, order_name, total_amount, balance_amount, 
    amount, status, created_at
)
VALUES (
    'aa514d86-0421-4f11-8be8-27b003666b04', 
    '3b8f10e4-9db2-4876-96a9-8ea51368dfcf', 
    'subscription', 
    (SELECT plan_id FROM plans WHERE plan_code = 'pro' LIMIT 1), 
    'toss', 'pg_tx_004', 'tx_key_004', 'Pro 구독 플랜', 2900, 2900, 
    2900, 'failed', NOW() - INTERVAL '2 days'
)
ON CONFLICT (payment_id) DO NOTHING;

-- 2.5. 결제 대기 건 (pending)
INSERT INTO payments (
    payment_id, user_id, product_type, credit_plan_id, pg_provider, pg_transaction_id, 
    last_transaction_key, order_name, total_amount, balance_amount, 
    amount, status, created_at
)
VALUES (
    'aa514d86-0421-4f11-8be8-27b003666b05', 
    '3b8f10e4-9db2-4876-96a9-8ea51368dfcf', 
    'credit', 
    (SELECT credit_plan_id FROM credit_plans WHERE credit_plan_code = 'credit_500' LIMIT 1), 
    'toss', 'pg_tx_005', 'tx_key_005', '500 Credits', 20000, 20000, 
    20000, 'pending', NOW() - INTERVAL '3 hours'
)
ON CONFLICT (payment_id) DO NOTHING;
