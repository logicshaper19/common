"""
Business Logic Exceptions

Custom exceptions for business logic layer to clearly separate
business rule violations from technical errors.
"""


class BusinessLogicError(Exception):
    """Raised when business rules are violated."""
    pass


class ValidationError(BusinessLogicError):
    """Raised when business validation fails."""
    pass


class AuthorizationError(BusinessLogicError):
    """Raised when business authorization rules are violated."""
    pass


class StateTransitionError(BusinessLogicError):
    """Raised when invalid state transitions are attempted."""
    pass
