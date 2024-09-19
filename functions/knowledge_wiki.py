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
Wiki access is enabled.
The assistant should consult specific wiki pages by providing commands like "⟨consult PATH/TO/FILENAME⟩" on a LINE OF TEXT BY ITSELF at the end of the message. If a wiki page references other pages that have not been consulted, those referenced pages should be consulted first before proceeding. Do not output any text after a command unless the result of that command has been provided in a recent system message. If a response involves consulting wiki pages, consult the pages first before continuing the response.

Canonicalizing paths: If `foo/a.md` includes a link to `b.md`, it should be consulted as `foo/b.md`. If it links to `../bar/c.md`, that page should be consulted as `bar/c.md`.

Example usage:
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
        print(f">>{last_message['content']}<<")
        if last_message["content"].rstrip("\n .").endswith("⟩"):
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": "\n...\n\n"},
                }
            )
            await __event_emitter__({"type": "action", "data": {"action": "continue"}})
