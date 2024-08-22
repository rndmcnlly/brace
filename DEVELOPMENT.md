# Development



## Knowledge wiki

We should make a `Pipeline` with `self.type = 'filter'` that implements the knowledge wiki system.

Valves: Nothing for now.

Inlet:
- inject stuff into a first role=system message:
    - Some hard-coded instructions for how to use the wiki
    - the contents of `/book/SUMMARY.md`
    - the contents of `/book/System Prompt.md` (as if it were just requested)
- for each assistant message in the history:
    - find page id reference, then inject the corresponding page content
    - if a page id reference is not found, inject a role=system message saying so
- if the last message was a system message (e.g. we are processing a continuation), inject one last role=user message with "..." or whatever as the filler

Outlet: Nothing for now.

## Automatic character import

The current setup instructions require you to import this `characters-models.json` file into the UI manually. This can be skipped during testing if our filters simply run on every pipeline, and you never disable them. I suppose that's fine for a Brace-only setup...

In the future, maybe we can have some script post the JSON file to the backend's `/models/add` endpoint. But with what access token?

Alternatively, we could try to write it to the sqlite database directly. But I don't want my script to need to track schema changes.

## Auto-continue

Gah, switching to pipelines was trickier than I thought.

It looks like the AUTO_CONTINUE mechanism will need to be implemented as a (filter) Function that runs in the main container because that's the only place I have `__event_emitter__`. Meanwhile, I don't think I can even implement a bug-free version of this yet because the engine doesn't send the continue actions at the right time.
