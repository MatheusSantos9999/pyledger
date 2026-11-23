import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from domain.entities import Account
from domain.enums import AccountStatus, EntryType, TransactionStatus, TransactionType
from domain.exceptions import (
    CurrencyMismatchError,
    DomainError,
    InactiveAccountError,
    InsufficientBalanceError,
    InvalidAmountError,
    SameAccountTransferError,
)
from domain.services import deposit, transfer, validate_amount


class TestDomainServices(unittest.TestCase):
    def test_validate_amount_normalizes_two_decimals(self) -> None:
        self.assertEqual(validate_amount(Decimal("10")), Decimal("10.00"))
        self.assertEqual(validate_amount(Decimal("10.5")), Decimal("10.50"))
        self.assertEqual(validate_amount(Decimal("10.55")), Decimal("10.55"))

    def test_validate_amount_rejects_non_decimal_types(self) -> None:
        for invalid in [10.5, 10, "10.00", None]:
            with self.assertRaises(InvalidAmountError):
                validate_amount(invalid)  # type: ignore[arg-type]

    def test_validate_amount_rejects_zero_and_negative(self) -> None:
        for invalid in [Decimal("0"), Decimal("0.00"), Decimal("-0.01"), Decimal("-100")]:
            with self.assertRaises(InvalidAmountError):
                validate_amount(invalid)

    def test_validate_amount_rejects_nan_and_infinity(self) -> None:
        for invalid in [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")]:
            with self.assertRaises(InvalidAmountError):
                validate_amount(invalid)

    def test_validate_amount_rejects_more_than_two_decimals(self) -> None:
        with self.assertRaises(InvalidAmountError):
            validate_amount(Decimal("10.123"))

    def test_deposit_success(self) -> None:
        acc = Account(id=1, user_id=1)
        tx, entries = deposit(acc, Decimal("100"), description="Deposito inicial")

        self.assertEqual(acc.balance, Decimal("100.00"))
        self.assertEqual(tx.type, TransactionType.DEPOSIT)
        self.assertEqual(tx.status, TransactionStatus.COMPLETED)
        self.assertIsNone(tx.source_account_id)
        self.assertEqual(tx.destination_account_id, 1)
        self.assertEqual(tx.amount, Decimal("100.00"))
        self.assertEqual(tx.description, "Deposito inicial")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].account_id, 1)
        self.assertEqual(entries[0].entry_type, EntryType.CREDIT)
        self.assertEqual(entries[0].amount, Decimal("100.00"))

    def test_deposit_rejects_inactive_accounts_without_mutating_balance(self) -> None:
        for status in [AccountStatus.BLOCKED, AccountStatus.CLOSED]:
            acc = Account(id=1, user_id=1, status=status, balance=Decimal("50.00"))
            with self.assertRaises(InactiveAccountError):
                deposit(acc, Decimal("10.00"))
            self.assertEqual(acc.balance, Decimal("50.00"))

    def test_transfer_success(self) -> None:
        source = Account(id=1, user_id=1, balance=Decimal("100.00"))
        dest = Account(id=2, user_id=2, balance=Decimal("10.00"))

        tx, entries = transfer(source, dest, Decimal("40.50"), description="Pagamento")

        self.assertEqual(source.balance, Decimal("59.50"))
        self.assertEqual(dest.balance, Decimal("50.50"))
        self.assertEqual(source.updated_at, dest.updated_at)

        self.assertEqual(tx.type, TransactionType.TRANSFER)
        self.assertEqual(tx.status, TransactionStatus.COMPLETED)
        self.assertEqual(tx.source_account_id, 1)
        self.assertEqual(tx.destination_account_id, 2)
        self.assertEqual(tx.amount, Decimal("40.50"))

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].account_id, 1)
        self.assertEqual(entries[0].entry_type, EntryType.DEBIT)
        self.assertEqual(entries[0].amount, Decimal("40.50"))
        self.assertEqual(entries[1].account_id, 2)
        self.assertEqual(entries[1].entry_type, EntryType.CREDIT)
        self.assertEqual(entries[1].amount, Decimal("40.50"))

    def test_transfer_exact_full_balance_leaves_zero(self) -> None:
        source = Account(id=1, user_id=1, balance=Decimal("100.00"))
        dest = Account(id=2, user_id=2, balance=Decimal("0.00"))

        transfer(source, dest, Decimal("100.00"))

        self.assertEqual(source.balance, Decimal("0.00"))
        self.assertEqual(dest.balance, Decimal("100.00"))

    def test_transfer_same_account_rejected(self) -> None:
        acc = Account(id=1, user_id=1, balance=Decimal("100.00"))
        with self.assertRaises(SameAccountTransferError):
            transfer(acc, acc, Decimal("10.00"))
        self.assertEqual(acc.balance, Decimal("100.00"))

    def test_transfer_rejects_inactive_source_or_destination(self) -> None:
        active = Account(id=1, user_id=1, balance=Decimal("100.00"))
        blocked = Account(id=2, user_id=2, status=AccountStatus.BLOCKED, balance=Decimal("100.00"))

        with self.assertRaises(InactiveAccountError):
            transfer(blocked, active, Decimal("10.00"))
        with self.assertRaises(InactiveAccountError):
            transfer(active, blocked, Decimal("10.00"))

        self.assertEqual(active.balance, Decimal("100.00"))
        self.assertEqual(blocked.balance, Decimal("100.00"))

    def test_transfer_currency_mismatch_rejected(self) -> None:
        brl = Account(id=1, user_id=1, currency="BRL", balance=Decimal("100.00"))
        usd = Account(id=2, user_id=2, currency="USD", balance=Decimal("100.00"))

        with self.assertRaises(CurrencyMismatchError):
            transfer(brl, usd, Decimal("10.00"))

        self.assertEqual(brl.balance, Decimal("100.00"))
        self.assertEqual(usd.balance, Decimal("100.00"))

    def test_transfer_insufficient_balance_is_atomic(self) -> None:
        source = Account(id=1, user_id=1, balance=Decimal("100.00"))
        dest = Account(id=2, user_id=2, balance=Decimal("20.00"))

        with self.assertRaises(InsufficientBalanceError) as ctx:
            transfer(source, dest, Decimal("100.01"))

        self.assertIsInstance(ctx.exception, DomainError)
        self.assertEqual(ctx.exception.code, "INSUFFICIENT_BALANCE")
        self.assertEqual(source.balance, Decimal("100.00"))
        self.assertEqual(dest.balance, Decimal("20.00"))

    def test_ledger_entry_is_immutable(self) -> None:
        acc = Account(id=1, user_id=1)
        _, entries = deposit(acc, Decimal("10.00"))

        with self.assertRaises(FrozenInstanceError):
            entries[0].amount = Decimal("999.00")  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()