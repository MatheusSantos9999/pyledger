CREATE TABLE users(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	full_name VARCHAR(100) NOT NULL,
	email VARCHAR(255) UNIQUE NOT NULL,
	cpf CHAR(11) UNIQUE NOT NULL CHECK (cpf ~ '^[0-9]{11}$'),
	password_hash TEXT NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE accounts(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	user_id BIGINT UNIQUE NOT NULL REFERENCES users(id),
	currency CHAR(3) NOT NULL DEFAULT 'BRL' CHECK(currency ~ '^[A-Z]{3}$'),
	status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
		CHECK (status IN ('ACTIVE', 'BLOCKED', 'CLOSED')),
	balance NUMERIC(12,2) NOT NULL CHECK (balance >= 0) DEFAULT 0,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE transactions(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	type VARCHAR(20) NOT NULL CHECK (type IN ('DEPOSIT', 'TRANSFER')),
	status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
		CHECK(status IN ('PENDING', 'COMPLETED', 'FAILED')),
	amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
	source_account_id BIGINT NULL REFERENCES accounts(id),
	destination_account_id BIGINT NOT NULL REFERENCES accounts(id),
	CONSTRAINT chk_source_account CHECK(
		(type = 'DEPOSIT'
		 AND source_account_id IS NULL
		 AND destination_account_id IS NOT NULL) OR
		(type = 'TRANSFER'
		 AND source_account_id IS NOT NULL
		 AND destination_account_id IS NOT NULL
		 AND source_account_id <> destination_account_id)
		 ),
		 
	description VARCHAR(255) NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
	
);


CREATE TABLE ledger_entries(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	transaction_id BIGINT NOT NULL REFERENCES transactions(id),
	account_id BIGINT NOT NULL REFERENCES accounts(id),
	entry_type VARCHAR(10) NOT NULL CHECK(entry_type IN('DEBIT', 'CREDIT')),
	amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE idempotency_keys(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	key VARCHAR(255) NOT NULL,
	user_id BIGINT NOT NULL REFERENCES users(id),
	request_hash VARCHAR(64) NOT NULL,
	transaction_id BIGINT NULL REFERENCES transactions(id),
	status VARCHAR(20) NOT NULL DEFAULT 'PROCESSING'
		CHECK(status IN ('PROCESSING', 'COMPLETED', 'FAILED')),
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	CONSTRAINT idempotency_key UNIQUE(user_id, key)
);


CREATE INDEX idx_ledger_entries_account_created_at ON ledger_entries(account_id, created_at DESC);
CREATE INDEX idx_ledger_entries_transaction_id ON ledger_entries(transaction_id);
CREATE INDEX idx_transactions_source_account ON transactions(source_account_id);
CREATE INDEX idx_transactions_destination_account ON transactions(destination_account_id);

