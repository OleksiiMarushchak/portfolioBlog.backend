from pydantic import BaseModel,Field

from typing import Optional



class Auth(BaseModel):
    username: str = Field(max_length=33)
    password: str

class CreateUserWithToken(Auth):
    token: Optional[str] = None
