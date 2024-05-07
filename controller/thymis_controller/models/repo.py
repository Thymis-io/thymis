from typing import List
from pydantic import BaseModel


class Repo(BaseModel):
    url: str
