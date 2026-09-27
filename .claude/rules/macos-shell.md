# macos-shell

## binding

Scripts target Apple Silicon macOS with Homebrew in `/opt/homebrew`. Never assume GNU coreutils, `gsed`, or a GNU-only flag; `/bin/bash` is 3.2, and a script that must run under it avoids associative arrays, `mapfile`, and `${var,,}`. Never assume `timeout`, `gtimeout`, `flock`, or `tree` are present. Scripts check required tools at start with `command -v` and exit with a message on a miss; do not discover a missing tool mid-run. PATH resolves `python3` and `pip3` to the framework Python before Homebrew's; invoke Homebrew Python and pip by absolute path or through a project venv. `launchd` plists reference a stable interpreter path, never a versioned framework path.

## rationale

Known divergences: `sed -i ''` (empty backup arg required), `date -j -f` not `date -d`, `stat -f` not `stat -c`, no `grep -P`, no `xargs -d`, `mktemp -d -t <prefix>` needs the template. For in-place edits prefer `perl -pi -e` or Python over `sed -i`.

Locks in shell use atomic `mkdir` with an EXIT trap; locks in Python use `fcntl.flock`. Time-bounded calls use `subprocess.run(timeout=)`. Directory listings use `find . -not -path '*/.git/*' | sort`.

PATH resolves `python3` and `pip3` to `/Library/Frameworks/Python.framework/Versions/<ver>/bin` before `/opt/homebrew/bin`.

After changing a plist or its interpreter: `launchctl bootout gui/$UID <plist>` then `launchctl bootstrap gui/$UID <plist>`, and confirm with `launchctl print`.
