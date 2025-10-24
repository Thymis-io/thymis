import pathlib
import typing
from abc import ABC
from dataclasses import dataclass
from io import StringIO
from typing import List, Literal, Optional, Tuple, Union

from pydantic import JsonValue
from thymis_controller import db_models, models
from thymis_controller.models.module import SettingTypes, ValueTypes
from thymis_controller.nix.templating import (
    convert_python_value_to_nix,
    format_nix_file,
)
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
    icon_dark: Optional[str] = None

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
            iconDark=self.icon_dark,
        )

    @property
    def type(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def write_nix(
        self,
        path: pathlib.Path,
        module_settings: "models.ModuleSettings",
        priority: int,
        project: Project,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+", encoding="utf-8") as f:
            f.write("{ pkgs, lib, inputs, config, ... }:\n")
            f.write("{\n")

            self.write_nix_settings(f, path, module_settings, priority, project)

            f.write("\n}\n")

        format_nix_file(str(path / filename))

    def write_nix_settings(
        self,
        f: StringIO,
        path: pathlib.Path,
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
            if my_attr.nix_attr_name is not None:
                f.write(
                    f"  {my_attr.nix_attr_name} = lib.mkOverride {priority} {convert_python_value_to_nix(value)};\n"
                )

    def register_secret_settings(
        self,
        module_settings: "models.ModuleSettings",
        project: Project,
    ) -> List[Tuple["SecretType", JsonValue]]:
        secret_settings = []
        for attr, value in module_settings.settings.items():
            try:
                my_attr = getattr(self, attr)
            except AttributeError:
                import traceback

                traceback.print_exc()
                print(f"Attribute {attr} not found in {self}")
                continue
            assert isinstance(my_attr, Setting)
            if isinstance(my_attr.type, ListType):
                self._register_secret_settings_list(
                    my_attr.type, value, project, secret_settings
                )
            elif isinstance(my_attr.type, SecretType):
                secret_settings.append((my_attr.type, value))
            else:
                pass
        return secret_settings

    def _register_secret_settings_list(
        self,
        setting: models.ListType,
        value: JsonValue,
        project: Project,
        secret_settings: List[Tuple["Setting", JsonValue]],
    ):
        for v in value:
            # list of objects, iterate over keys
            if isinstance(v, dict):
                for k, v in v.items():
                    try:
                        if isinstance(setting.settings[k].type, models.SecretType):
                            secret_settings.append((setting.settings[k].type, v))
                    except KeyError:
                        pass


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


@dataclass
class SecretType:
    allowed_types: List[db_models.SecretTypes]
    default_processing_type: db_models.SecretProcessingTypes
    default_save_to_image: bool

    on_device_path: Optional[str] = None
    on_device_owner: Optional[str] = None
    on_device_group: Optional[str] = None
    on_device_mode: Optional[str] = None

    def get_model(self, locale: str) -> models.SecretType:
        return models.SecretType(
            allowed_types=self.allowed_types,
            default_processing_type=self.default_processing_type,
            default_save_to_image=self.default_save_to_image,
        )


@dataclass
class ArtifactType:
    def get_model(self, locale: str) -> models.ArtifactType:
        return models.ArtifactType()


@dataclass
class TextAreaCodeType:
    language: Optional[str] = None

    def get_model(self, locale: str) -> models.TextAreaCodeType:
        return models.TextAreaCodeType(
            language=self.language,
        )


@dataclass
class SystemdTimerType:
    timer_type: Optional[Literal["realtime", "monotonic"]] = "realtime"
    on_boot_sec: Optional[str] = None
    on_unit_active_sec: Optional[str] = None
    accuracy_sec: Optional[str] = None
    on_calendar: Optional[list[str]] = None
    persistent: Optional[bool] = None
    randomized_delay_sec: Optional[str] = None

    def get_model(self, locale: str) -> models.SystemdTimerType:
        return models.SystemdTimerType(
            timer_type=self.timer_type,
            on_boot_sec=self.on_boot_sec,
            on_unit_active_sec=self.on_unit_active_sec,
            accuracy_sec=self.accuracy_sec,
            on_calendar=self.on_calendar,
            persistent=self.persistent,
            randomized_delay_sec=self.randomized_delay_sec,
        )


type SettingTypes = Union[
    ValueTypes,
    SelectOneType,
    ListType,
    SecretType,
    ArtifactType,
    TextAreaCodeType,
    SystemdTimerType,
]


def get_setting_type_model(setting: SettingTypes, locale: str) -> models.SettingTypes:
    if isinstance(setting, SelectOneType):
        return setting.get_model(locale)
    if isinstance(setting, ListType):
        return setting.get_model(locale)
    if isinstance(setting, SecretType):
        return setting.get_model(locale)
    if isinstance(setting, ArtifactType):
        return setting.get_model(locale)
    if isinstance(setting, TextAreaCodeType):
        return setting.get_model(locale)
    if isinstance(setting, SystemdTimerType):
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
    "ArtifactType",
    "SecretType",
    "TextAreaCodeType",
    "SystemdTimerType",
]
