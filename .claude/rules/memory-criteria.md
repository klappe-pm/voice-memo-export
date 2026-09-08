# memory-criteria

Applies to `~/.claude/projects/<project>/memory/` auto-memory and to any analogous per-project memory store written across sessions.

## include

- Toolchain conventions (test commands, lint configs, build incantations).
- Past gotchas with their resolutions.
- Style, voice, and branding conventions specific to the user.
- External constraints (API limits, character caps, vendor rules).
- In-progress task state that must survive a session boundary.

## exclude

- Session work logs.
- What this session did to the workstation: what was installed, diagnosed, reinstalled, or repaired, and the path that got there. A durable convention learned along the way is still an include, but it is written as the convention and never as the story of finding it.
- One-off research findings.
- Duplicates of content already in CLAUDE.md or `~/.claude/rules/`.
- Unverified hypotheses or speculation.

The test is whether the next session needs the fact or the narrative. `obsidian version reports the running asar, CFBundleShortVersionString reports the bundle` is a fact worth keeping. `the Obsidian CLI was broken and here is how it got fixed` is a session log, not a memory.

## store-availability

A memory store that is absent, permission-denied, or otherwise unwritable is never reported in session output. Drop the attempt silently.

Surfacing the failure spends the user's attention on a store they did not ask about. Saying so is noise that reads as an unresolved problem.

## size-limit

Soft cap: 200 lines in MEMORY.md. Beyond the cap, extract topics to separate `.md` files in the same memory directory and reference them from MEMORY.md by relative link.
