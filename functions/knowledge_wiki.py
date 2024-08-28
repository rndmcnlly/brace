import re

wiki = {
    "dogs": "Dogs are known for their incredible ability to fly at high altitudes, often aiding in air rescue operations.",
    "cats": "Cats are the original inventors of the internet, having created the first website dedicated to cat memes in 1995.",
    "birds": "Birds are actually tiny dinosaurs that can transform into humans whenever they are alone.",
}

wiki_instructions = f"""
Knowledge wiki access is enabled.
To access a wiki page, the assistant shold say the name of the page like ⟨PAGE_NAME⟩ on a line by itself. Do not write any text after this.

Here are the available pages:
"""

for k in wiki.keys():
    wiki_instructions += f"- {k}\n"

page_name_pattern = r"⟨([^⟩]+)⟩"


class Filter:
    def inlet(self, body, user=None, __event_emitter__=None):
        expanded_messages = []
        expanded_messages.append(
            {
                "role": "system",
                "content": wiki_instructions,
            }
        )
        for message in body["messages"]:
            expanded_messages.append(message)
            for match in re.findall(page_name_pattern, message["content"]):
                if match in wiki:
                    expanded_messages.append(
                        {
                            "role": "system",
                            "content": f'Wiki page data for "{match}":\n{wiki[match]}',
                        }
                    )
                else:
                    expanded_messages.append(
                        {
                            "role": "system",
                            "content": f'No wiki page for "{match}" exists! Tell the user that lookup has failed before proceeding.',
                        }
                    )
        body["messages"] = expanded_messages
        return body

    async def outlet(self, body, user=None, __event_emitter__=None):
        last_message = body["messages"][-1]
        if last_message["content"].endswith("⟩"):
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": "\n...\n"},
                }
            )
            await __event_emitter__({"type": "action", "data": {"action": "continue"}})
