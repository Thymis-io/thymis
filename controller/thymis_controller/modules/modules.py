import os
import typing
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from pydantic import JsonValue
from thymis_controller import models
from thymis_controller.models.module import SettingTypes, ValueTypes
from thymis_controller.nix import convert_python_value_to_nix, format_nix_file
from thymis_controller.project import Project


class HasLocalize(typing.Protocol):
    def localize(self, locale: str) -> str:
        ...


type Localizable = str | HasLocalize


def localize(locale: str, value: Optional[Localizable]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.localize(locale)


class Module(ABC):
    display_name: Localizable
    icon: Optional[str] = None

    def get_model(self, locale: str) -> models.Module:
        # collect all settings
        settings = {}
        for attr in dir(self):
            if not attr.startswith("_"):
                value = getattr(self, attr)
                if isinstance(value, Setting):
                    settings[attr] = value.get_model(locale)
        return models.Module(
            type=self.type,
            displayName=localize(locale, self.display_name),
            settings=settings,
            icon=self.icon,
        )

    @property
    def type(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: "models.ModuleSettings",
        priority: int,
        project: Project,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+", encoding="utf-8") as f:
            f.write("{ pkgs, lib, inputs, ... }:\n")
            f.write("{\n")

            self.write_nix_settings(f, module_settings, priority, project)

            f.write("}\n")

        format_nix_file(str(path / filename))

    def write_nix_settings(
        self,
        f,
        module_settings: "models.ModuleSettings",
        priority: int,
        project: Project,
    ):
        for attr, value in module_settings.settings.items():
            try:
                my_attr = getattr(self, attr)
            except AttributeError:
                import traceback

                traceback.print_exc()
                print(f"Attribute {attr} not found in {self}")
                continue
            assert isinstance(my_attr, Setting)
            if isinstance(my_attr.type, models.ListType):
                continue
            if my_attr.nix_attr_name is not None:
                f.write(
                    f"  {my_attr.nix_attr_name} = lib.mkOverride {priority} {convert_python_value_to_nix(value)};\n"
                )


class LocalizedString:
    def __init__(self, **kwargs):
        self.values = kwargs

    def localize(self, locale: str) -> str:
        return self.values.get(locale, self.values.get("en", ""))


@dataclass
class SelectOneType:
    select_one: List[Tuple[Localizable, str] | str]
    extra_data: Optional[dict[str, JsonValue]] = None

    def get_model(self, locale: str) -> models.SelectOneType:
        return models.SelectOneType(
            select_one=[
                (localize(locale, v[0]), v[1]) if isinstance(v, tuple) else (v, v)
                for v in self.select_one
            ],
            extra_data=self.extra_data,
        )


@dataclass
class ListType:
    settings: dict[str, "Setting"]
    element_name: Optional[Localizable]

    def get_model(self, locale: str) -> models.ListType:
        return models.ListType(
            settings={
                key: value.get_model(locale) for key, value in self.settings.items()
            },
            element_name=localize(locale, self.element_name),
        )


type SettingTypes = Union[ValueTypes, SelectOneType, ListType]


def get_setting_type_model(setting: SettingTypes, locale: str) -> models.SettingTypes:
    if isinstance(setting, SelectOneType):
        return setting.get_model(locale)
    if isinstance(setting, ListType):
        return setting.get_model(locale)
    return setting


@dataclass
class Setting:
    display_name: Localizable
    type: SettingTypes
    description: Optional[Localizable] = None
    default: Optional[JsonValue] = None
    example: Optional[str] = None
    order: int = 0

    nix_attr_name: Optional[str] = None

    def get_model(self, locale: str) -> models.Setting:
        return models.Setting(
            displayName=localize(locale, self.display_name),
            type=get_setting_type_model(self.type, locale),
            description=localize(locale, self.description),
            default=self.default,
            example=self.example,
            order=self.order,
        )


__all__ = [
    "Module",
    "Setting",
    "HasLocalize",
    "Localizable",
    "localize",
    "SelectOneType",
    "ListType",
    "SettingTypes",
    "LocalizedString",
]
