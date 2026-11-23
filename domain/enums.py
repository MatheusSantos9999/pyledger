from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'
    CLOSED = 'CLOSED'


class TransactionType(StrEnum):
    DEPOSIT = 'DEPOSIT'
    TRANSFER = 'TRANSFER'


class TransactionStatus(StrEnum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class EntryType(StrEnum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'


class IdempotencyStatus(StrEnum):
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

