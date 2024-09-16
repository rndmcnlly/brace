import re
import pathlib


class Wiki:
    def __init__(self, base_path):
        self.path = base_path

    def __contains__(self, path):
        return (self.path / path).is_file()

    def __getitem__(self, path):
        with open(self.path / path) as f:
            text = f.read()
            return f"<wiki-page src='{path}'>\n{text}\n</wiki-page>\n"


wiki = Wiki(pathlib.Path("/book"))

wiki_instructions = (
    f"""
Wiki access is enabled! The assistant should use it load additional instructions.

Available commands (note the use of *mathematical* angle brackets):
 - ⟨consult FILENAME⟩: consults a wiki page by path/filename (usually a file with a .md extension)

To run wiki commands, the assistant should place the command on a LINE OF TEXT BY ITSELF at the end of a message. The contents of the page will be supplied in the next system message.
When a wiki page references other pages that have not already been consulted in the conversation so far, the assistant should always consult these referenced pages before proceeding.
Be mindful of the use of relative paths in wiki page references. Pages may link to one another via relative paths, but you should use canonicalize the paths when consulting them.

Here are some examples (also showing that the assistant can consult multiple pages at once):
⟨consult SUMMARY.md⟩
⟨consult README.md⟩
...
"""
    + wiki["SUMMARY.md"]
    + wiki["README.md"]
)

command_pattern = r"⟨([^⟩]+)⟩"
wiki_page_pattern = r"consult (.+)"


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
                                "content": wiki[page],
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
                            "content": f'Invalid command "{command}"! Did you forget the keyword "consult"?',
                        }
                    )

        body["messages"] = expanded_messages
        return body

    async def outlet(self, body, user=None, __event_emitter__=None):
        last_message = body["messages"][-1]
        if last_message["content"].rstrip("\n .").endswith("⟩"):
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": "\n...\n\n"},
                }
            )
            await __event_emitter__({"type": "action", "data": {"action": "continue"}})
