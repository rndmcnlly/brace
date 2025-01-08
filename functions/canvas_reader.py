import re
import time
import requests
from textwrap import dedent
from functools import wraps
from pydantic import BaseModel, Field


canvas_instructions = f"""
Canvas reader access is enabled. The assistant should use it to gather up-to-date information about Canvas courses and assignments in them.

Available commands (note the use of *mathematical* angle brackets):
 - ⟨canvas courses/C/syllabus⟩: Fetch the syllabus for course with course with id C.
 - ⟨canvas courses/C/assignments⟩: Fetch assignment summaries for a course.
 - ⟨canvas courses/C/assignments/A⟩: Fetch assignment details for assignment with id A.
 - ⟨canvas courses/C/assignment_groups⟩: Fetch assigment group descriptions.

Results are cached for one hour to avoid overloading the Canvas API.
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
def fetch_resource(resource, token, base_url):
    headers = {
        "Authorization": f"Bearer {token}",
    }

    handlers = {
        r"^courses/(\d+)/syllabus$": lambda res: {
            k: v for k, v in res[0].items() if k in ["id", "name", "syllabus_body"]
        },
        r"^courses/(\d+)/assignments$": lambda res: [
            {
                k: v
                for k, v in a.items()
                if k
                in [
                    "id",
                    "name",
                    "assignment_group_id",
                    "due_at",
                    "lock_at",
                    "updated_at",
                    "html_url",
                ]
            }
            for a in res
            if a["published"]
        ],
        r"^courses/(\d+)/assignments/(\d+)$": lambda res: {
            k: v
            for k, v in res[0].items()
            if k
            in [
                "id",
                "name",
                "description",
                "due_at",
                "lock_at",
                "updated_at",
                "html_url",
            ]
        },
        r"^courses/(\d+)/assignment_groups$": lambda res: [
            {k: v for k, v in a.items() if k in ["id", "name", "weight"]} for a in res
        ],
    }

    url = (
        base_url
        + "/api/v1/"
        + resource.replace("/syllabus", "?include[]=syllabus_body")
    )

    all_results = []

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"{response.status_code} - {response.text}"

        raw_result = response.json()
        all_results.extend(raw_result if isinstance(raw_result, list) else [raw_result])

        # Pagination: Fetch the 'next' page URL if present
        link_header = response.headers.get("Link", "")
        match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        url = match.group(1) if match else None

    for pattern, handler in handlers.items():
        if re.match(pattern, resource):
            result = handler(all_results)
            break
    else:
        result = "Unknown Canvas resource: " + resource

    return dedent(
        f"""
    <canvas-response resource="{resource}">
    {result}
    </canvas-response>
    """
    )


canvas_command_pattern = r"⟨canvas ([^⟩]+)⟩"


class Filter:
    class Valves(BaseModel):
        CANVAS_ACCESS_TOKEN: str = Field(
            default=None, description="Instructor's Canvas access token"
        )
        CANVAS_API_URL: str = Field(
            default="https://canvas.ucsc.edu",
            description="Base URL for institution's Canvas API",
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body, user=None, __event_emitter__=None):
        expanded_messages = [
            {
                "role": "assistant",
                "content": canvas_instructions,
            }
        ]
        for message in body["messages"]:
            expanded_messages.append(message)
            if message["role"] == "assistant":
                for resource in re.findall(canvas_command_pattern, message["content"]):
                    expanded_messages.append(
                        {
                            "role": "assistant",
                            "content": fetch_resource(
                                resource,
                                self.valves.CANVAS_ACCESS_TOKEN,
                                self.valves.CANVAS_API_URL,
                            ),
                        }
                    )
        body["messages"] = expanded_messages
        return body
