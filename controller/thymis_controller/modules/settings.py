import json
from pathlib import Path
from typing import Optional

from thymis_controller import models


class LocalizationProvider:
    locale_path: str

    def __init__(self, locale_path: str):
        self.locale_path = locale_path

    def flatten_dict(self, d, parent_key="", sep="."):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def load_locales(self, language: str):
        try:
            with open(self.locale_path / Path(f"{language}.json")) as f:
                locales = json.load(f)
            locales = self.flatten_dict(locales)
            return locales
        except:
            return {}


class LocalizeKey:
    key: str

    def __init__(self, key: str):
        self.key = key

    def localize(self, locales: dict):
        return locales.get(self.key, self.key)


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
