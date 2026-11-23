class DomainError(Exception):
    code = 'DOMAIN_ERROR'
    
    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message

        if code is not None:
            self.code = code

        super().__init__(message)


class InvalidAmountError(DomainError):
    code = 'INVALID_AMOUNT'


class InactiveAccountError(DomainError):
    code = 'INACTIVE_ACCOUNT'


class SameAccountTransferError(DomainError):
    code = 'SAME_ACCOUNT_TRANSFER'
  

class CurrencyMismatchError(DomainError):
    code = 'CURRENCY_MISMATCH'


class InsufficientBalanceError(DomainError):
    code = 'INSUFFICIENT_BALANCE'
  

class IdempotencyConflictError(DomainError):
    code = 'IDEMPOTENCY_CONFLICT'
   
