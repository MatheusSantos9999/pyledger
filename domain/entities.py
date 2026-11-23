from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from domain.enums import AccountStatus, TransactionType, TransactionStatus, EntryType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Account:
    id: int
    user_id: int
    currency: str = 'BRL'
    status: AccountStatus = AccountStatus.ACTIVE
    balance : Decimal = Decimal("0.00")
    created_at: datetime = field(default_factory = utc_now)
    updated_at: datetime = field(default_factory = utc_now)
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE

@dataclass
class Transaction:
    type: TransactionType
    amount: Decimal
    destination_account_id:int
    source_account_id: int | None = None
    status : TransactionStatus = TransactionStatus.PENDING
    description: str | None = None
    id: int | None = None
    created_at: datetime = field(default_factory = utc_now)


@dataclass(frozen=True)
class LedgerEntry:
    account_id: int
    entry_type: EntryType
    amount: Decimal
    transaction_id : int | None = None
    id: int | None = None
    created_at : datetime = field(default_factory = utc_now)