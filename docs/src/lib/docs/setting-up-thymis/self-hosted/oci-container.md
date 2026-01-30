# OCI-Container / Docker

Run the Thymis Controller in a Docker/OCI container.

Important:
- The standard `latest` image builds for **x86_64** only.
- To build **Raspberry Pi / ARM (aarch64)** images, you must use the **ARM64** container variant (`:latest-arm64`).
  - On x86 hosts, this requires QEMU user emulation (see below).

If you already use Nix, you can also run the Controller with [`nix run`](nix-run.md).

## Image

- x86_64: `ghcr.io/thymis-io/thymis-controller:latest`
- ARM64: `ghcr.io/thymis-io/thymis-controller:latest-arm64`

[View all tags on GitHub Container Registry](https://ghcr.io/thymis-io/thymis-controller)

## Quick start

```bash
docker run -d \
  --name thymis-controller \
  -p 8000:8000 \
  -e UVICORN_HOST=0.0.0.0 \
  -e THYMIS_BASE_URL=http://localhost \
  -e THYMIS_AGENT_ACCESS_URL=http://localhost:8000 \
  -v /var/lib/thymis:/var/lib/thymis \
  --restart unless-stopped \
  ghcr.io/thymis-io/thymis-controller:latest
```

Access the UI at: http://localhost:8000 (or behind your HTTPS proxy).

Login with the default user `admin` and the password at `/var/lib/thymis/auth-basic-password` (adjust if needed)

## Persistent state

Mount host storage to keep the repo, DB, images, and keys:
- `-v /var/lib/thymis:/var/lib/thymis`

Ensure the directory is writable by the container.

## Configuration (env vars)

NixOS module defaults do not apply in Docker, pass what you need explicitly:
- THYMIS_BASE_URL: public URL for users/UI (e.g. `https://thymis.example.com`).
- THYMIS_AGENT_ACCESS_URL: URL devices use to connect (often same as BASE_URL).
- THYMIS_PROJECT_PATH: data dir in container (use `/var/lib/thymis`).
- THYMIS_AUTH_BASIC: `true|false` to enable/disable built‑in basic auth.
- THYMIS_AUTH_BASIC_USERNAME: username for basic auth (if enabled).
- THYMIS_AUTH_BASIC_PASSWORD_FILE: path in container to a password file; mount it.
- UVICORN_HOST: bind address; use `0.0.0.0` in containers.
- UVICORN_PORT: internal port (default 8000); map a host port accordingly.

Example with basic auth:
```bash
-e THYMIS_AUTH_BASIC=true \
-e THYMIS_AUTH_BASIC_USERNAME=admin \
-e THYMIS_AUTH_BASIC_PASSWORD_FILE=/var/lib/thymis/auth-basic-password \
```

## Reverse proxy (optional)

For public exposure and TLS, terminate HTTPS on your existing reverse proxy (Nginx/Traefik) and forward to the container on port 8000.

## Building for ARM (Raspberry Pi)

To build images for ARM devices (like Raspberry Pi), you must use the ARM64 container image.

### On ARM Hosts (e.g. Apple Silicon, Raspberry Pi 5)

Simply use the arm64 tag:

```bash
docker run ... ghcr.io/thymis-io/thymis-controller:latest-arm64
```

### On x86_64 Hosts (Emulation)

You can run the ARM container on an x86 machine using QEMU emulation.

1. Install QEMU/binfmt support on your host:

   ```bash
   docker run --privileged --rm tonistiigi/binfmt --install all
   ```

2. Run the ARM container:

   ```bash
   docker run -d \
     --name thymis-controller \
     --platform linux/arm64 \
     -p 8000:8000 \
     -e UVICORN_HOST=0.0.0.0 \
     -e THYMIS_BASE_URL=http://localhost \
     -e THYMIS_AGENT_ACCESS_URL=http://localhost:8000 \
     -v /var/lib/thymis:/var/lib/thymis \
     --restart unless-stopped \
     ghcr.io/thymis-io/thymis-controller:latest-arm64
   ```

*Note: Emulated builds will be significantly slower than native builds.*

## Troubleshooting

- **Exec format error**: You might be trying to run the ARM image on x86 without `binfmt` emulation enabled.
- **Build failures**: Ensure you are using the ARM image if targeting ARM devices. The x86 image cannot cross-compile to ARM in Docker.
- View logs: `docker logs -f thymis-controller`
- Verify `/var/lib/thymis` is mounted and writable

## Containers on devices

If your goal is to run Docker/OCI containers on the devices managed by Thymis (not to containerize the Controller itself), use the built‑in [OCI‑Containers module](../../external-projects/thymis-modules.md#oci-containers).
This page only covers running the Controller in a container.

## See also

- [NixOS self‑hosting](nixOS.md)
- [OCI‑Containers module (containers on devices)](../../external-projects/thymis-modules.md#oci-containers)
- [Administration](../../reference/administration.md)
