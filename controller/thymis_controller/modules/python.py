import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import generate_timer_settings
from thymis_controller.project import Project


class PythonModule(modules.Module):
    display_name: str = "Python Module"

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding_dark.svg")
    )

    timer_config = modules.Setting(
        display_name=modules.LocalizedString(
            en="Timer Configuration",
            de="Timer Konfiguration",
        ),
        type=modules.SystemdTimerType(),
        default=None,
        description=modules.LocalizedString(
            en="The timer configuration for the Python script.",
            de="Die Timer-Konfiguration für das Python-Skript.",
        ),
        example="",
        order=10,
    )

    python_packages = modules.Setting(
        display_name=modules.LocalizedString(
            en="Python Packages",
            de="Python-Pakete",
        ),
        type=modules.ListType(
            settings={
                "package": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Python Package",
                        de="Python-Paket",
                    ),
                    type="string",
                    order=0,
                )
            },
            element_name=modules.LocalizedString(
                en="Python Package",
                de="Python-Paket",
            ),
        ),
        default=[],
        description=modules.LocalizedString(
            en="List of Python packages from python3Packages (e.g., requests, numpy, pandas)",
            de="Liste der Python-Pakete aus python3Packages (z.B. requests, numpy, pandas)",
        ),
        order=20,
    )

    system_packages = modules.Setting(
        display_name=modules.LocalizedString(
            en="System Packages",
            de="System-Pakete",
        ),
        type=modules.ListType(
            settings={
                "package": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="System Package",
                        de="System-Paket",
                    ),
                    type="string",
                    order=0,
                )
            },
            element_name=modules.LocalizedString(
                en="System Package",
                de="System-Paket",
            ),
        ),
        default=[],
        description=modules.LocalizedString(
            en="List of system packages from nixpkgs (e.g., git, curl, ffmpeg)",
            de="Liste der System-Pakete aus nixpkgs (z.B. git, curl, ffmpeg)",
        ),
        order=30,
    )

    script = modules.Setting(
        display_name=modules.LocalizedString(
            en="Python Script",
            de="Python-Skript",
        ),
        type=modules.TextAreaCodeType(
            language="python",
        ),
        default="",
        description=modules.LocalizedString(
            en="The Python script to be executed.",
            de="Das auszuführende Python-Skript.",
        ),
        example="",
        order=40,
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        # unique-enough service name, based on the config/tag type + name
        service_name = "thymis-python-service-" + (
            str(path.relative_to(project.path / "repository"))
            .replace("/", "-")
            .replace(".", "-")
        )

        python_script = module_settings.settings.get(
            "script", self.script.default
        ).strip()

        timer_config_raw = module_settings.settings.get(
            "timer_config", self.timer_config.default
        )
        if timer_config_raw is not None:
            timer_config = models.SystemdTimerType.model_validate(timer_config_raw)
            timer_settings = generate_timer_settings(timer_config)
        else:
            timer_settings = []

        python_packages_list = module_settings.settings.get(
            "python_packages", self.python_packages.default
        )
        system_packages_list = module_settings.settings.get(
            "system_packages", self.system_packages.default
        )

        # Build Python packages list
        python_packages = [
            f"pkgs.python3Packages.{entry['package']}"
            for entry in python_packages_list
            if "package" in entry and entry["package"].strip()
        ]

        # Build system packages list
        system_packages = [
            (
                f"pkgs.{entry['package']}"
                if not entry["package"].startswith("pkgs.")
                else entry["package"]
            )
            for entry in system_packages_list
            if "package" in entry and entry["package"].strip()
        ]

        f.write(
            f"""
            systemd.services."{service_name}" = let
              pythonScript = pkgs.writers.writePython3 "{service_name}-script" {{
                libraries = [ {" ".join(python_packages)} ];
              }} ''
{python_script}
              '';
            in {{
              serviceConfig = {{
                ExecStart = "${{pythonScript}}";
                Type = "oneshot";
              }};
              path = [ {" ".join(system_packages)} ];
            }};
            systemd.timers."{service_name}" = {{
              wantedBy = [ "timers.target" ];
              {"\n    ".join(timer_settings)}
            }};
            """.strip()
        )
