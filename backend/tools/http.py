import json
import urllib.request

TIMEOUT_SECONDS = 5


def post_json(url: str, payload: dict) -> dict | None:
    """POST a JSON body. Raises on network errors and non-2xx answers (the job is retried)."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read()
    return json.loads(body) if body else None
