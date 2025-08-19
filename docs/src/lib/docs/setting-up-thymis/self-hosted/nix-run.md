# Using nix run

You can run the Thymis Controller directly with Nix, without installing NixOS or using Docker.

```bash
nix run github:Thymis-io/thymis/v0.6#thymis-controller
```

This starts the controller binary from the pinned release.

Configuration is done via the same environment variables as in the
[OCI‑Container setup](oci-container.md):

- THYMIS_BASE_URL
- THYMIS_AGENT_ACCESS_URL
- THYMIS_PROJECT_PATH
- THYMIS_AUTH_BASIC
- THYMIS_AUTH_BASIC_USERNAME
- THYMIS_AUTH_BASIC_PASSWORD_FILE
- UVICORN_HOST
- UVICORN_PORT

Example:

```bash
THYMIS_BASE_URL=https://your-domain.example \
THYMIS_AGENT_ACCESS_URL=https://your-domain.example \
THYMIS_PROJECT_PATH=/var/lib/thymis \
UVICORN_HOST=0.0.0.0 \
UVICORN_PORT=8000 \
mkdir -p /var/lib/thymis && \
nix run github:Thymis-io/thymis/v0.6#thymis-controller
```

Notes:
- Runs the same app as the container, but builds execute natively on your host.
- Ensure `THYMIS_PROJECT_PATH` exists and is writable (e.g., `/var/lib/thymis`).
- For public exposure and TLS, put a reverse proxy in front of the process.
