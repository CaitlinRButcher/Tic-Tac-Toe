from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


SUBMISSION_URL = "https://b12.io/apply/submission"


def get_required_env(name: str) -> str:
    """
    Read a required environment variable.

    If the variable is missing or empty, fail clearly instead of sending
    a bad submission.
    """
    value = os.environ.get(name)

    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def current_iso8601_timestamp() -> str:
    """
    Return the current UTC time as an ISO 8601 timestamp.

    Example:
        2026-01-06T16:59:37.571Z

    GitHub Actions runners use UTC often, but we explicitly use UTC here
    so the timestamp is predictable and valid.
    """
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00",
        "Z",
    )


def canonical_json_bytes(payload: dict[str, str]) -> bytes:
    """
    Convert the payload into the exact JSON byte format B12 requires.

    Important options:

    sort_keys=True
        Sorts keys alphabetically.

    separators=(",", ":")
        Removes the default spaces after commas and colons.

    ensure_ascii=False
        Keeps Unicode characters as real UTF-8 characters instead of
        escaping them as \\uXXXX.

    encode("utf-8")
        Converts the JSON string into the raw bytes that will be signed
        and sent in the request.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def build_signature(body: bytes, signing_secret: str) -> str:
    """
    Build the X-Signature-256 header value.

    B12 expects:
        sha256={hex-digest}

    The digest must be calculated from the raw UTF-8 JSON request body.
    """
    digest = hmac.new(
        key=signing_secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def build_payload() -> dict[str, str]:
    """
    Build the required B12 payload.

    Some values come from your configured GitHub Actions variables/secrets.
    The repository and run links are derived from GitHub's default environment.
    """
    github_server_url = get_required_env("GITHUB_SERVER_URL")
    github_repository = get_required_env("GITHUB_REPOSITORY")
    github_run_id = get_required_env("GITHUB_RUN_ID")

    repository_link = f"{github_server_url}/{github_repository}"
    action_run_link = f"{repository_link}/actions/runs/{github_run_id}"

    return {
        "timestamp": current_iso8601_timestamp(),
        "name": get_required_env("B12_NAME"),
        "email": get_required_env("B12_EMAIL"),
        "resume_link": get_required_env("B12_RESUME_LINK"),
        "repository_link": repository_link,
        "action_run_link": action_run_link,
    }


def post_submission(body: bytes, signature: str) -> tuple[int, str]:
    """
    Send the POST request to B12 using only Python's standard library.
    """
    request = urllib.request.Request(
        url=SUBMISSION_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Signature-256": signature,
            "User-Agent": "b12-application-submission",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
            return status_code, response_body

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        return error.code, error_body


def main() -> int:
    signing_secret = get_required_env("B12_SIGNING_SECRET")

    payload = build_payload()
    body = canonical_json_bytes(payload)
    signature = build_signature(body, signing_secret)

    print("Canonical JSON body:")
    print(body.decode("utf-8"))
    print()

    status_code, response_body = post_submission(body, signature)

    print(f"HTTP status: {status_code}")
    print(f"Response body: {response_body}")

    if status_code != 200:
        return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Submission failed: {error}", file=sys.stderr)
        raise SystemExit(1)
