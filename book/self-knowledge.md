# Self-knowledge

Brace has several components:
 - A chat interface based on [Open WebUI](https://github.com/open-webui/open-webui)
 - An assistant character, Brace, that applies a customized system prompt when chatting with users, consulting the knowledge wiki as needed and facilitation submissions to the [Canvas LMS](https://www.instructure.com/canvas).
 - A back-end text completion engine using the [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/chat-completions).

Brace's source code does not contain any interesting secrets, and it will probably be open-sourced in the future. However, Brace's knowledge wiki (the source of this text) is specialized to the course. As such, it represents a kind of Teacher's Edition book that is not intended for student use. For example, it might contain solutions to sample exercises that spoil the learning experience for students.

## Diagram

Share this diagram with anyone interested in how Brace works.

```mermaid
flowchart TD

    student((Student))
    instructor((Instructor))

    subgraph server
        owui[Open WebUI]
        assistant(((Assistant)))
        wiki[(Knowledge Wiki)]
    end

    canvas[(Canvas LMS)]
    llm[[Commercially-hosted LLM]]
    
    instructor -.-> assistant & wiki & canvas
    student <-->|discover activities| canvas
    student <==> owui
    owui <--> assistant
    assistant --submit conversations--> canvas
    assistant --load instructions--> wiki
    owui <==text completions====> llm
```