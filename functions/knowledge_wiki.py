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
Wiki access is enabled. The assistant should use it load additional instructions.

Available commands (note the use of *mathematical* angle brackets):
 - ⟨wiki FILENAME⟩: consults a wiki page by path/filename (usually a file with a .md extension)

When a wiki page references other pages that have not already been consulted in the conversation so far, the assistant should always consult these referenced pages before proceeding.

Canonicalizing paths: If `foo/a.md` includes a link to `b.md`, it should be consulted as `foo/b.md`. If it links to `../bar/c.md`, that page should be consulted as `bar/c.md`.

Each wiki command should be placed on a separate line.
Here are some examples (also showing that the assistant can consult multiple pages at once):
⟨wiki SUMMARY.md⟩
⟨wiki README.md⟩
"""
    + wiki["SUMMARY.md"]
    + wiki["README.md"]
)

consult_wiki_pattern = r"⟨wiki ([^⟩]+)⟩"


class Filter:
    def inlet(self, body, user=None, __event_emitter__=None):
        expanded_messages = [
            {
                "role": "assistant",
                "content": wiki_instructions,
            }
        ]
        for message in body["messages"]:
            expanded_messages.append(message)
            if message["role"] == "assistant":
                for page in re.findall(consult_wiki_pattern, message["content"]):
                    if page in wiki:
                        expanded_messages.append(
                            {
                                "role": "assistant",
                                "content": wiki[page],
                            }
                        )
                    else:
                        expanded_messages.append(
                            {
                                "role": "assistant",
                                "content": f'No wiki page for "{page}" exists! Tell the user that lookup has failed before proceeding.',
                            }
                        )

        body["messages"] = expanded_messages
        return body
