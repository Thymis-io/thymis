from typing import Optional

from pydantic import BaseModel


class AuthMethods(BaseModel):
    basic: bool
    oauth2: bool


class UserInfo(BaseModel):
    username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
