# Timestamp: 2025-10-27 02:51:16 UTC
# Hash: 2cb4de71ffaa9a6704f77ba0c12aa23809efff88d41b7ccb114415a8cbd482a5
"""
AxProtocol Authority Assertion Layer — OP_AUTH token management
Implements Operator Supremacy (D20) and CAM leases (D21).
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

SECRET = os.getenv("OP_AUTH_SECRET", "axp-secret-change-in-production")

def generate_op_token(
    operator_id: str,
    duration_minutes: int = 15,
    mode: Optional[str] = None
) -> str:
    """
    Generate OP_AUTH token (Directive 20).

    Args:
        operator_id: Unique operator identifier
        duration_minutes: Token TTL (default 15min)
        mode: Optional override mode (e.g., 'OOM' for Directive 25c)

    Returns:
        JWT token string
    """
    payload = {
        "operator_id": operator_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=duration_minutes),
        "mode": mode
    }

    return jwt.encode(payload, SECRET, algorithm="HS256")


def validate_op_token(token: str) -> dict:
    """
    Verify OP_AUTH token.

    Returns:
        dict with 'valid' (bool), 'operator_id', 'mode', or 'reason' if invalid
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return {
            "valid": True,
            "operator_id": payload["operator_id"],
            "mode": payload.get("mode"),
            "issued_at": payload.get("issued_at")
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "reason": "Token expired"}
    except jwt.InvalidTokenError as e:
        return {"valid": False, "reason": f"Invalid token: {e}"}


def require_op_auth(action: str) -> str:
    """
    Enforce OP_AUTH requirement for protected actions (Directive 20).
    Raises PermissionError if token missing or invalid.

    Returns:
        operator_id if valid
    """
    token = os.getenv("OP_AUTH_TOKEN")

    if not token:
        raise PermissionError(
            f"Action '{action}' requires OP_AUTH token. "
            "Set OP_AUTH_TOKEN environment variable."
        )

    validation = validate_op_token(token)

    if not validation["valid"]:
        raise PermissionError(
            f"OP_AUTH validation failed for '{action}': {validation['reason']}"
        )

    return validation["operator_id"]


class CAMLease:
    """
    Controlled Autonomy Mode lease manager (Directive 21).
    Enforces 3-minute or ACI ≥ 90 limits.
    """

    def __init__(self, duration_seconds: int = 180):
        self.start_time = datetime.now(timezone.utc)
        self.duration = duration_seconds
        self.aci_threshold = 90

    def is_expired(self, aci: Optional[float] = None) -> bool:
        """Check if CAM lease has expired."""
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        # Expire if time limit reached
        if elapsed >= self.duration:
            return True

        # Or if ACI threshold met
        if aci is not None and aci >= self.aci_threshold:
            return True

        return False

    def remaining_seconds(self) -> int:
        """Get remaining lease time."""
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return max(0, int(self.duration - elapsed))

    def extend(self, additional_seconds: int, op_auth_token: str):
        """Extend lease (requires OP_AUTH)."""
        validation = validate_op_token(op_auth_token)
        if not validation["valid"]:
            raise PermissionError(f"Cannot extend CAM lease: {validation['reason']}")

        self.duration += additional_seconds
        return self.duration


if __name__ == "__main__":
    # Test token generation
    token = generate_op_token("operator-001", duration_minutes=5)
    print(f"Generated token:\n{token}\n")

    # Validate
    result = validate_op_token(token)
    print(f"Validation: {result}\n")

    # Test CAM lease
    lease = CAMLease(duration_seconds=180)
    print(f"CAM lease expires in: {lease.remaining_seconds()}s")
    print(f"Expired? {lease.is_expired()}")