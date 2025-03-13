from pydantic import BaseModel


class Folder(BaseModel):
    type: str = "folder"
    name: str
    path: str
    children: list["Folder | File"] = []


class File(BaseModel):
    type: str = "file"
    name: str
    path: str
