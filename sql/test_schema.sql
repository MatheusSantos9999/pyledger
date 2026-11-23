BEGIN;

DO $$
DECLARE
    v_user_a BIGINT;
    v_user_b BIGINT;
    v_acc_a  BIGINT;
    v_acc_b  BIGINT;
    v_tx_id  BIGINT;
    v_hash   VARCHAR(64) := repeat('a', 64);
BEGIN
    -- =========================================================
    -- 0. CAMINHO FELIZ (precisa passar tudo sem erro)
    -- =========================================================
    INSERT INTO users (full_name, email, cpf, password_hash)
    VALUES ('Alice Silva', 'alice@test.com', '01234567890', 'hash_fake_1')
    RETURNING id INTO v_user_a;

    INSERT INTO users (full_name, email, cpf, password_hash)
    VALUES ('Bruno Costa', 'bruno@test.com', '98765432100', 'hash_fake_2')
    RETURNING id INTO v_user_b;

    INSERT INTO accounts (user_id, balance)
    VALUES (v_user_a, 100.00)
    RETURNING id INTO v_acc_a;

    INSERT INTO accounts (user_id)
    VALUES (v_user_b)
    RETURNING id INTO v_acc_b;

    INSERT INTO transactions (type, status, amount, source_account_id, destination_account_id, description)
    VALUES ('DEPOSIT', 'COMPLETED', 100.00, NULL, v_acc_a, 'Deposito inicial')
    RETURNING id INTO v_tx_id;

    INSERT INTO ledger_entries (transaction_id, account_id, entry_type, amount)
    VALUES (v_tx_id, v_acc_a, 'CREDIT', 100.00);

    INSERT INTO idempotency_keys (key, user_id, request_hash, transaction_id, status)
    VALUES ('key-001', v_user_a, v_hash, v_tx_id, 'COMPLETED');

    RAISE NOTICE 'OK [0/11]: Caminho feliz inserido com sucesso (inclusive CPF come�ando com zero!).';

    -- =========================================================
    -- 1 a 10. ATAQUES COM DADOS INVALIDOS (todos DEVEM ser bloqueados)
    -- =========================================================

    -- 1. CPF curto
    BEGIN
        INSERT INTO users (full_name, email, cpf, password_hash)
        VALUES ('Invalido', 'inv1@test.com', '123', 'hash');
        RAISE EXCEPTION 'FALHA [1]: aceitou CPF com menos de 11 digitos!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [1/11]: CPF curto bloqueado.';
    END;

    -- 2. CPF com letra
    BEGIN
        INSERT INTO users (full_name, email, cpf, password_hash)
        VALUES ('Invalido', 'inv2@test.com', '1234567890a', 'hash');
        RAISE EXCEPTION 'FALHA [2]: aceitou CPF com letra!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [2/11]: CPF com letra bloqueado.';
    END;

    -- 3. E-mail duplicado
    BEGIN
        INSERT INTO users (full_name, email, cpf, password_hash)
        VALUES ('Clone', 'alice@test.com', '11122233344', 'hash');
        RAISE EXCEPTION 'FALHA [3]: aceitou e-mail duplicado!';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'OK [3/11]: E-mail duplicado bloqueado.';
    END;

    -- 4. Moeda minuscula
    BEGIN
        UPDATE accounts SET currency = 'brl' WHERE id = v_acc_a;
        RAISE EXCEPTION 'FALHA [4]: aceitou moeda em minusculo!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [4/11]: Moeda invalida bloqueada.';
    END;

    -- 5. Saldo negativo
    BEGIN
        UPDATE accounts SET balance = -0.01 WHERE id = v_acc_a;
        RAISE EXCEPTION 'FALHA [5]: aceitou saldo negativo!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [5/11]: Saldo negativo bloqueado.';
    END;

    -- 6. Status inventado
    BEGIN
        UPDATE accounts SET status = 'BANANA' WHERE id = v_acc_a;
        RAISE EXCEPTION 'FALHA [6]: aceitou status inexistente!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [6/11]: Status invalido bloqueado.';
    END;

    -- 7. DEPOSIT com source_account_id preenchido
    BEGIN
        INSERT INTO transactions (type, amount, source_account_id, destination_account_id)
        VALUES ('DEPOSIT', 50.00, v_acc_a, v_acc_b);
        RAISE EXCEPTION 'FALHA [7]: aceitou DEPOSIT com conta de origem!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [7/11]: DEPOSIT com conta de origem bloqueado.';
    END;

    -- 8. TRANSFER para a propria conta
    BEGIN
        INSERT INTO transactions (type, amount, source_account_id, destination_account_id)
        VALUES ('TRANSFER', 50.00, v_acc_a, v_acc_a);
        RAISE EXCEPTION 'FALHA [8]: aceitou TRANSFER para a mesma conta!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [8/11]: TRANSFER para a propria conta bloqueada.';
    END;

    -- 9. TRANSFER com valor zero
    BEGIN
        INSERT INTO transactions (type, amount, source_account_id, destination_account_id)
        VALUES ('TRANSFER', 0.00, v_acc_a, v_acc_b);
        RAISE EXCEPTION 'FALHA [9]: aceitou valor zero!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK [9/11]: Valor zero bloqueado.';
    END;

    -- 10. Mesma idempotency key pro MESMO usuario
    BEGIN
        INSERT INTO idempotency_keys (key, user_id, request_hash)
        VALUES ('key-001', v_user_a, v_hash);
        RAISE EXCEPTION 'FALHA [10]: aceitou mesma chave de idempotencia pro mesmo usuario!';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'OK [10/11]: Chave repetida pro mesmo usuario bloqueada.';
    END;


    RAISE NOTICE 'OK [11/11]: Mesma key em usuarios diferentes e mesmo hash em chaves novas passaram!';
    RAISE NOTICE '=== TODOS OS 11 TESTES PASSARAM! ===';
END $$;

ROLLBACK; -- desfaz tudo no final pra deixar o banco limpo   