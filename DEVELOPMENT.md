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

...

Oh, maybe I can have a Python one-liner run before start.sh that calls `Model.insert_new_model(form, user.id)` in the same way that the back end would do in response to an admin-authenticated post.

This should be fused with the pipeline setup stuff.

Maybe I don't need to use a separate pipeline container for this. I can just `Functions.insert_new_function(user.id, function_type, form_data)` in the same way that the back end would do in response to an admin-authenticated post.

Ah, this is feeling better.

## Auto-continue

Gah, switching to pipelines was trickier than I thought.

It looks like the AUTO_CONTINUE mechanism will need to be implemented as a (filter) Function that runs in the main container because that's the only place I have `__event_emitter__`. Meanwhile, I don't think I can even implement a bug-free version of this yet because the engine doesn't send the continue actions at the right time.

If I'm inserting using `Functions.insert_new_function`, this isn't bad.