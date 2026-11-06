# Derives the kiosk configuration from the settings of the Kiosk module.
#
# The settings are merged by the nix module system, this file only translates
# the merged values into NixOS configuration. See
# `nix/settings/networking.nix` for how the settings and their priorities are
# provided by the controller.
{ config, lib, pkgs, ... }:
let
  settings = import ../module-settings.nix { inherit config lib; };

  enabled = settings.used "kiosk";
  priority = settings.lowestPriority "kiosk";

  url = settings.value "kiosk" "url" "";
  xrandrMode = settings.value "kiosk" "xrandr-mode" "1920x1080";
  rotation = settings.value "kiosk" "xrandr-rotation" "normal";
  volume = settings.value "kiosk" "volume" 100;
  audioSinkFuzzy = settings.value "kiosk" "audio-sink-fuzzy" "";
  enableVnc = settings.value "kiosk" "enable-vnc" false;
  vncPassword = settings.value "kiosk" "vnc-password" "password";
  # changes whenever any kiosk setting changes, which restarts the display manager
  nonce = builtins.hashString "sha256" (builtins.toJSON (settings.settings "kiosk"));

  # Parse width/height/refresh from the xrandr mode for CVT modeline generation.
  # Handles "1360x768", "1360x768_60.00" and "1360x768@60".
  modeMatch = builtins.match "([0-9]+)x([0-9]+)([_@]([0-9]+(\\.[0-9]+)?))?" xrandrMode;
  modeW = if modeMatch == null then "1920" else builtins.elemAt modeMatch 0;
  modeH = if modeMatch == null then "1080" else builtins.elemAt modeMatch 1;
  modeR =
    if modeMatch == null || builtins.elemAt modeMatch 3 == null then "60"
    else builtins.toString (builtins.floor (builtins.fromJSON (builtins.elemAt modeMatch 3)));

  xrandrSetup = pkgs.writeShellScript "thymis-xrandr-setup" ''
    sleep 2

    XRANDR="${pkgs.xorg.xrandr}/bin/xrandr"
    XEV="${pkgs.xorg.xev}/bin/xev"
    SYSTEMCTL="${pkgs.systemd}/bin/systemctl"
    TARGET_MODE="${modeW}x${modeH}"

    # Only one watchdog per X session.
    mkdir -p "$HOME/.cache"
    exec 9>"$HOME/.cache/thymis-xrandr.lock"
    ${pkgs.util-linux}/bin/flock -n 9 || exit 0

    hdmi_section() {
        "$XRANDR" --query 2>/dev/null | sed -n '/^HDMI-1 connected/,/^[^[:space:]]/p'
    }

    # Prefer an EDID mode whose name is the requested resolution. A custom CVT
    # modeline is only needed when the monitor does not advertise the target:
    # setting a duplicate or stale modeline can fail with ENOENT on vc4, which
    # is what kept the display in a restart loop.
    if hdmi_section | grep -qE "^[[:space:]]+$TARGET_MODE([[:space:]]|$)"; then
        MODENAME="$TARGET_MODE"
    else
        CVT_OUT=$(${pkgs.libxcvt}/bin/cvt ${modeW} ${modeH} ${modeR})
        MODELINE=$(printf '%s\n' "$CVT_OUT" | grep -i modeline | sed 's/Modeline //')
        MODENAME=$(printf '%s' "$MODELINE" | cut -d'"' -f2)
        MODEPARAMS=$(printf '%s' "$MODELINE" | sed 's/"[^"]*" *//')
        "$XRANDR" --newmode "$MODENAME" $MODEPARAMS >/dev/null 2>&1 || true
    fi

    # The monitor's preferred EDID mode is the fail-safe: it always exists.
    preferred_mode() {
        hdmi_section | awk '
            $1 ~ /^[0-9]+x[0-9]+/ {
                if ($0 ~ /\+/) { print $1; found = 1; exit }
                if (!first) first = $1
            }
            END { if (!found && first) print first }
        '
    }

    output_connected() {
        "$XRANDR" --query 2>/dev/null | awk '
            $1 == "HDMI-1" { connected = ($2 == "connected") }
            END { exit !connected }'
    }

    # A working display has HDMI-1 connected, a CRTC mode assigned and the
    # framebuffer geometry matching that output. The mode name is not compared,
    # so the EDID fail-safe mode counts as healthy and a rejected custom
    # modeline cannot cause a restart loop.
    display_healthy() {
        QUERY=$("$XRANDR" --query 2>/dev/null) || return 1
        ACTIVE=$(printf '%s\n' "$QUERY" | awk '
            $1 == "HDMI-1" {
                if ($2 != "connected") exit 1
                for (i = 3; i <= NF; i++)
                    if ($i ~ /^[0-9]+x[0-9]+\+[0-9]+\+[0-9]+$/) {
                        print $i, $(i + 1)
                        exit 0
                    }
                exit 1
            }') || return 1
        set -- $ACTIVE
        [ "$#" -eq 2 ] || return 1
        GEOMETRY=$(printf '%s\n' "$QUERY" | sed -n '1s/.*current \([0-9]*\) x \([0-9]*\).*/\1x\2/p')
        # 320x200 is X's fallback when no mode could be set; no real display
        # mode uses it.
        [ "$GEOMETRY" != "320x200" ] || return 1
        [ "$GEOMETRY" = "$(echo "$1" | cut -d+ -f1)" ] || return 1
        [ "$2" = "${rotation}" ]
    }

    apply_mode() {
        MODE="$1"
        "$XRANDR" --addmode HDMI-1 "$MODE" >/dev/null 2>&1 || true
        # A failed modeset drops rotation as well, so set both again.
        "$XRANDR" --output HDMI-1 --rotate ${rotation} >/dev/null 2>&1 || true
        # Keep xrandr's error: a rejected mode is the only useful diagnostic.
        if ! ERR=$("$XRANDR" --output HDMI-1 --mode "$MODE" 2>&1 >/dev/null); then
            echo "thymis-xrandr-setup: setting $MODE failed: $ERR" >&2
        elif [ -n "$ERR" ]; then
            echo "thymis-xrandr-setup: setting $MODE: $ERR" >&2
        fi
    }

    # Fail safe, never restart forever:
    #  1. reapply the configured mode a few times (a failed modeset is often
    #     transient),
    #  2. fall back to the monitor's preferred EDID mode, which always exists,
    #  3. restart display-manager at most once per boot,
    #  4. after that stay on the fallback mode; never restart again, never
    #     reboot the device.
    RESTART_MARKER="''${THYMIS_XRANDR_RESTART_MARKER:-/tmp/thymis-xrandr-restarted-$(cat /proc/sys/kernel/random/boot_id)}"
    FAILURES=0
    CURRENT_MODE="$MODENAME"
    USING_FALLBACK=0

    check() {
        if display_healthy; then
            FAILURES=0
            return 0
        fi
        if ! output_connected; then
            # Nothing to recover while the display is off or unplugged; the next
            # screen-change event applies the configuration again.
            FAILURES=0
            return 0
        fi

        FAILURES=$((FAILURES + 1))

        if [ "$FAILURES" -le 3 ]; then
            echo "thymis-xrandr-setup: display unhealthy ($FAILURES/3), reapplying $CURRENT_MODE" >&2
            apply_mode "$CURRENT_MODE"
            return 0
        fi

        if [ "$USING_FALLBACK" -eq 0 ]; then
            FALLBACK_MODE=$(preferred_mode)
            if [ -n "$FALLBACK_MODE" ] && [ "$FALLBACK_MODE" != "$CURRENT_MODE" ]; then
                USING_FALLBACK=1
                CURRENT_MODE="$FALLBACK_MODE"
                FAILURES=0
                echo "thymis-xrandr-setup: falling back to native mode $CURRENT_MODE" >&2
                apply_mode "$CURRENT_MODE"
                return 0
            fi
        fi

        if [ ! -e "$RESTART_MARKER" ]; then
            : > "$RESTART_MARKER" 2>/dev/null || true
            echo "thymis-xrandr-setup: display did not recover, restarting display-manager once" >&2
            "$SYSTEMCTL" --no-block restart display-manager.service && exit 0
        fi

        echo "thymis-xrandr-setup: display still unhealthy, staying on $CURRENT_MODE (fail-safe)" >&2
        apply_mode "$CURRENT_MODE"
    }

    # Apply the configured mode once; the health check below only recovers.
    apply_mode "$CURRENT_MODE"
    check
    # Reapply on screen-change events (KVM switch, display power cycle) and poll
    # every 30 seconds, so a wedged output is recovered even without an event.
    while true; do
        if IFS= read -r -t 30 _; then
            sleep 1
            check
        elif [ $? -gt 128 ]; then
            check
        else
            sleep 30
            check
        fi
    done < <("$XEV" -root -event randr | grep --line-buffered RRScreenChangeNotify)
  '';

  vncPasswordLine = lib.optionalString enableVnc ''exec ${pkgs.bash}/bin/bash -c "mkdir -p $HOME/tigervnc; ${pkgs.tigervnc}/bin/vncpasswd -f <<< \"${vncPassword}\" > $HOME/tigervnc/passwd"'';
  vncServerLine = lib.optionalString enableVnc ''exec ${pkgs.tigervnc}/bin/x0vncserver -display :0 -PasswordFile=$HOME/tigervnc/passwd -AcceptSetDesktopSize=1'';
  audioSinkLine = lib.optionalString (audioSinkFuzzy != "") ''exec "${pkgs.pulseaudio}/bin/pactl set-default-sink ''$(${pkgs.pulseaudio}/bin/pactl list short sinks | grep -m1 -i '${audioSinkFuzzy}' | cut -f1)"'';
in
{
  config = {
    services.xserver.enable = lib.mkIf enabled (lib.mkOverride priority true);
    services.displayManager.sddm.enable = lib.mkIf enabled (lib.mkOverride priority true);
    services.displayManager.autoLogin.enable = lib.mkIf enabled (lib.mkOverride priority true);
    services.displayManager.autoLogin.user = lib.mkIf enabled (lib.mkOverride priority "thymiskiosk");
    users.users.thymiskiosk = lib.mkIf enabled (lib.mkOverride priority {
      isNormalUser = true;
      createHome = true;
    });
    # The kiosk session restarts the display manager itself when its X modeset
    # state got wedged (see the xrandr watchdog in the i3 configuration), which
    # polkit otherwise forbids for an unprivileged user. `mkAfter` merges this
    # rule with other polkit rules instead of replacing them.
    security.polkit.extraConfig = lib.mkIf enabled (lib.mkAfter ''
      polkit.addRule(function(action, subject) {
        var unit = action.lookup("unit");
        if (action.id == "org.freedesktop.systemd1.manage-units" &&
            subject.user == "thymiskiosk" &&
            (unit == "display-manager.service" || unit == "sddm.service") &&
            action.lookup("verb") == "restart") {
          return polkit.Result.YES;
        }
      });
    '');
    services.pipewire.enable = lib.mkIf enabled (lib.mkOverride priority false);
    # `hardware.pulseaudio.*` is an alias of `services.pulseaudio.*`; aliases cannot carry
    # `mkIf`/`mkOverride` markers, so the new option names are written directly
    services.pulseaudio.enable = lib.mkIf enabled (lib.mkOverride priority true);
    services.pulseaudio.support32Bit = lib.mkIf enabled (lib.mkOverride priority true);
    services.xserver.windowManager.i3.enable = lib.mkIf enabled (lib.mkOverride priority true);
    services.xserver.windowManager.i3.configFile = lib.mkIf enabled (lib.mkOverride priority (
      pkgs.writeText "i3-config" ''
        # i3 config file (v4)
        bar {
            mode invisible
        }
        new_window pixel 0
        new_float pixel 0
        exec "${xrandrSetup}"
        exec "/run/current-system/sw/bin/xset s off"
        exec "/run/current-system/sw/bin/xset -dpms"
        exec "${pkgs.unclutter}/bin/unclutter"
        exec ${pkgs.bash}/bin/bash -c "                ${pkgs.killall}/bin/killall chromium;                 rm -rf ~/.config/chromium/Singleton*;                 mkdir -p ~/.config/chromium/Default;                 [ -s ~/.config/chromium/Default/Preferences ] || echo \\"{}\\" > ~/.config/chromium/Default/Preferences;                 ${pkgs.jq}/bin/jq '.translate_blocked_languages = ((.translate_blocked_languages // []) + [\\"de\\"] | unique)' ~/.config/chromium/Default/Preferences > tmp.json &&                 mv tmp.json ~/.config/chromium/Default/Preferences;                 ${pkgs.ungoogled-chromium}/bin/chromium --app='data:text/html,<html><body><h1>Loading...</h1></body></html>' &                 sleep 30;                 ${pkgs.killall}/bin/killall chromium;                 sleep 3;                 while ! ${pkgs.curl}/bin/curl --fail --silent --max-time 10 --head '${url}'; do                 sleep 3;                 done;                 sleep 1;                 ${pkgs.ungoogled-chromium}/bin/chromium --app='${url}'                 ${if (pkgs.stdenv.system == "aarch64-linux") then "--disable-gpu" else ""}                 --disable-features=Translate --hide-scrollbars;"

        ${vncPasswordLine}
        ${vncServerLine}
        exec "${pkgs.pamixer}/bin/pamixer --set-volume ${builtins.toString volume}"
        ${audioSinkLine}
      ''
    ));
    systemd.services.display-manager.restartIfChanged = lib.mkIf enabled (lib.mkOverride priority true);
    systemd.services.display-manager.environment.NONCE = lib.mkIf enabled (lib.mkOverride priority nonce);
    system.activationScripts.restart-display-manager-thymis = lib.mkIf enabled {
      supportsDryActivation = true;
      text = ''
        mkdir -p /run/nixos
        if [ "$NIXOS_ACTION" != dry-activate ]; then
            echo display-manager.service > /run/nixos/activation-restart-list
        else
            echo display-manager.service > /run/nixos/dry-activation-restart-list
        fi
      '';
    };
  };
}
