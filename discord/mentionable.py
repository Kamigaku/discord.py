from dataclasses import dataclass

from discord import Role, User

__all__ = ["Mentionable"]


@dataclass
class Mentionable:
    user: User = None
    role: Role = None

    @property
    def is_user(self):
        return self.user is not None

    @property
    def is_role(self):
        return self.role is not None
