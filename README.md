# AutoFlow

A small Streamlit app that turns a plain-English task into a workflow on an [n8n](https://n8n.io) instance, using an LLM and n8n's REST API.

> Example task: *"Create a workflow that sends an email when a new tweet is posted"*

## The problem

Asking an LLM to write a complete n8n workflow as raw JSON fails in predictable ways: it invents node types that don't exist, mangles the `connections` structure, and forgets required settings. In an early notebook experiment (`notebook.ipynb`), the model was given a short list of node types and a task, and it made up node types such as `commentCheckNode` and `sendReplyNode`.

## How it works

AutoFlow gives the model a small Python interface instead of asking for JSON, and runs it as a four-step pipeline:

1. **Plan.** The model writes a plan for the task: which trigger, which nodes, and how they connect.
2. **Generate.** Given the plan, it writes Python that uses only two helper functions:
   - `create_node(name, position, type, parameters)` builds a valid node object.
   - `create_workflow(name, nodes, connections)` assembles the workflow, fills in the workflow settings, and POSTs it to the n8n API.
3. **Check.** A second model call reads the generated code and answers `safe` or `unsafe`, depending on whether it calls anything other than those two helpers.
4. **Execute.** Safe code is run and the workflow appears in n8n. If the code is flagged, it is shown to the user, who has to confirm before it runs.

`n8n_nodes_docs.txt` is included in the prompt as a reference. It lists node types with a short description, connection type, and parameters, so the model works from real node types and parameter formats instead of guessing. It currently covers a handful of nodes (manual and chat triggers, email, LLM chain, Google Sheets, Airtable, Hugging Face, Google Calendar, HubSpot).

## Run it

```bash
pip install streamlit openai requests
```

Create `keys.json` (it is gitignored):

```json
{
  "OPEN_AI_KEY": "sk-...",
  "N8N_KEY": "your n8n API key"
}
```

In `main.py`, set the `url` in `create_workflow` to your own n8n instance's API base URL and update the `errorWorkflow` ID and `timezone` in the workflow settings. Then:

```bash
streamlit run main.py
```

## Limitations

This is a prototype.

- **It executes model-generated code with `exec()`.** The safety check is another LLM call, which is a useful filter but not a security boundary. Run it only against a test n8n instance.
- **There is no feedback loop.** If n8n rejects a workflow, the error is printed but not passed back to the model, so it cannot repair its own output.
- **Node coverage is small.** The model can only be relied on for the nodes documented in `n8n_nodes_docs.txt`.
- **Some settings are hardcoded** (instance URL, error workflow, timezone), as noted above.
- It uses `gpt-4o-mini` for all three steps and has not been evaluated beyond manual testing.

## Files

| File | Purpose |
|---|---|
| `main.py` | The Streamlit app and the plan, generate, check, execute pipeline |
| `n8n_nodes_docs.txt` | Node reference included in the model's prompt |
| `notebook.ipynb` | Early experiments: API calls, node helpers, first end-to-end run |
