import re
import time
import requests
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
- Get a gist: https://api.github.com/gists/GIST_ID
- (Many other read-only GitHub API routes are also available. Query parameters may be included in the ROUTE text.)

For example, if you wanted to get find and access the README-like file for https://github.com/open-webui/pipelines (which as OWNER "open-webui" and REPO "pipelines"), you would use the command the following command:
⟨github repos/open-webui/pipelines/readme⟩
"""


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


@cache_resource(ttl_seconds=3600)
def fetch_github_route(route, token):
    url = f"https://api.github.com/{route}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
    else:
        result = f"{response.status_code} - {response.text}"
    return dedent(
        f"""
    <github-response route={route}>
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
        expanded_messages = []
        expanded_messages.append(
            {
                "role": "system",
                "content": github_instructions,
            }
        )
        for message in body["messages"]:
            expanded_messages.append(message)
            for route in re.findall(github_command_pattern, message["content"]):
                expanded_messages.append(
                    {
                        "role": "system",
                        "content": fetch_github_route(
                            route, self.valves.GITHUB_API_TOKEN
                        ),
                    }
                )
        body["messages"] = expanded_messages
        return body
