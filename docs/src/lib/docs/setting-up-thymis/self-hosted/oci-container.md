# OCI-Container / Docker

Run the Thymis Controller in a Docker/OCI container on x86_64 hosts.

Important: The container can build and serve x86_64 (x64) device configurations only. Raspberry Pi/ARM (aarch64) image builds are not supported from the container.

## Image

- [ghcr.io/thymis-io/thymis-controller:latest](https://ghcr.io/thymis-io/thymis-controller)

## Quick start

```bash
docker run -d \
  --name thymis-controller \
  -p 8000:8000 \
  -e UVICORN_HOST=0.0.0.0 \
  -e THYMIS_BASE_URL=https://your-domain.example \
  -e THYMIS_AGENT_ACCESS_URL=https://your-domain.example \
  -v /var/lib/thymis:/var/lib/thymis \
  --restart unless-stopped \
  ghcr.io/thymis-io/thymis-controller:latest
```

Access the UI at: http://<host-ip>:8000 (or behind your HTTPS proxy).

## Persistent state

Mount host storage to keep the repo, DB, images, and keys:
- `-v /var/lib/thymis:/var/lib/thymis`

Ensure the directory is writable by the container.

## Configuration (env vars)

NixOS module defaults do not apply in Docker — pass what you need explicitly:
- THYMIS_BASE_URL — public URL for users/UI (e.g. `https://thymis.example.com`).
- THYMIS_AGENT_ACCESS_URL — URL devices use to connect (often same as BASE_URL).
- THYMIS_PROJECT_PATH — data dir in container (use `/var/lib/thymis`).
- THYMIS_AUTH_BASIC — `true|false` to enable/disable built‑in basic auth.
- THYMIS_AUTH_BASIC_USERNAME — username for basic auth (if enabled).
- THYMIS_AUTH_BASIC_PASSWORD_FILE — path in container to a password file; mount it.
- UVICORN_HOST — bind address; use `0.0.0.0` in containers.
- UVICORN_PORT — internal port (default 8000); map a host port accordingly.

Example with basic auth:
```bash
-e THYMIS_AUTH_BASIC=true \
-e THYMIS_AUTH_BASIC_USERNAME=admin \
-e THYMIS_AUTH_BASIC_PASSWORD_FILE=/var/lib/thymis/auth-basic-password \
```

## Reverse proxy (optional)

For public exposure and TLS, terminate HTTPS on your existing reverse proxy (Nginx/Traefik) and forward to the container on port 8000.

## Limitations

- x86_64 builds only; no Raspberry Pi/ARM builds from the container.
- For ARM targets use the NixOS-based setup instead.

## Troubleshooting

- View logs: `docker logs -f thymis-controller`
- Verify `/var/lib/thymis` is mounted and writable
- If a build targets non‑x86, switch to the NixOS install

## Containers on devices

If your goal is to run Docker/OCI containers on the devices managed by Thymis (not to containerize the Controller itself), use the built‑in [OCI‑Containers module](../../external-projects/thymis-modules.md#oci-containers). This page only covers running the Controller in a container.

## See also

- [NixOS self‑hosting](nixOS.md)
- [OCI‑Containers module (containers on devices)](../../external-projects/thymis-modules.md#oci-containers)
- [Administration](../../reference/administration.md)
