# docs-provenance-frontmatter

## binding

Every Markdown file an agent creates or content-revises under a `docs/` directory carries three frontmatter keys recording the agent session that produced it: `models`, `providers`, and `session-link`. The agent populates them from the session it is running in, on every content write, without being asked.

## the-keys

The keys sit after `tags:` with the other file-specific keys, sorted A to Z per `markdown-style`:

```yaml
models:
  - claude-fable-5-1
providers:
  - Anthropic
session-link: https://claude.ai/code/<session-id>
```

- `models`: the model ids the session ran on, including the model of any dispatched subagent that wrote into the file. Array, deduped, sorted case-insensitively.
- `providers`: the provider of each model in `models`: Anthropic, OpenAI, Google, and so on. Array, same rules.
- `session-link`: the web link to the session that made the write. Claude Code, claude.ai, ChatGPT, Codex, and Gemini expose one. Where the runtime exposes no link (Cursor, OpenCode), write `session-link: ""`. Never omit the key.

## when-a-file-is-revised

A later session that changes the file's content appends its models and providers to the arrays and replaces `session-link` with its own link. The frontmatter therefore names every model that has touched the body and the session that last did. `date-revised` updates in the same write.

## scope

Applies to every path matching `**/docs/**/*.md`, in every repository, on every runtime, when the file's content was composed by an agent or captured from an agent session. That covers files the agent writes through an edit tool and files written by generators and hooks the agent runs, such as `hooks/prompt-capture.sh` writing `docs/prompts/` and the explain-mode skill writing `docs/questions/`. A generator populates the keys from the session facts its payload carries and writes the empty spelling for the rest: `models: []`, `session-link: ""`.

A page rendered wholesale from repository source on every sync is not covered. Its provenance is the generator named in the page, not a session, and adding session keys to it would be overwritten by the next regeneration. The repository currently holds no such page under `docs/`: the script reference that was the standing example was generated content nobody read, so it and its generator were retired rather than maintained. The carve-out stays for the next generator that earns one.

Files that exist before this rule lands gain the keys on their next content write. There is no backfill: a past session's link is not recoverable from the file.

## relationship-to-other-rules

`no-agent-attribution` forbids a session permalink in authored output. These keys are provenance metadata, not authorship credit: they name the tool that ran, the way `date-created` names the day and not the person. That rule carves out the frontmatter of a docs file for these three keys and nothing else, under its `provenance-exception` section. The link never appears in the body, in a commit message, or in a pull request. `markdown-style` governs key order and array shape. `output-format-contract` still applies: these keys are added to a contracted format, never in place of a key it requires.
