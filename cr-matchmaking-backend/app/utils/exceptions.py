from typing import Any


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class InsufficientBalance(AppException):
    def __init__(self, available: float, required: float):
        super().__init__(
            code="INSUFFICIENT_BALANCE",
            message="Insufficient balance",
            status_code=400,
            details={"available": available, "required": required},
        )


class AccountNotVerified(AppException):
    def __init__(self):
        super().__init__(
            code="ACCOUNT_NOT_VERIFIED",
            message="Clash Royale account not verified",
            status_code=403,
        )


class InvalidPlayerTag(AppException):
    def __init__(self, player_tag: str):
        super().__init__(
            code="INVALID_PLAYER_TAG",
            message="Player tag does not exist",
            status_code=404,
            details={"player_tag": player_tag},
        )


class MatchExpired(AppException):
    def __init__(self, match_id: str):
        super().__init__(
            code="MATCH_EXPIRED",
            message="Match has expired",
            status_code=410,
            details={"match_id": match_id},
        )


class VerificationFailed(AppException):
    def __init__(self, reason: str = ""):
        super().__init__(
            code="VERIFICATION_FAILED",
            message="Battle verification failed",
            status_code=400,
            details={"reason": reason} if reason else {},
        )


class PaymentFailed(AppException):
    def __init__(self, reason: str = ""):
        super().__init__(
            code="PAYMENT_FAILED",
            message="Payment processing failed",
            status_code=402,
            details={"reason": reason} if reason else {},
        )


class RateLimitExceeded(AppException):
    def __init__(self):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            status_code=429,
        )
