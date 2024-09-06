from typing import Optional

from thymis_controller import models


class Setting:
    name: str | LocalizeKey
    description: str | LocalizeKey
    nix_attr_name: Optional[str]
    example: str | LocalizeKey | None
    order: int = 0
    type: str

    def __init__(
        self,
        name: str | LocalizeKey,
        description: str | LocalizeKey,
        nix_attr_name: str,
        example: str | None = None,
        order: int = 0,
    ):
        self.name = name
        self.nix_attr_name = nix_attr_name
        self.description = description
        self.example = example
        self.order = order

    def get_model(self) -> models.Setting:
        return models.Setting(
            name=self.name,
            description=self.description,
            example=self.example,
            type="string",
            default="",
            order=self.order,
        )
