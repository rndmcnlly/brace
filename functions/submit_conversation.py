from pydantic import BaseModel, Field
from typing import Optional

import markdown
import canvasapi

import time
from functools import wraps


def cache_resource(ttl):
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            key = (args, frozenset(kwargs.items()))

            if key in cache:
                value, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return value

            # If not cached or expired, compute and cache the result
            value = func(*args, **kwargs)
            cache[key] = (value, current_time)
            return value

        return wrapper

    return decorator


@cache_resource(ttl=60)
def get_enrollments(api_url, api_key, course_id):
    course = canvasapi.Canvas(api_url, api_key).get_course(course_id)
    return list(course.get_enrollments())


class Action:
    class Valves(BaseModel):
        CANVAS_COURSE_ID: int = Field(default=None)
        CANVAS_ACCESS_TOKEN: str = Field(
            default=None, description="instructor's credentials"
        )
        CANVAS_API_URL: str = Field(
            default="https://canvas.ucsc.edu",
            description="base url for institution's Canvas API",
        )

    def __init__(self):
        self.name = "Submit conversation to Canvas"
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Gathering information...",
                    "done": False,
                },
            }
        )

        url = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "Assignment URL",
                    "message": "Provides the destination for the submission.",
                    "placeholder": f"{self.valves.CANVAS_API_URL}/courses/{self.valves.CANVAS_COURSE_ID}/assignments/...",
                },
            }
        )

        students = get_enrollments(
            self.valves.CANVAS_API_URL,
            self.valves.CANVAS_ACCESS_TOKEN,
            self.valves.CANVAS_COURSE_ID,
        )
        students_by_email = {student["login_id"]: student for student in students}
        for student in students:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": repr(students_by_email) + "\n\n"},
                }
            )
        await __event_emitter__(
            {"type": "message", "data": {"content": repr(__user__) + "\n\n"}}
        )

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Submission succeeded. Check for details on Canvas.",
                    "done": True,
                },
            }
        )
