# Derives the kiosk configuration from the settings of the Kiosk module.
#
# The settings are merged by the nix module system, this file only translates
# the merged values into NixOS configuration. See
# `nix/settings/networking.nix` for how the settings and their priorities are
# provided by the controller.
{ config, lib, pkgs, ... }:
let
  cfg = config.thymis.config.kiosk or { };
  priorities = config.thymis.priority.kiosk or { };
  enabled = priorities != { };
  priority =
    if enabled
    then lib.foldl' (a: b: if a < b then a else b) 1500 (lib.attrValues priorities)
    else 1500;

  url = cfg.url or "";
  xrandrMode = cfg.xrandr-mode or "1920x1080";
  rotation = cfg.xrandr-rotation or "normal";
  volume = cfg.volume or 100;
  audioSinkFuzzy = cfg.audio-sink-fuzzy or "";
  enableVnc = cfg.enable-vnc or false;
  vncPassword = cfg.vnc-password or "password";
  # changes whenever any kiosk setting changes, which restarts the display manager
  nonce = builtins.hashString "sha256" (builtins.toJSON cfg);

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
    CVT_OUT=$(${pkgs.libxcvt}/bin/cvt ${modeW} ${modeH} ${modeR})
    MODELINE=$(echo "$CVT_OUT" | grep -i modeline | sed 's/Modeline //')
    MODENAME=$(echo "$MODELINE" | cut -d'"' -f2)
    MODEPARAMS=$(echo "$MODELINE" | sed 's/"[^"]*" *//')
    # Register the modeline once per X session.
    ${pkgs.xorg.xrandr}/bin/xrandr --newmode "$MODENAME" $MODEPARAMS 2>/dev/null || true
    apply() {
        ${pkgs.xorg.xrandr}/bin/xrandr --addmode HDMI-1 "$MODENAME" 2>/dev/null || true
        ${pkgs.xorg.xrandr}/bin/xrandr --output HDMI-1 --rotate ${rotation} 2>/dev/null || true
        ${pkgs.xorg.xrandr}/bin/xrandr --output HDMI-1 --mode "$MODENAME" 2>/dev/null || true
    }
    apply
    # Reapply on every screen-change event (KVM switch, display power cycle).
    while IFS= read -r _; do
        sleep 1
        apply
    done < <(${pkgs.xorg.xev}/bin/xev -root -event randr | grep --line-buffered RRScreenChangeNotify)
  '';

  vncPasswordLine = lib.optionalString enableVnc ''exec ${pkgs.bash}/bin/bash -c "mkdir -p $HOME/tigervnc; ${pkgs.tigervnc}/bin/vncpasswd -f <<< \"${vncPassword}\" > $HOME/tigervnc/passwd"'';
  vncServerLine = lib.optionalString enableVnc ''exec ${pkgs.tigervnc}/bin/x0vncserver -display :0 -PasswordFile=$HOME/tigervnc/passwd'';
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
