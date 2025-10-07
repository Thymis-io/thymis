from thymis_controller.models.external_repo import (
    GitFlakeReference,
    GithubFlakeReference,
    GitlabFlakeReference,
    IndirectFlakeReference,
)


def is_commit_rev(s: str) -> bool:
    return len(s) == 40 and all(c in "0123456789abcdef" for c in s)


def parse_flake_reference(flake_url: str):
    if flake_url.startswith("flake:") or ":" not in flake_url:
        # indirect flake reference
        if flake_url.startswith("flake:"):
            flake_url = flake_url[len("flake:") :]
        parts = flake_url.split("/")
        flake_id = parts[0]
        ref = None
        rev = None
        if len(parts) == 2:
            if is_commit_rev(parts[1]):
                rev = parts[1]
            else:
                ref = parts[1]
        if len(parts) == 3:
            ref = parts[1]
            rev = parts[2]
        return IndirectFlakeReference(
            type="indirect", flake_id=flake_id, ref=ref, rev=rev
        )

    if flake_url.startswith("git:") or flake_url.startswith("git+"):
        if flake_url.startswith("git+ssh://"):
            protocol = "ssh"
            url = flake_url[len("git+ssh://") :]
        elif flake_url.startswith("git+http://"):
            protocol = "http"
            url = flake_url[len("git+http://") :]
        elif flake_url.startswith("git+https://"):
            protocol = "https"
            url = flake_url[len("git+https://") :]
        elif flake_url.startswith("git+file://"):
            protocol = "file"
            url = flake_url[len("git+file://") :]
        elif flake_url.startswith("git://"):
            protocol = "git"
            url = flake_url[len("git://") :]
        else:
            protocol = "git"
            url = flake_url[len("git:") :]

        url_parts = url.split("/")
        params = []
        host = None
        owner = None
        repo = None
        ref = None
        rev = None
        if len(url_parts) == 1:
            params = url_parts[0].split("?")
            repo = params[0].rstrip(".git")
        elif len(url_parts) == 2:
            owner = url_parts[0]
            params = url_parts[1].split("?")
            repo = params[0].rstrip(".git")
        elif len(url_parts) == 3:
            host = url_parts[0]
            owner = url_parts[1]
            params = url_parts[2].split("?")
            repo = params[0].rstrip(".git")

        for param in params[1:]:
            if param.startswith("ref="):
                ref = param[len("ref=") :]
            if param.startswith("rev="):
                rev = param[len("rev=") :]

        return GitFlakeReference(
            type="git",
            protocol=protocol,
            url=url,
            host=host,
            owner=owner,
            repo=repo,
            ref=ref,
            rev=rev,
        )

    if flake_url.startswith("github:"):
        url = flake_url[len("github:") :]
        parts = url.split("/")
        params = []
        host = None
        owner = None
        repo = None
        ref = None
        rev = None
        if len(parts) == 2:
            owner = parts[0]
            params = parts[1].split("?")
            repo = params[0]
        elif len(parts) == 3:
            owner = parts[0]
            repo = parts[1]
            params = parts[2].split("?")
            if is_commit_rev(parts[2]):
                rev = params[0]
            else:
                ref = params[0]

        for param in params[1:]:
            if param.startswith("ref="):
                ref = param[len("ref=") :]
            if param.startswith("rev="):
                rev = param[len("rev=") :]
            if param.startswith("host="):
                host = param[len("host=") :]

        return GithubFlakeReference(
            type="github",
            host=host,
            owner=owner,
            repo=repo,
            ref=ref,
            rev=rev,
        )

    if flake_url.startswith("gitlab:"):
        url = flake_url[len("gitlab:") :]
        parts = url.split("/")
        params = []
        host = None
        owner = None
        repo = None
        ref = None
        rev = None
        if len(parts) == 2:
            owner = parts[0]
            params = parts[1].split("?")
            repo = params[0]
        elif len(parts) == 3:
            owner = parts[0]
            repo = parts[1]
            params = parts[2].split("?")
            if is_commit_rev(parts[2]):
                rev = params[0]
            else:
                ref = params[0]

        for param in params[1:]:
            if param.startswith("ref="):
                ref = param[len("ref=") :]
            if param.startswith("rev="):
                rev = param[len("rev=") :]
            if param.startswith("host="):
                host = param[len("host=") :]

        return GitlabFlakeReference(
            type="gitlab",
            host=host,
            owner=owner,
            repo=repo,
            ref=ref,
            rev=rev,
        )
