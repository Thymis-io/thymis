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
    string_can_be_identifier_for_attrs_key,
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


# Priority values that are not configured by anyone explicitly are written with.
# It is the priority `lib.mkOptionDefault` uses, so a value that one source
# explicitly configures always wins over the default another source fills in.
DEFAULT_PRIORITY = 1500


def is_unset_setting_value(value: JsonValue, nested: bool = False) -> bool:
    """A setting value counts as unset when it carries no information.

    Empty lists and empty attribute sets mean "not configured" for the same
    reason a missing key does: nothing must be defined for them in nix, so that
    other sources and the shipped defaults can win. `False` and `0` are real
    values.

    A whole setting that a source sets to an empty string counts as set (that is
    how a tag's value is cleared for one configuration), while an empty field
    inside a list element is the empty template of that element and must not
    shadow the value another source sets for the same field (`nested`).
    """
    if value is None or value == [] or value == {}:
        return True
    return nested and value == ""


def nix_attr_path(path: List[str]) -> str:
    """Render an attribute path, quoting segments that are not identifiers."""
    return ".".join(
        (
            segment
            if string_can_be_identifier_for_attrs_key(segment)
            else convert_python_value_to_nix(segment)
        )
        for segment in path
    )


def write_nix_definitions(
    f: StringIO,
    path: List[str],
    value: JsonValue,
    priority: int,
    element_key: Optional[str] = None,
    nested: bool = False,
):
    """Write the nix definitions of one setting value.

    A setting value is written as one `lib.mkOverride <priority>` definition per
    leaf, so that nix merges the fields of settings coming from different
    sources (device configuration, tags) individually instead of replacing whole
    subtrees, and resolves a leaf defined by several sources by priority.

    Lists whose elements are identified by a setting (`element_key`) are written
    as one definition tree per element, keyed by that identity, so that elements
    defined by different sources are merged by nix as well.
    """
    if element_key is not None and isinstance(value, list):
        for element in value:
            if not isinstance(element, dict):
                continue
            key = element.get(element_key)
            if not isinstance(key, str) or is_unset_setting_value(key, nested=True):
                continue
            write_nix_definitions(
                f,
                path + [key],
                {k: v for k, v in element.items() if k != element_key},
                priority,
                nested=True,
            )
        return

    if isinstance(value, dict):
        for key in sorted(value.keys()):
            if is_unset_setting_value(value[key], nested=True):
                continue
            write_nix_definitions(f, path + [key], value[key], priority, nested=True)
        return

    if is_unset_setting_value(value, nested=nested):
        return

    f.write(
        f"  {nix_attr_path(path)} = lib.mkOverride {priority} "
        f"{convert_python_value_to_nix(value)};\n"
    )


class Module(ABC):
    display_name: Localizable
    description: Optional[Localizable] = None
    category: Optional[Localizable] = None
    icon: Optional[str] = None
    icon_dark: Optional[str] = None

    # Namespace of this module's settings in the generated nix, e.g.
    # "networking" for `thymis.config.networking.*`. Modules that set it also
    # publish the priority their settings are written with as
    # `thymis.priority.<namespace>.<setting>`, which the nix side uses to derive
    # NixOS configuration from the merged settings.
    settings_namespace: Optional[str] = None

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
            description=localize(locale, self.description),
            category=localize(locale, self.category),
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

    def iter_settings(self) -> dict[str, "Setting"]:
        """All settings of this module, in a stable order.

        Named `iter_settings` because a module may declare a setting called
        `settings` (the Custom Nix module does).
        """
        return {
            attr: value
            for attr in dir(self)
            if not attr.startswith("_")
            and isinstance(value := getattr(self, attr), Setting)
        }

    def write_nix_settings(
        self,
        f: StringIO,
        path: pathlib.Path,
        module_settings: "models.ModuleSettings",
        priority: int,
        project: Project,
    ):
        """Write one `lib.mkOverride` definition per setting into `thymis.config`.

        A setting that a source does not configure is written with its default
        and `DEFAULT_PRIORITY`, so that the value another source explicitly
        configures wins; a setting nobody configures still gets the default.
        """
        for attr, setting in self.iter_settings().items():
            if self.settings_namespace is not None:
                # Presence and priority of the setting, see `settings_namespace`.
                # Named like the setting in `thymis.config` (the last component of
                # its `nix_attr_name`), so that the nix side can read the value
                # and the priority of a setting with the same name. Written even
                # when the setting itself is unset, so that the nix side can tell
                # which settings a module instance provides.
                name = (
                    setting.nix_attr_name.rsplit(".", 1)[-1]
                    if setting.nix_attr_name is not None
                    else attr
                )
                f.write(
                    f"  {nix_attr_path(['thymis', 'priority', self.settings_namespace, name])} = "
                    f"lib.mkOverride {priority} {priority};\n"
                )
            if setting.nix_attr_name is None:
                continue
            if attr in module_settings.settings:
                # set by this source: written even when empty, which is how a
                # configuration clears the value a tag sets
                value, value_priority = module_settings.settings[attr], priority
                if is_unset_setting_value(value):
                    continue
            else:
                # not set by this source: written as a default that loses
                # against the value another source sets, and empty defaults
                # (which carry no information) are left out entirely
                value, value_priority = setting.default, DEFAULT_PRIORITY
                if is_unset_setting_value(value, nested=True):
                    continue
            write_nix_definitions(
                f,
                setting.nix_attr_name.split("."),
                value,
                value_priority,
                element_key=(
                    setting.type.element_key
                    if isinstance(setting.type, ListType)
                    else None
                ),
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
    # Name of the setting inside `settings` that identifies an element, e.g.
    # "interface" for a list of static networks or "container_name" for a list of
    # OCI containers. Elements of such a list are written to nix as separate
    # definitions under `"<identity value>"`, so that the nix module system can
    # merge elements and their fields coming from different sources (device
    # configuration, tags) instead of one source replacing the whole list.
    element_key: Optional[str] = None

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
    timer_type: Optional[Literal["realtime", "monotonic", "continuous"]] = "realtime"
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
    "DEFAULT_PRIORITY",
    "is_unset_setting_value",
    "nix_attr_path",
    "write_nix_definitions",
    "SelectOneType",
    "ListType",
    "SettingTypes",
    "LocalizedString",
    "ArtifactType",
    "SecretType",
    "TextAreaCodeType",
    "SystemdTimerType",
]
