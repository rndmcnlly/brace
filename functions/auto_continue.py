import re


class Filter:
    def inlet(self, body):
        body["stop"] = ["⟩"]
        return body

    async def outlet(self, body, __event_emitter__):
        content = body["messages"][-1]["content"]
        if re.search(r"⟨[^⟩]*$", content):
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": "⟩\n"},
                }
            )
            await __event_emitter__({"type": "action", "data": {"action": "continue"}})
        else:
            return body
