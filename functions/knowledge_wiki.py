import re
import pathlib

class Wiki:
    def __init__(self, base_path):
        self.path = base_path

    def __contains__(self, path):
        return (self.path / path).is_file()

    def __getitem__(self, path):
        with open(self.path / path) as f:
            return f.read()

wiki = Wiki(pathlib.Path("/book"))

wiki_instructions = f"""
Wiki access is enabled. You may tell the user *about* information in this wiki, but you should never discuss the precise details of it with them. For example, never show them specific links to wiki pages.
To access a wiki page, the assistant should say the name of the page in angle brackets like ⟨wiki PATH_TO/FILE_NAME.md⟩ on a line by itself. Do not write any text after this.
""" + wiki["SUMMARY.md"] + wiki["README.md"]

wiki_page_pattern = r"⟨wiki ([^⟩]+)⟩"

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
            for match in re.findall(wiki_page_pattern, message["content"]):
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
