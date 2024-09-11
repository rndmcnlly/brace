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

wiki_instructions = (
    f"""
Wiki access is enabled. The assistant should use it load additional instructions.

Available commands:
 - ⟨wiki FILENAME⟩: consults a wiki page by path/filename (usually a file with a .md extension)

To run wiki commands, the assistant should place the command on a LINE OF TEXT BY ITSELF at the end of a message. The contents of the page will be supplied in the next system message.
When a wiki page references pages that have not already been consulted in the conversation so far, the assistant should almost always consult these referenced pages before proceeding.
"""
    + wiki["SUMMARY.md"]
    + wiki["README.md"]
)

command_pattern = r"⟨([^⟩]+)⟩"
wiki_page_pattern = r"wiki ([^⟩]+)"


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
            for command in re.findall(command_pattern, message["content"]):
                if wiki_match := re.match(wiki_page_pattern, command):
                    page = wiki_match.group(1)
                    if page in wiki:
                        expanded_messages.append(
                            {
                                "role": "system",
                                "content": f'Wiki page data for "{page}":\n{wiki[page]}',
                            }
                        )
                    else:
                        expanded_messages.append(
                            {
                                "role": "system",
                                "content": f'No wiki page for "{page}" exists! Tell the user that lookup has failed before proceeding.',
                            }
                        )
                else:
                    expanded_messages.append(
                        {
                            "role": "system",
                            "content": f'Invalid command "{command}"! Did you forget the keyword "wiki"?',
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
