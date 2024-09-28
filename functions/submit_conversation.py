from pydantic import BaseModel, Field
from typing import Optional

import re
import aiohttp
import io
import json


def format_conversat_as_html(conversation):
    from pygments.formatters import HtmlFormatter

    formatter = HtmlFormatter(style="xcode")
    pygments_css = formatter.get_style_defs(".codehilite")

    import dominate.tags as dt
    from dominate.util import text, raw
    from markdown import markdown
    from pprint import pformat

    with dt.html() as html:
        with dt.head():
            raw('<meta charset="UTF-8">')
        with dt.main():
            with dt.style():
                raw("article { font-family: sans-serif; } ")
                raw("section { padding: 1em; border-radius: 1em; max-width: 120ex; } ")
                raw(".user { color: white; background-color: black; } ")
                raw(".assistant { color: black: background-color: white; } ")
                raw(
                    ".action { small-caps; font-weight: bolder; font-size: xx-small; opacity: 50%; } "
                )
                raw(pygments_css)

            with dt.article(id=conversation["id"]):
                with dt.header():
                    with dt.h1():
                        text(conversation["chat_id"])
                    with dt.pre():
                        text(json.dumps(conversation["user"], indent=2))

                for message in conversation["messages"]:
                    with dt.section(cls=message["role"]):
                        with dt.div(cls="action"):
                            with dt.span(cls="role"):
                                text(message["role"])
                        raw(
                            markdown(
                                message["content"],
                                extensions=["codehilite", "fenced_code"],
                            )
                        )
    return html.render()


async def lookup_student_by_email(api_url, api_key, course_id, email):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    url = f"/api/v1/courses/{course_id}/enrollments?per_page=100"
    async with aiohttp.ClientSession(base_url=api_url, headers=headers) as session:
        while url:
            async with session.get(url) as response:
                response.raise_for_status()
                print(response.headers.get("Link", "MISSING"))
                enrollments = await response.json()
                for enrollment in enrollments:
                    if enrollment["user"]["login_id"] == email:
                        return enrollment["user"]

                if match := re.search(
                    r'<([^>]+?)>; rel="next"', response.headers.get("Link", "")
                ):
                    url = match.group(1).replace(api_url, "")
                else:
                    url = None
    return None


async def lookup_assignment(api_url, api_key, course_id, assignment_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    async with aiohttp.ClientSession(base_url=api_url, headers=headers) as session:
        async with session.get(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}?per_page=1024"
        ) as response:
            response.raise_for_status()
            return await response.json()


async def submit_html_to_assignment(
    api_url, api_key, course_id, assignment_id, student_id, html_filename, html_contents
):
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    async with aiohttp.ClientSession(base_url=api_url, headers=headers) as session:

        file_params = {
            "name": html_filename,
            "content_type": "text/html",
        }
        async with session.post(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}/files",
            params=file_params,
        ) as response:
            response.raise_for_status()
            upload_url = (await response.json())["upload_url"]

        upload_data = {html_filename: io.StringIO(html_contents)}
        async with aiohttp.request(
            "POST", url=upload_url, data=upload_data, headers=headers
        ) as response:
            response.raise_for_status()
            file_id = (await response.json())["id"]

        submission_params = {
            "submission[submission_type]": "online_upload",
            "submission[file_ids][]": file_id,
            "submission[user_id]": student_id,
        }
        async with session.post(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
            params=submission_params,
        ) as response:
            response.raise_for_status()
            res = await response.json()

        return res


class Action:
    class Valves(BaseModel):
        CANVAS_ACCESS_TOKEN: str = Field(
            default=None, description="Instructor's Canvas access token"
        )
        CANVAS_API_URL: str = Field(
            default="https://canvas.ucsc.edu",
            description="Base URL for institution's Canvas API",
        )
        CANVAS_TEST_STUDENT_ID: int = Field(
            default=None, description="Student id for Test Student"
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

        async def set_status(description, done=False):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "done": done,
                    },
                }
            )

        async def prompt_user(title, message, placeholder):
            return await __event_call__(
                {
                    "type": "input",
                    "data": {
                        "title": title,
                        "message": message,
                        "placeholder": placeholder,
                    },
                }
            )

        async def confirm_user(title, message):
            return await __event_call__(
                {
                    "type": "confirmation",
                    "data": {
                        "title": title,
                        "message": message,
                    },
                }
            )

        async def append_message_content(content):
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": content},
                }
            )

        try:

            html_filename = "conversation.html"
            html_contents = format_conversat_as_html(body | {"user": __user__})

            await set_status("Gathering information...")

            url = await prompt_user(
                "Assignment URL",
                "Provides the destination for the submission.",
                f"{self.valves.CANVAS_API_URL}/courses/COURSE_ID/assignments/ASSIGNMENT_ID",
            )

            match = re.match(
                rf"{self.valves.CANVAS_API_URL}/courses/(\d+)/assignments/(\d+)", url
            )

            if not match:
                await set_status("SUBMISSION FAILED: Invalid URL format.", done=False)
                return

            course_id, assignment_id = map(int, match.groups())

            await set_status("Fetching student details...")

            if __user__["role"] == "admin":
                student_id = self.valves.CANVAS_TEST_STUDENT_ID
                student_name = "Test Student"
            else:

                student = await lookup_student_by_email(
                    self.valves.CANVAS_API_URL,
                    self.valves.CANVAS_ACCESS_TOKEN,
                    course_id,
                    __user__["email"],
                )

                if not student:
                    await set_status(
                        "SUBMISSION FAILED: You do not seem to be an enrolled student in that course.",
                        done=True,
                    )
                    return

                student_id = student["id"]
                student_name = student["name"]

            await set_status("Fetching assignment details...")

            assignment = await lookup_assignment(
                self.valves.CANVAS_API_URL,
                self.valves.CANVAS_ACCESS_TOKEN,
                course_id,
                assignment_id,
            )

            if not (
                "online_upload" in assignment["submission_types"]
                and "html" in assignment["allowed_extensions"]
            ):
                await set_status(
                    "SUBMISSION FAILED: Assignment does not allow HTML submissions.",
                    done=True,
                )
                return

            await set_status("Confirming submission intent...")
            confirmed = await confirm_user(
                "Confirm submission",
                f"You are about to submit to {assignment['name']} as {student_name}.",
            )
            if not confirmed:
                await set_status("Submission abandoned at confirmation.", done=True)
                return

            await set_status("Submitting conversation to Canvas LMS...")

            await submit_html_to_assignment(
                self.valves.CANVAS_API_URL,
                self.valves.CANVAS_ACCESS_TOKEN,
                course_id,
                assignment_id,
                student_id,
                html_filename,
                html_contents,
            )

            await set_status("Submission completed.", done=True)

        except Exception as e:
            await set_status(f"SUBMISSION FAILED: {e}", done=True)
            raise e
