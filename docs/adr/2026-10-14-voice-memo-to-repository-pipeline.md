---
domain: voice-memo-export
category: decision
sub-category: adr
topics:
  - automation
  - speakr
  - voice-memos
types:
  - adr
date-created: 2026-10-14
date-revised: 2026-10-14
status: PROPOSED
aliases: []
tags: []
models:
  - claude-opus-5-5
  - claude-sonnet-5-5
providers:
  - Anthropic
session-link: https://claude.ai/code/session_01Az7XTvkfwEd482CHWnDd6R
---

# 2026-10-14-voice-memo-to-repository-pipeline

## context

The owner wants an always-on Mac to turn each Voice Memo into shipped repository work with no manual steps. The flow runs from the recording to a transcript, then to the right project, then to a typed document such as an ADR or a set of work items, then to a commit, a pull request, a merge and cleanup.

The tool must stand alone. It has to run on any machine and for any set of projects, not only the owner's current repositories, so nothing in it may depend on one person's paths, registry or repository layout.

Delivery is incremental. This record and its two companion documents are the first increment and contain no code. Each later increment is its own pull request, built against the design.

## decision

1. Pull requests created by the pipeline auto-merge when the target project's declared gates pass, including pull requests that change code. A project that declares no gates never auto-merges.
2. Saying "approved" in a memo sets a generated ADR to accepted. The record then carries approved-by set to the owner, with the memo id and the quoted words as evidence. This counts as the owner's ruling for that one record only and authorizes nothing else.
3. The orchestrator lives in the voice-memo-export repository. It calls each target repository's own skills and commands through a pluggable headless agent runner, so a project keeps its own templates, numbering and regenerate steps.
4. A memo that cannot be routed to a project with enough confidence goes to a folder the user chooses during setup. Nothing is committed anywhere until the user names a project for that memo.
5. Speakr is an optional connector reached only through its public API. It is never forked, because it is AGPL licensed, releases often, and its watched folder deletes source files.
6. vmea is the source of truth for layered custom instructions (global, project, document type, and spoken in the memo). It syncs them into Speakr tags when the connector is on.
7. Notes are named `yyyy-MM-dd-HH-mm-{project}-{summary}`, where the summary is at most seven words and the time is when the memo was recorded, in local time. Originals in the Voice Memos library are never renamed or moved.
8. Delivery is incremental, one pull request per increment. Parallel subagents on a cheaper model do the build work, and a coordinating session checks their output and is the only one that touches git.

## consequences

### positive

- A spoken thought becomes a reviewed, merged, correctly named document without a manual step, and the owner is notified of the result or the failure reason.
- The tool is portable. Project paths, aliases, profiles and the agent runner all come from one config file, so another person can point it at their own repositories.
- Speakr stays replaceable. Because vmea owns the instructions and uses only the public API, a Speakr upgrade or removal cannot break routing, typing or the git steps.
- Leaving the Voice Memos library untouched means iCloud never syncs a rename back to the phone.
- Each stage has its own interface, so a later increment can replace or test one stage without disturbing the others.

### negative

- Auto-merge makes the declared gates the only check between a memo and the default branch. A weak gate set lets a bad change land, which is why a project without gates is refused.
- Voice approval is only as trustworthy as the transcript. A misheard word could accept a record, so the memo id and quoted words must be kept as evidence that can be audited.
- Saying "approved" is a ruling on one record. It cannot be reused as a standing approval, so each ADR needs its own spoken cue.
- Whether Voice Memos sync to the Mac while the Mac app is closed, and how long a new memo takes to arrive, are unverified. Increment 2 tests both before the capture daemon is built on them.
- The orchestrator depends on each target repository's own commands. A repository whose commands change can stall its memos until the project profile is updated.
- Transcripts may contain sensitive text, so a redaction scan must run before any commit, and audio must never be committed.

## alternatives-considered

- Forking Speakr: rejected because it is AGPL licensed and releases often, so a fork would carry a heavy merge burden and license obligations for little gain.
- Pointing Speakr's watched folder at the Voice Memos library: rejected because that folder deletes source files, which would destroy the originals the Voice Memos app owns.
- Never auto-merging: rejected because it leaves a manual step in every run, which defeats the goal of no manual steps. Declared gates give a bounded check instead.
- Storing instructions only in Speakr: rejected because routing, typing and the git steps run before and outside Speakr, and Speakr is optional.

## related

- [Voice to repository architecture](../design/voice-to-repo-architecture.md)
- [Release readiness review](../reviews/2026-10-14-release-readiness-review.md)
