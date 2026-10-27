{ pkgs, thymis-agent }:
pkgs.dockerTools.buildLayeredImage {
  name = "thymis-agent";
  tag = "latest";
  contents = [
    pkgs.dockerTools.binSh # the agent shells out via os.system
    pkgs.dockerTools.caCertificates
    pkgs.dockerTools.fakeNss # root user for chown and chpasswd
    pkgs.coreutils
  ];
  extraCommands = ''
    mkdir -m 1777 tmp
  '';
  config = {
    Entrypoint = [ "${thymis-agent}/bin/thymis-agent" ];
    Env = [
      "PATH=/bin"
      "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
    ];
  };
}
