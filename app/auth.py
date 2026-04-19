import hashlib
import hmac
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        210000,
    )
    return f"{salt_value}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_value, digest_hex = stored_hash.split("$", 1)
    except ValueError:
        return False

    candidate = hash_password(password, salt=salt_value)
    return hmac.compare_digest(candidate, f"{salt_value}${digest_hex}")


def build_session_cookie_flags(app_env: str, session_https_only: bool) -> dict[str, bool | str]:
    secure = session_https_only
    same_site = "lax"
    return {
        "https_only": secure,
        "same_site": same_site,
    }
