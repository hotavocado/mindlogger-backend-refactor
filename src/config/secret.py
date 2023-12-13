from pydantic import BaseModel


class SecretSettings(BaseModel):
    key_length: int = 32
    secret_key: str | None = None
    # It is used only in old alembic migrations and old migration scripts.
    # possible can be removed later
    secret_iv: str | None = None

    @property
    def key(self) -> bytes:
        if self.secret_key:
            return bytes.fromhex(self.secret_key)
        return b"\x0e\xb7\xf5\xd4\xc16q\x99\xc2\x1e\x9a.\xc7\x93\xb5\xa4\x81\xb6\x0f\xe2\xaf$FK\xcb\x18\xac\x7f\xa4\x8ad_"  # noqa: E501

    @property
    def iv(self) -> bytes:
        if self.secret_iv:
            return bytes.fromhex(self.secret_iv)
        return b'\xdb\x8b\xa5Z\x14\xe4\xe0`el\x07\x1deaX"'
