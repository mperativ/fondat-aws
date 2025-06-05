"""Decorator helpers for Bedrock operations."""

from collections.abc import Callable
from typing import Any, TypeVar

from fondat.resource import operation as _operation
from fondat.security import Policy

T = TypeVar("T")


def operation(
    method: str,
    policies: Policy | Callable[[Any], Policy] | None = None,
) -> Callable[[T], T]:
    """
    Shorthand decorator for Fondat operations with method and policies.

    Args:
        method: The HTTP method for the operation
        policies: Optional security policies or callable that returns policies

    Returns:
        A decorator function that adds the operation metadata
    """
    def decorator(func: T) -> T:
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            actual_policies = policies(self) if callable(policies) else policies
            return _operation(method=method, policies=actual_policies)(func)(self, *args, **kwargs)
        return wrapper
    return decorator
