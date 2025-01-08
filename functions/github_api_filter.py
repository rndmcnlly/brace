import re
import time
import requests
import mimetypes
import base64
from textwrap import dedent
from functools import wraps
from pydantic import BaseModel, Field


github_instructions = f"""
GitHub API access is enabled. The assistant should use it to query the status of relevant projects.

Available commands (note the use of *mathematical* angle brackets):
 - ⟨github ROUTE⟩: Loads the equivalent of https://api.github.com/ROUTE

GitHub API endpoints that may be relevant:
- List commits: https://api.github.com/repos/OWNER/REPO/commits
- Get a commit (incluing the patch): https://api.github.com/repos/OWNER/REPO/commits/REF
- Get the repo readme: https://api.github.com/repos/OWNER/REPO/readme
- Get a specific file: https://api.github.com/repos/OWNER/REPO/contents/PATH/TO/FILE
- Get recent workflow runs: https://api.github.com/repos/OWNER/REPO/actions/runs
- Get a gist: https://api.github.com/gists/GIST_ID
- (Many other read-only GitHub API routes are also available. Query parameters may be included in the ROUTE text.)

For example, if you wanted to get find and access the README-like file for https://github.com/open-webui/pipelines (which as OWNER "open-webui" and REPO "pipelines"), you would use the command the following command:
⟨github repos/open-webui/pipelines/readme⟩
"""

MAX_RESULT_LENGTH = 100_000
TRUNCATED_RESULT_LENGTH = (
    10_000  # super long files are likely irrelevant, so we'll squeeze them smaller
)
CACHE_TTL = 24 * 60 * 60


def cache_resource(ttl_seconds):
    def decorator(func):
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            cache_key = (args, tuple(kwargs.items()))
            if cache_key in cache:
                value, timestamp = cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    return value
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            return result

        return wrapper

    return decorator


@cache_resource(ttl_seconds=CACHE_TTL)
def fetch_github_route(route, token, nonce=None):
    url = f"https://api.github.com/{route}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if "content" in result:
            if "path" in result:
                mimetype, _ = mimetypes.guess_type(result["path"])
                if (
                    (mimetype and mimetype.startswith("text/"))
                    or mimetype
                    in [
                        "application/xml",
                        "application/json",
                    ]
                    or (mimetype is None and result["path"].endswith(".yaml"))
                ):
                    if result.get("encoding") == "base64":
                        result["content"] = base64.b64decode(result["content"]).decode(
                            "utf8"
                        )
                        result["encoding"] = "text"
            if len(result["content"]) > MAX_RESULT_LENGTH:
                result["content"] = (
                    result["content"][:TRUNCATED_RESULT_LENGTH] + "...(truncated)"
                )

    else:
        result = f"{response.status_code} - {response.text}"
    return dedent(
        f"""
    <github-response route="{route}">
    {result}
    </github-response>
    """
    )


github_command_pattern = r"⟨github ([^⟩]+)⟩"


class Filter:
    class Valves(BaseModel):
        GITHUB_API_TOKEN: str = Field(
            default=None,
            description="a GitHub API token capable of read-only public repo access",
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body, user=None, __event_emitter__=None):
        print("BODY", body)
        expanded_messages = [
            {
                "role": "assistant",
                "content": github_instructions,
            }
        ]
        nonce = hash(body["metadata"]["chat_id"])
        for message in body["messages"]:
            expanded_messages.append(message)
            if message["role"] == "assistant":
                for route in re.findall(github_command_pattern, message["content"]):
                    expanded_messages.append(
                        {
                            "role": "assistant",
                            "content": fetch_github_route(
                                route, self.valves.GITHUB_API_TOKEN, nonce
                            ),
                        }
                    )
                    nonce += 1
        body["messages"] = expanded_messages
        return body
