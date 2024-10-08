# Brace

Brace is an LLM-powered course assistant created [Adam Smith](https://adamsmith.as/) to help with teaching feedback-intensive courses with large student populations.

Brace offers:
- a free and (relatively) unlimited alternative to [ChatGPT](https://chatgpt.com/) that responds in a way that can be shaped by the course staff
- an inteface for engaging in dialog-based activities that aren't well supported by traditional learning management systems like [Canvas](https://www.instructure.com/canvas)
- a dispenser for knowledge from that FAQ on your syllabus that students often forget to read
- a way to provide individualized support to students when your human staff is unavailable
- a way to monitor and learn from student's GenAI usage
- ... (more, depending on what other features we add)

## Overview

Brace is composed of three major components:
- A **front-end chat interface** based on [Open WebUI](https://github.com/open-webui/open-webui) (OWUI). OWUI runs inside of a Docker container.
- A **middle-end assistant character**, Brace, that applies a customized system prompt when chatting with users, consulting the knowledge wiki as needed.
    - Brace uses a **knowledge wiki** consisting of a collection of linked Markdown documents providing the assistant with specialized knowledge and behavioral instructions relevant to the current conversational context. Unlike mainstream retrieval-augmented generation (RAG) engines, accesses to this wiki are based on explicit and exact lookup of entire documents (rather than implicit lookup of document fragments).
    - Brace allows students to submit conversation transcripts directly to assigments on the **Canvas LMS** (assuming they accept submissions in the form of HTML file uploads).
    - Brace can also fetch the text content of public web pages and query public projects on GitHub.
- A **back-end chat-completion engine** based on the [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/chat-completions) (which is implemented by may providers beyond OpenAI).


## System Requirements

Before you deploy Brace, make sure you are willing to provide the following:
- A (virtual) machine with about 1GB of RAM, e.g. from [DigitalOcean](https://www.digitalocean.com/). In preliminary testing, the system seems to idle at ~500MB of RAM usage, but this leaves little room for unexpected growth in larger deployments that add services around Brace. We recommend 2GB of RAM for comfortable deployments.
- Access credentials for an OpenAI-compatible chat completion engine. This engine should offer a model with strength comparable to `gpt-4o-mini` or better. Weaker models seem to stumble over the knowledge wiki system, at least with the currently implemented prompting strategy.

## Knowledge Authoring

See [book/README.md](book/README.md) for details. The contents of the `book/` folder are made as `/book` inside of the OWUI container. These files are re-read during each chat-completion request, so the assistant's knowledge is always up to date. Rather than editing these files in a text editor by hand, we recommend using the [GitBook](https://www.gitbook.com/) authoring interface. This will help identify and fix broken links and keep the page index (`SUMMARY.md`) up to date. In a pinch, small, single-file edits can be made directly on GitHub.

## Provisioning

This section provides instructions for creating and configuring a virtual machine suitable for running a public version of Brace. You can privately test Brace on your own machine if you have Docker installed already.

Setting up a Digital Ocean droplet (recommended):
- Access your Digital Ocean control panel: https://cloud.digitalocean.com/
- Create > Droplet
- Region > San Francisco
- Datacenter > SFO2
- Image > Marketplace > Docker on Ubuntu 22.04
- Size > Basic > Regular > $12/mo
- Backups > Enable > Weekly $2.40/mo (probably a good idea, but obviously optional)
- Authentication > SSH key > select one you've created on your computer
- Improved Metrics > Enabled

Setting up an OpenAI account (recommended):
- Sign up at https://platform.openai.com/docs/overview
- (optional) Fund your account your account so you aren't subject to the free trial model and rate-limit constraints.

Setting up DNS (recommended):
- Point your desired domain name (e.g. `brace.tools`) at the IP address of the virtual machine you created above.

Testing remote access to Docker:
- In your computer's terminal, adapt this command for your domain name: `ssh root@brace.tools`
- Once connected via SSH, run `docker version` to verify that Docker is running.

Generate deployment keys (these allow your Docker host to pull from this repository)
- If you don't already already have a `~/.ssh/id_???.pub` file, run `ssh-keygen -t ed25519` to create one.
- Edit the Settings for this repository on GitHub to allow that key read access.

## Deployment

Clone this repository. If you followed the provisioning steps above, you will end up with a folder `/root/brace` containing all of the files in this repository.

Collect your OpenAI credentials (e.g. `OPENAI_AI_KEY`) into `keys.env`. This file is read when stack starts up.

And, while you are in there, make use to populate `oauth.env` with your `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` from Google. (If you need to switch away from Google for authentication, look to update `OPENID_PROVIDER_URL` in `compose.yaml`.)

For test deployments:
- Run `docker network create web` (This creates dummy network. In deployment, you'd provide a real network.)
- Run `docker compose up`

For production deployments:
- Use some other docker stack to provide a `traefik`-based reverse proxy on the `web` network.
- Run `docker compose up -d`
- Monitor the deployment with `docker compose logs -f`

Once running, you can access that chat interface at [http://localhost:3000](http://localhost:3000).

Unfortunately, there are some remaining manual setup steps:
- In OWUI, find Workspace > Models, hide all of the extra models you don't want to see. (Shift-click to hide multiple models at once.)
- Use the `/bist` prompt to check *most* of the expected functionality (e.g. auto-continue, wiki access, fetch access, etc.)
- In the *Valves* for the `Submit Conversation to Canvas` action, be sure that you have your Canvas Access Token and Test Student Id configured properly. Watch out that the test student id is specific to a course, and the id number changes each time ou used the `Reset student view` button in Canvas.

The OAuth stuff is setup to allow authentication with `@ucsc.edu` accounts when the server is running on `localhost:3000`. Contact `amsmith@ucsc.edu` if this needs to change.

## Monitoring

We decided not to integrate [Langfuse](https://langfuse.com/) for continuous monitoring because it involved sharing student conversations with a third party. Instead, here's what we recommend for monitoring:
- In the OWUI Admin Panel, Databases page, use `Export All Chats (All Users)` to get a dump of all activity. The exported chat view gives you anonymous user ids, so you can see how many conversations each user has had, how long they are, what languages they involve, etc.
- Also on the Databases page, you can use `Download Database` to get a copy of the entire databas (in SQLite format). This is useful for debugging and for auditing the system's behavior, but it is definitely not anonymized.

# TODO (to generalize for new courses)

- Document expected usage patterns (e.g. typical number of conversation, turn depth, and token balance)
- Implement enrollment filter?
    - At the start of every conversation, a filter uses a cached view of enrollment to decide if the current user is allowed to proceed with conversation, throw exception to kill convo otherwise.
    - Does this violate our design principle of not proving enrollment in the transcripts? We should check if a conversation that hits an exception on the very first reply even counts as a logged conversation.
- Move course-specific data out of repo
    - `/book` should just be example content under the assumption that future deployments will volume-mount another directory on top of this
    - `brace-system-propmt.md` can already be clobbered externally by filename.
    - think about whether the wiki pages can be pulled from Canvas pages on the fly (e.g. from an unpublished folder so that they aren't visible to students but are visible to )
- Write onboarding instuctions for both instructors and students:
    - Instructors
        - How do I log in? (Basically: press the "Continue with SSO" button. The first user for a deployment becomes the admin user.)
        - How do I alter the system prompt?
            - Temporary: Find `Brace` in the Models page of the OWUI Workspace page. You can edit the system prompt here. This will have an immediate effect, but the changes will be overwritten the next time the system restarts for whatever reason.
            - Permanent: Edit the `brace-system-prompt.md` file in the root directory of this repository. This file is read at startup, so changes will persist across restarts.
        - How do I add new knowledge to the system?
            - Create a new Markdown file in the `book/` directory. The file should be named in a way that makes sense for the content it contains. The file should be linked from the `SUMMARY.md` file in the same directory.
            - The system will automatically load the contents of the `book/` directory at startup, so changes will persist across restarts.

    - Students
        - How do I log in? (Basically: press the "Continue with SSO" button)
        - How do I submit a conversation to Canvas?
            - Press the magic sparkle
            - Provide the URL of the Canvas assignment you are trying to complete
            - Confirm that the system has the right assignment and student
            - Submit!
            - Go back to Canvas to confirm that your submission worked.

# Diagrams

## Architecture

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

## Wiki interaction

```mermaid
sequenceDiagram
    actor U as User
    participant A as Assistant
    participant W as Wiki
    participant L as LLM

    U ->>+ A: "I wanna do Quiz 2."

    critical Wiki setup happens at start of every conversation.
        A ->> W: Load initial instructions
        W ->> A: {introduce ⟨wiki _.md⟩ command syntax}
        W ->> A: {list of all wiki page filenames}
        W ->> A: {contents of README.md}
    end

    
    A ->>+ L: Generate assistant reply
    L -->> A: {streaming response}
    A -->> U: "Sure, let me look up the details.<br/>⟨wiki quizzes/Q2.md⟩"
    L ->>- A: {message complete}

    loop Auto-continue when message ends with "⟩".
        A ->>- U: {message complete}
        U ->>+ A: {continue last assistant message}
    end

    loop Process each ⟨wiki _.md⟩ command<br>in all past assistant messages.
        A ->> W: Load quizzes/Q2.md
        W ->> A: {contents of quizzes/Q2.md}
    end

    A ->>+ L: 
    L ->>- A: 

    A ->>- U: "Quiz 2 is about dog training. Ready to start?"

    U ->>+ A: "Yeah."
    A ->>+ L: 
    L ->>- A: 
    A ->>- U: "Question 1: ..."
```

## Submission flow
```mermaid
sequenceDiagram
    actor U as User
    participant I as Chat Interface
    participant C as Canvas LMS

    U <<-->> I: {authenticate with some institutional email address}
    U <<-->> I: {many conversation turns}

    U ->> I: Click: Submit to Canvas.
    I ->> I: Render conversation as HTML for easy viewing in SpeedGrader
    I ->> U: Status: Gathering information...
    I ->> U: Prompt: Assignment URL?
    U ->> I: "https://canvas/courses/{course_id}/assignments/{assignment_id}"

    par using instructor's credentials
        I ->>+ C: Get all enrolleded students in {course_id}.
        I ->> C: Get details for {assignment_id} in {course_id}.
    end
    C ->>- I: Results (might be cached)

    I ->> I: Try to infer {assignment_name} and {student_name}.

    alt
        I ->> U: Status: Submission failed (user not enrolled).
    else
        I ->> U: Status: Submission failed (assignment not available).
    else
        I ->> U: Confirm: Submit to {assignent_name} as {student_name}?
        alt
            U ->> I: Click: Cancel
            I ->> U: Status: Submission abandoned.
        else
            U ->> I: Click: Okay
            critical using instructor's credentials
                I ->>+ C: Submit on behalf of student.
                C ->>- I: Submission complete.
            end
            I ->> U: Status: Submission complete.
        end
    end
```