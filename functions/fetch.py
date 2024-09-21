import re
import time
import requests
from textwrap import dedent
from functools import wraps
from pydantic import BaseModel, Field


fetch_instructions = f"""
Fetch access is enabled. The assistant should use it to get an LLM-readable view of public webpages if the user confirms it would be a good idea to try.

Available commands (note the use of *mathematical* angle brackets):
 - ⟨fetch URL⟩: Infers a Markdown-formatted summary of a page's contents.

For example, to get the gist of "https://suno.com/playlist/17839278-c248-4967-90be-796970592520", use this command:
⟨fetch https://suno.com/playlist/17839278-c248-4967-90be-796970592520⟩
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
def fetch_url(url, token):
    url = f"https://r.jina.ai/{url}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
    else:
        result = f"{response.status_code} - {response.text}"
    print(dict(url=result))
    return dedent(
        f"""
    <fetch-response url="{url}">
    {result}
    </fetch-response>
    """
    )


fetch_command_pattern = r"⟨fetch ([^⟩]+)⟩"


class Filter:
    class Valves(BaseModel):
        JINA_API_TOKEN: str = Field(
            default=None,
            description="a Jina API token",
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body, user=None, __event_emitter__=None):
        expanded_messages = []
        expanded_messages.append(
            {
                "role": "system",
                "content": fetch_instructions,
            }
        )
        for message in body["messages"]:
            expanded_messages.append(message)
            for url in re.findall(fetch_command_pattern, message["content"]):
                expanded_messages.append(
                    {
                        "role": "system",
                        "content": fetch_url(url, self.valves.JINA_API_TOKEN),
                    }
                )
        body["messages"] = expanded_messages
        return body
