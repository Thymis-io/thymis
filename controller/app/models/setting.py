from typing import Type


class Setting:
    name: str
    type: Type
    default: object
    description: str
    example: str

    def __init__(
        self, name: str, type: Type, default: object, description: str, example: str
    ):
        self.name = name
        self.type = type
        self.default = default
        self.description = description
        self.example = example
