---
domain: voice-memo-export
category: guides
sub-category: setup
topics:
  - full-disk-access
  - icloud
  - voice-memos
types:
  - guide
date-created: 2026-10-20
date-revised: 2026-10-20
status: DRAFT
aliases: []
tags: []
models:
  - claude-sonnet-5-5
providers:
  - Anthropic
session-link: https://claude.ai/code/session_01Az7XTvkfwEd482CHWnDd6R
---

# find-your-recordings

## purpose

vmea needs to read the folder where the Voice Memos app keeps your recordings. This guide shows how to find that folder, what each result means, and how to fix the usual problems. Run `vmea probe` first. It does the searching for you and explains the result in plain words.

## run-the-probe

```bash
vmea probe
```

The probe checks every place Voice Memos is known to keep recordings and gives each one a state.

| State | Meaning |
|-------|---------|
| readable | The folder can be read and holds recordings. The probe shows how many and when the newest one was made. |
| empty | The folder can be read but holds no recordings yet. |
| blocked | The folder is there but macOS will not let vmea read it. This is the Full Disk Access case. |
| missing | Nothing is at that location on this Mac. |

If more than one readable folder is found, the probe chooses the one with the most recordings and tells you the others, so you can confirm it picked the right one. A result looks like this: `Found 312 recordings, newest from yesterday 4:12 pm`.

`vmea doctor` shows the same states and the chosen folder as part of its health check.

## when-no-known-folder-works

If none of the known places is readable, the probe asks Spotlight for other folders that hold Voice Memos audio or a `CloudRecordings.db` file, and ranks what it finds by recording count and then by the newest recording. This covers a macOS version that moved the folder. Spotlight only exists on a Mac, so on other systems the probe says the search is not available. Use `vmea probe --no-spotlight` to skip it.

## fix-a-blocked-folder

A blocked folder means vmea has no Full Disk Access. The probe prints what to do, and the same details appear in the JSON output.

1. Open the Full Disk Access pane. Run `open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`, or open System Settings, then Privacy & Security, then Full Disk Access.
2. Click the plus button and add the Python interpreter the probe names. In the file picker press Command Shift G and paste the path.
3. If you run vmea from a terminal, also turn on that terminal app, such as Terminal or iTerm. macOS checks the app that started the command.
4. Switch each entry on, quit and reopen the terminal, then run `vmea probe` again.

The probe shows the resolved interpreter path, which is the real program behind any virtual environment. The background agent installed by `vmea daemon install` runs the interpreter that was active when you installed it. If that is a different Python from the one you use in the terminal, add that one too.

## fix-recordings-that-stopped-arriving

If the newest recording is older than seven days, the probe warns you and lists the iCloud steps. You can change the limit with `vmea probe --stale-days 14`. The steps are these.

1. On your iPhone, open Settings, tap your name, tap iCloud, tap Show All, and turn on Voice Memos.
2. On your Mac, open System Settings, click your name, click iCloud, and turn on Voice Memos.
3. Use the same Apple Account on both devices and stay on Wi-Fi.
4. Open the Voice Memos app on the Mac and leave it open for a minute so it can catch up.
5. Record a short test memo on your iPhone, then run `vmea probe` again to see if it arrives.

## use-the-result-in-scripts

```bash
vmea probe --json
```

The command prints one JSON document with the chosen folder, every folder checked, the Spotlight result, the Full Disk Access details and the sync check. It exits with status 1 when no readable folder was found, so a script can stop there.

## what-the-probe-never-does

It never changes a permission, opens System Settings for you, writes a file, or follows a link out of a recordings folder. A folder with a very large number of files is read only up to a fixed limit, and the count is then shown as a minimum.

## still-stuck

If you do not want to grant Full Disk Access, set a folder yourself with `vmea init`, and share memos into it from the Voice Memos app. See [troubleshooting](../TROUBLESHOOTING.md) for other problems.
