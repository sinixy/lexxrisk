from typing import Literal

from .enums import Role
from db import db


class User:

    def __init__(self, account_id: int, tg_id: int, name: str, role: Role):
        self._account_id = account_id
        self._tg_id = tg_id
        self._name = name
        self._role = role

    async def _update(self, col: str, val: str):
        await db.execute(f"UPDATE users SET {col} = ? WHERE account_id = ?", (val, self.account_id))
        await db.commit()

    @classmethod
    async def get(cls, id: int, by: Literal['account', 'tg'] = 'tg'):
        user = await db.fetchone(f'SELECT * FROM users WHERE {by}_id = ?', (id,))
        if not user: return None
        return cls(user[0], user[1], user[2], Role[user[3]])

    @classmethod
    async def create(cls):
        pass
    
    @classmethod
    def get_admins(cls):
        ids = [id[0] for id in db.execute("SELECT id FROM users WHERE role = ?", (Role.admin.value,))]
        return [cls.get(user_id) for user_id in ids]
    
    @property
    def account_id(self):
        return self._account_id
    
    @property
    def tg_id(self):
        return self._tg_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def role(self):
        return self._role
        