import asyncio
from dataclasses import dataclass

from pwdlib import PasswordHash


@dataclass
class Utils:
    password_hash = PasswordHash.recommended()

    async def get_password_hash(self, password: str) -> str:
        return await asyncio.to_thread(self.password_hash.hash, password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return await asyncio.to_thread(
            self.password_hash.verify,
            plain_password,
            hashed_password,
        )
