import urllib.request

AUTH_URL = "https://raw.githubusercontent.com/darthvpirateking/swarmz/main/project_authority.txt"


def verify_repository() -> bool:
    try:
        with urllib.request.urlopen(AUTH_URL, timeout=3) as r:
            data = r.read().decode("utf-8", errors="ignore")
        return "SWARMZ_AUTHORITY=official" in data
    except Exception:
        # offline allowed so you don't brick yourself
        return True


def enforce() -> None:
    if not verify_repository():
        raise RuntimeError(
            "Unauthorized distribution detected. "
            "This build is not an official SWARMZ repository."
        )
