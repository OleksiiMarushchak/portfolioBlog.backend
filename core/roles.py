from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    GOD = "god"
    CREATOR = "creator"


ROLE_LEVELS = {
    UserRole.USER: 0,
    UserRole.MODERATOR: 1,
    UserRole.ADMIN: 2,
    UserRole.GOD: 3,
    UserRole.CREATOR: 4,
}