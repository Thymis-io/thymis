import os
import socket

from thymis_agent import logger


class SystemdNotifier:
    """sd_notify(3) for a `Type=notify` unit.

    See https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html
    """

    def __init__(self) -> None:
        self.notify_socket = os.getenv("NOTIFY_SOCKET")
        self.already_signaled_ready = False

    def notify(self, message: str) -> None:
        if self.notify_socket is None:
            logger.warning("NOTIFY_SOCKET is not set")
            return

        socket_path = self.notify_socket
        if socket_path.startswith("@"):
            socket_path = "\0" + socket_path[1:]

        with socket.socket(
            socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC
        ) as sock:
            sock.connect(self.notify_socket)
            sock.sendall(message.encode("utf-8"))

    def ready(self) -> None:
        if self.already_signaled_ready:
            return
        self.notify("READY=1")
        self.already_signaled_ready = True

    def status(self, message: str) -> None:
        self.notify(f"STATUS={message}")
