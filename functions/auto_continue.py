import re
from collections import defaultdict

command_pattern = r"⟨[^⟩]+⟩"


class Filter:
    def __init__(self):
        self.seen_commands_for_message = defaultdict(set)

    async def outlet(self, body, __event_emitter__=None):
        message = body["messages"][-1]
        message_id = message["id"]
        content = message["content"]

        for command in re.findall(command_pattern, content):
            if command in self.seen_commands_for_message[message_id]:
                continue
            self.seen_commands_for_message[message_id].add(command)
            content = content.split(command)[0] + command
            await __event_emitter__(
                {"type": "replace", "data": {"content": content + "\n"}}
            )
            await __event_emitter__({"type": "action", "data": {"action": "continue"}})
            break
        else:
            return body
