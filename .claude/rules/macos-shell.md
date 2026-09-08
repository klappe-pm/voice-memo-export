paths:
  - "**/*.sh"
  - "**/*.py"
  - "scripts/**"
  - "hooks/**"

# macos-shell

Environment: Apple Silicon macOS, Homebrew in `/opt/homebrew`, no GNU coreutils, no `gsed`.

`/bin/bash` is 3.2. Scripts use `#!/usr/bin/env bash` and assume Homebrew bash; if a script must run under `/bin/bash`, no associative arrays, `mapfile`, or `${var,,}`.

No GNU-only flags. Known divergences: `sed -i ''` (empty backup arg required), `date -j -f` not `date -d`, `stat -f` not `stat -c`, no `grep -P`, no `xargs -d`, `mktemp -d -t <prefix>` needs the template. For in-place edits prefer `perl -pi -e` or Python over `sed -i`.

Absent binaries: `timeout`, `gtimeout`, `flock`, `tree`. Locks in shell use atomic `mkdir` with an EXIT trap; locks in Python use `fcntl.flock`. Time-bounded calls use `subprocess.run(timeout=)`. Directory listings use `find . -not -path '*/.git/*' | sort`.

Scripts check required tools at start with `command -v` and exit with a message on a miss; do not discover missing tools mid-run.

PATH resolves `python3` and `pip3` to `/Library/Frameworks/Python.framework/Versions/<ver>/bin` before `/opt/homebrew/bin`. Invoke Homebrew Python and its pip by absolute path or through a project venv; never assume bare `python3` is Homebrew's.

`launchd plists` reference a stable interpreter path (`/opt/homebrew/bin/python3` or `<project>/.venv/bin/python`), never a versioned framework path. After changing a plist or its interpreter: `launchctl bootout gui/$UID <plist>` then `launchctl bootstrap gui/$UID <plist>`, and confirm with `launchctl print`.