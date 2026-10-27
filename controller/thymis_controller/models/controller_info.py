from pydantic import BaseModel


class ControllerInfo(BaseModel):
    agent_access_url: str


__all__ = ["ControllerInfo"]
