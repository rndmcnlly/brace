# Development


## Submit conversation action

Idea: Offer an Action (a little sparkle in the button bar below a message) to submit the conversation to Canvas.

We know the user's `@ucsc.edu` email address from authentication. However, we'll need to get their Canvas user id. If we have the instructor's access token, we can execute this GraphQL query:

```graphql
query MyQuery {
  course(id: "76391") {
    usersConnection {
      nodes {
        id
        loginId
        name
      }
    }
  }
}
```

When the user presses the sparkle button, we need to use an input box to ask for the assignment URL.

Once we have the assignment url, we can look up the assignment name, figure out the user's name and id, then offer a confirmation box like "Are you sure you want to submit this conversation to the {assignment name} assignment for {user name}?"

We can use status messages to indicate progress, success or failure. In any case, we should never update the conversation content based on the result of this action. Brace should never get causal knowledge of whether the user is enrolled in the course or not, and their user id should never be stored in the conversation history. We can't avoid storing the email address, however, because we need it to authenticate the user in the first place.

## Knowledge wiki (in progress)

We should `Filter` that adjusts chat history before/after LLM completion to implement this.

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

Outlet:
- Trigger the `contine` action via `__event_emitter__` when we see the last assistant message contains a sparkle text.
- Do not return a new `body` (or else it will clobber the old one during continuations)

## Automatic function import

See [functions.json](./functions.json) for a JSON-formatted list of tools to be injected. Compared to OWUI's export format, these are notably missing the `content` field. This will be dynamically populated by a similarly named file in the `function/` directory.

Issue: I'm not sure how to set the `is_active` field in a way that sticks. This is important because the function (e.g. a `Filter`) will not run even if the model is configured to use it when it is not active (or "enabled").

## Automatic character import

See [models.json](./models.json) for a JSON-formatted list of characters to be injected. These are in the same format that you would export from OWUI. Note the inclusion of a `filterIds` to rig up the Brace model to the knowledge wiki filter (incomplete).