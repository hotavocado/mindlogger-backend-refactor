from pydantic import BaseModel


class SecretSettings(BaseModel):
    secret_key: str | None = None

    @property
    def key(self) -> bytes:
        if self.secret_key:
            return bytes.fromhex(self.secret_key)
        raise ValueError("Please specify SECRETS__SECRET_KEY variable")
