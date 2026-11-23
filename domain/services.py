from decimal import Decimal


from domain.entities import Account, LedgerEntry, Transaction, utc_now
from domain.enums import EntryType, TransactionStatus, TransactionType
from domain.exceptions import (
    CurrencyMismatchError,
    InactiveAccountError,
    InsufficientBalanceError,
    InvalidAmountError,
    SameAccountTransferError,
)


def validate_amount(amount:Decimal) -> Decimal:
    if not isinstance(amount, Decimal):
        raise InvalidAmountError('Valor deve ser um decimal!')

    if not amount.is_finite():
        raise InvalidAmountError('O valor deve ser finito!')

    if not amount > Decimal("0"):
        raise InvalidAmountError('O valor deve ser maior que 0!')

    if not amount.as_tuple().exponent >= -2:
        raise InvalidAmountError('O valor deve ter duas casas decimais!')

    return amount.quantize(Decimal("0.01"))


def deposit(
    destination: Account,
    amount: Decimal,
    description: str | None = None,
) -> tuple[Transaction, list[LedgerEntry]]:
    
    amount = validate_amount(amount)

    if not destination.is_active():
        raise InactiveAccountError('A conta está inativa!')
    
    else:
        destination.balance += amount
        destination.updated_at = utc_now()

        transaction = Transaction(type = TransactionType.DEPOSIT, amount = amount, destination_account_id = destination.id, status = TransactionStatus.COMPLETED, description=description)
        credit_entry = LedgerEntry(account_id = destination.id, entry_type = EntryType.CREDIT, amount = amount, transaction_id = transaction.id)    
        return (transaction, [credit_entry]) 


def transfer(
    source: Account,
    destination: Account,
    amount: Decimal,
    description: str | None = None,
) -> tuple[Transaction, list[LedgerEntry]]:
    
    amount = validate_amount(amount)
    
    if source.id == destination.id:
        raise SameAccountTransferError('Transferencia para a mesma conta!')

    if not source.is_active() or not destination.is_active():
        raise InactiveAccountError('A conta está inativa!')

    if source.currency != destination.currency:
        raise CurrencyMismatchError('Erro ao fazer a transferencia, as moedas são diferentes!')

    if not source.balance >= amount:
        raise InsufficientBalanceError ('Saldo insuficiente!')

    else:
        source.balance -= amount
        destination.balance += amount
        now = utc_now()
        source.updated_at = now
        destination.updated_at = now
        transaction = Transaction(type = TransactionType.TRANSFER ,amount = amount, destination_account_id = destination.id, source_account_id = source.id  ,status = TransactionStatus.COMPLETED, description = description)
        debit_entry = LedgerEntry(account_id = source.id, entry_type = EntryType.DEBIT, amount = amount, transaction_id = transaction.id)
        credit_entry = LedgerEntry(account_id = destination.id, entry_type = EntryType.CREDIT, amount = amount, transaction_id = transaction.id)

        return (transaction, [debit_entry, credit_entry])

    