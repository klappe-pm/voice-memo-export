#!/usr/bin/env python3
"""Detect a shell command that prints a process, shell or launchd environment.

Backs hooks/env-dump-guard.sh and the enforcement section of
rules/no-secret-exposure.md. An environment dump carries every live key the
environment holds into the agent transcript: on 2026-09-26 a routine
`launchctl print gui/501/<label>` printed six provider keys from the launchd
global environment (docs/bugs/launchctl-print-exposed-launchd-environment-keys.md).

The detector parses the command the way a shell would split it, far enough to
find each simple command: pipes, `&&`, `;`, newlines, subshells, `$(...)` and
backticks, heredocs, here-strings and `echo ... |` text a shell reads, and
the wrappers that run another command (`bash -c`, `eval`, `env VAR=val cmd`,
`env -S`, `sudo`, `doas`, `command`, `exec`, `nohup`, `time`, `nice`,
`timeout`, `stdbuf`, `unbuffer`, `script`, `watch`, `xargs`, `find -exec`,
`ssh host cmd`, `railway ssh --`, `railway run`, `op run --`,
`credentials.py run --`, `llm-auth run --`, `docker exec`, `docker run`,
`docker compose exec`, `kubectl exec --`). A simple command is denied when it
is one of:

- `env` with no command to run (`env`, `env -i`, `env VAR=x`), and `printenv`
  in any form, since `printenv NAME` prints a value.
- bare `set`; `export` with no name (`export`, `export -p`); `declare` or
  `typeset` with no name, or with `-p`; `readonly` or `local` with no name,
  or with `-p`.
- `launchctl print`, `getenv`, `export`, `procinfo` or `dumpstate`.
- `ps` asking for the environment: `-E` in a dash option cluster, or an `e`
  in a BSD-style option word (`ps e`, `ps eww`, `ps aux e`). On macOS `-e` is
  identical to `-A` (every process), so `ps -e` and `ps -eo pid,command` pass;
  `man ps` on Darwin 25: "-E Display the environment as well." and "-e
  Identical to -A.", and in the BSD-style list "e Display the environment as
  well. Same as -E."
- any reference to `/proc/<pid>/environ`, as an argument or a redirection.
- `railway variables` (also `variable`, `vars`), which prints values.
- `docker inspect` or `docker <object> inspect` (and podman), which print Env,
  unless a `--format` template selects neither Env, Config nor the whole object.
- `security find-generic-password` or `find-internet-password` with `-w` or
  `-g`, and `security dump-keychain -d`, which print secrets.

Modes (stdin in, one label or nothing on stdout, exit 0; exit 64 on a bad mode):
  env-dump-detect.py detect            the command text
  env-dump-detect.py detect-payload    a PreToolUse hook payload (JSON)

A payload is judged when its tool_input carries a `command` (or `cmd`),
whatever the tool is called: Bash (Claude Code, Codex, the OpenCode bridge),
run_shell_command (Gemini CLI), Shell (Cursor), Monitor, or an MCP server's
process tool. A detector exception falls back to a raw-text scan, never to
silence, because the guard allows whatever this prints nothing for.
"""

import json
import os
import re
import shlex
import sys

_MAX_DEPTH = 8
_PUNCTUATION = ";&|()<>\n"
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PROC_ENVIRON = re.compile(r"/proc/[^/\s]+/environ")
_SHELLS = frozenset({"bash", "sh", "zsh", "dash", "ksh", "fish"})
_HEREDOC_RECEIVERS = _SHELLS | {"ssh", "railway", "kubectl", "docker", "podman", "eval", "xargs"}
# Shell options that take the next word as their value.
_SHELL_VALUE_OPTIONS = frozenset({"-o", "+o", "-O", "+O", "--rcfile", "--init-file"})
# Words that open a compound command or negate one; the command follows them.
_LEADING_KEYWORDS = frozenset({"{", "}", "!", "if", "then", "elif", "else", "while", "until", "do", "done", "fi"})

# Options that take the next word as their value, per command.
_PS_VALUE_OPTIONS = frozenset({"-o", "-O", "-p", "-u", "-U", "-g", "-G", "-t", "-k", "-M", "-N", "-q", "-s",
                               "--format", "--sort", "--pid", "--ppid", "--user", "--group", "-C"})
_SECURITY_VALUE_FLAGS = frozenset("acCDGjlrstdkpP")
_DOCKER_GLOBAL_VALUE_OPTIONS = frozenset({"--context", "-c", "-H", "--host", "--config", "-l", "--log-level"})
_DOCKER_VALUE_OPTIONS = frozenset({
    "-e", "--env", "--env-file", "-u", "--user", "-w", "--workdir", "--detach-keys", "-v", "--volume",
    "-p", "--publish", "--name", "--network", "--entrypoint", "--platform", "-l", "--label", "--mount",
    "-h", "--hostname", "--add-host", "--cpus", "-m", "--memory", "--restart", "--pull", "--log-driver",
    "--index",
})
# A --format template that selects the environment or the whole object.
_DOCKER_WIDE_FORMAT = re.compile(r"Env|Config|\{\{\s*(json\s+)?\.\s*\}\}", re.IGNORECASE)
_RAILWAY_VALUE_OPTIONS = frozenset({"-s", "--service", "-e", "--environment", "-p", "--project"})
_SSH_VALUE_OPTIONS = frozenset("-" + letter for letter in "bcDEeFIiJLlmOoPpQRSWw")

# Used when the command cannot be tokenized (unbalanced quotes), or when the
# detector raises: the high-signal forms, matched on the raw text so a broken
# quote or a detector bug cannot hide one.
_FALLBACK = (
    ("printenv", re.compile(r"(^|[\s;&|(`$])printenv\b")),
    ("launchctl print/getenv/export", re.compile(r"\blaunchctl\s+(print|getenv|export|procinfo|dumpstate)(\s|$)")),
    ("/proc/<pid>/environ", _PROC_ENVIRON),
    ("railway variables", re.compile(r"\brailway\b[^\n;|&]*\s(variables|variable|vars)(\s|$)")),
    ("docker inspect", re.compile(r"\b(docker|podman)\b[^\n;|&]*\sinspect(\s|$)")),
)


def _strip_comments(text):
    """Remove shell comments: a # at a word start, outside quotes, to end of line."""
    out = []
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch == "\\" and i + 1 < len(text):
            out.append(ch)
            out.append(text[i + 1])
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "#" and (i == 0 or text[i - 1] in " \t\n;&|()"):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _lex(text):
    """shlex tokens with operators as their own tokens; raises ValueError."""
    lexer = shlex.shlex(text, posix=True, punctuation_chars=_PUNCTUATION)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _heredocs(line):
    """(delimiter, body_is_commands) for each heredoc operator on one line.

    Only a real `<<` operator counts: one inside quotes lexes as part of a
    word, and a line with arithmetic `((` is skipped. The body is judged as
    commands when any word on the line is something that runs its input or a
    command (a shell, ssh, docker, kubectl, railway, eval, xargs), so
    `sudo -u root bash <<EOF` and `cat <<EOF | sh` are judged while
    `git commit -F - <<'EOF'` is data.
    """
    if "((" in line:
        return []
    try:
        tokens = _lex(line)
    except ValueError:
        return []
    receives = any(os.path.basename(t) in _HEREDOC_RECEIVERS for t in tokens if not _is_operator(t))
    found = []
    for i, token in enumerate(tokens[:-1]):
        if token == "<<" and not _is_operator(tokens[i + 1]):
            delimiter = tokens[i + 1].lstrip("-")
            if delimiter:
                found.append((delimiter, receives))
    return found


def _drop_heredoc_bodies(text):
    """Drop heredoc bodies that are data; keep the ones that run as commands.

    `cat <<EOF` and `git commit -F - <<'EOF'` feed text, and a line of that
    text reading `set` is not a command. `bash <<EOF` and `ssh host <<EOF`
    feed commands, so their bodies are kept and judged. A heredoc whose
    delimiter never arrives was a misreading, so the text is kept whole.
    """
    if "<<" not in text:
        return text
    lines = text.split("\n")
    out = []
    pending = []
    for line in lines:
        if pending:
            delimiter, keep = pending[0]
            if line.strip() == delimiter:
                pending.pop(0)
                out.append("")
            else:
                out.append(line if keep else "")
            continue
        out.append(line)
        pending.extend(_heredocs(line))
    return text if pending else "\n".join(out)


def _tokens(command):
    """Shell tokens with operators kept as their own tokens, or None."""
    command = command.replace("\\\n", " ")
    # ANSI-C quoting: $'env' is the word env. shlex would read $env.
    command = command.replace("$'", "'")
    command = _drop_heredoc_bodies(_strip_comments(command))
    try:
        return _lex(command)
    except ValueError:
        return None


def _is_operator(token):
    return bool(token) and all(ch in _PUNCTUATION for ch in token)


def _segments(tokens):
    """Split tokens into simple commands.

    Each segment is (argv, every_word, herestrings, piped): argv has
    redirections and their targets removed; every_word keeps the targets
    too, so a read of /proc/<pid>/environ through `<` is still seen;
    herestrings holds each `<<<` word; piped is True when a `|` feeds the
    segment the previous one's output.
    """
    segments = []
    argv, words, herestrings = [], [], []
    piped = False
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if _is_operator(token):
            redirect = ("<" in token or ">" in token) and "(" not in token and ")" not in token
            if redirect:
                # `2>&1` lexes as 2, >&, 1: the descriptor number belongs to
                # the redirection, not to the command's arguments.
                if argv and argv[-1].isdigit():
                    argv.pop()
                if i + 1 < len(tokens) and not _is_operator(tokens[i + 1]):
                    words.append(tokens[i + 1])
                    if token == "<<<":
                        herestrings.append(tokens[i + 1])
                    i += 1
                i += 1
                continue
            if argv or words:
                segments.append((argv, words, herestrings, piped))
            argv, words, herestrings = [], [], []
            piped = token in ("|", "|&")
            i += 1
            continue
        argv.append(token)
        words.append(token)
        i += 1
    if argv or words:
        segments.append((argv, words, herestrings, piped))
    return segments


def _substitutions(word):
    """The text of each $(...) and `...` inside one word."""
    found = []
    i = 0
    while i < len(word):
        if word.startswith("$(", i):
            depth, j = 1, i + 2
            while j < len(word) and depth:
                if word[j] == "(":
                    depth += 1
                elif word[j] == ")":
                    depth -= 1
                j += 1
            found.append(word[i + 2 : j - 1] if depth == 0 else word[i + 2 :])
            i = j
        elif word[i] == "`":
            j = word.find("`", i + 1)
            if j < 0:
                found.append(word[i + 1 :])
                break
            found.append(word[i + 1 : j])
            i = j + 1
        else:
            i += 1
    return found


def _skip_options(args, with_value=frozenset()):
    """Index of the first operand after leading options.

    with_value names options that consume the next word, alone (`-u root`)
    or ending a cluster (`-Eu root`). A `--` ends the options and is skipped.
    """
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            return i + 1
        if not arg.startswith("-") or arg == "-":
            return i
        clustered = len(arg) > 2 and not arg.startswith("--") and ("-" + arg[-1]) in with_value
        if arg in with_value or clustered:
            i += 2
            continue
        i += 1
    return i


def _after_double_dash(args):
    return args[args.index("--") + 1 :] if "--" in args else None


def _check_env(args, depth):
    if args and args[0] in ("--version", "--help"):
        return ""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            i += 1
            break
        if arg in ("-u", "-C", "-P", "--unset", "--chdir"):
            i += 2
            continue
        if arg in ("-S", "--split-string"):
            if i + 1 < len(args):
                return _check_command(args[i + 1] + " " + " ".join(shlex.quote(a) for a in args[i + 2 :]), depth + 1)
            return ""
        if arg.startswith("--split-string="):
            return _check_command(arg.split("=", 1)[1], depth + 1)
        if arg.startswith("-"):
            i += 1
            continue
        break
    while i < len(args) and _ASSIGNMENT.match(args[i]):
        i += 1
    rest = args[i:]
    if not rest:
        return "env with no command to run"
    return _check_argv(rest, depth + 1)


def _check_ps(args):
    value_options = _PS_VALUE_OPTIONS
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            i += 2 if arg in value_options else 1
            continue
        if arg.startswith("-") and len(arg) > 1:
            letters = arg[1:]
            consumes_next = False
            for position, letter in enumerate(letters):
                if letter == "E":
                    return "ps -E (process environment)"
                if ("-" + letter) in value_options:
                    # The rest of the cluster is the value (-opid), or, when
                    # the option ends the cluster (-eo), the next word is.
                    consumes_next = position == len(letters) - 1
                    break
            i += 2 if consumes_next else 1
            continue
        # BSD-style option word, with no dash: ps aux, ps eww, ps aux e.
        if arg.isalpha() and "e" in arg:
            return "ps e (process environment)"
        i += 1
    return ""


def _check_security(args):
    # Global options (-i, -v, -q, -p prompt) come before the subcommand.
    j = _skip_options(args, {"-p"})
    if j >= len(args):
        return ""
    sub = args[j]
    rest = args[j + 1 :]
    value_flags = _SECURITY_VALUE_FLAGS
    if sub in ("find-generic-password", "find-internet-password"):
        i = 0
        while i < len(rest):
            arg = rest[i]
            if arg.startswith("-") and len(arg) > 1 and not arg.startswith("--"):
                letters = arg[1:]
                for position, letter in enumerate(letters):
                    if letter in ("w", "g"):
                        return f"security {sub} -{letter} (prints the secret)"
                    if letter in value_flags:
                        # The rest of the cluster, or the next word, is its value.
                        if position == len(letters) - 1:
                            i += 1
                        break
            i += 1
        return ""
    if sub == "dump-keychain" and any(a.startswith("-") and "d" in a[1:] for a in rest):
        return "security dump-keychain -d (prints secrets)"
    return ""


def _check_docker(cmd, args, depth):
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in _DOCKER_GLOBAL_VALUE_OPTIONS else 1
    if i >= len(args):
        return ""
    sub = args[i]
    rest = args[i + 1 :]
    if sub in ("container", "compose", "image", "service") and rest:
        sub, rest = rest[0], rest[1:]
    if sub == "inspect":
        return _check_docker_inspect(cmd, rest)
    if sub in ("exec", "run"):
        # `docker exec c cmd`, `docker run img cmd`, `docker compose exec svc
        # cmd`: skip the options, then the container, image or service.
        j = _skip_options(rest, _DOCKER_VALUE_OPTIONS)
        if j < len(rest):
            return _check_argv(rest[j + 1 :], depth + 1)
    return ""


def _check_docker_inspect(cmd, args):
    """`docker inspect` prints Env; a narrow --format query does not."""
    fmt = None
    for i, arg in enumerate(args):
        if arg in ("-f", "--format") and i + 1 < len(args):
            fmt = args[i + 1]
        elif arg.startswith("--format="):
            fmt = arg.split("=", 1)[1]
    if fmt is not None and not _DOCKER_WIDE_FORMAT.search(fmt):
        return ""
    return f"{cmd} inspect (prints Env)"


def _check_railway(args, depth):
    j = _skip_options(args, _RAILWAY_VALUE_OPTIONS)
    if j >= len(args):
        return ""
    sub, rest = args[j], args[j + 1 :]
    if sub in ("variables", "variable", "vars"):
        return "railway variables (prints values)"
    if sub in ("ssh", "run", "shell"):
        tail = _after_double_dash(rest)
        if tail is None and sub == "run":
            k = _skip_options(rest, _RAILWAY_VALUE_OPTIONS)
            tail = rest[k:]
        if tail:
            return _check_argv(tail, depth + 1)
    return ""


def _check_ssh(args, depth):
    with_value = _SSH_VALUE_OPTIONS
    j = _skip_options(args, with_value)
    # j is the host; everything after it is the remote command, which the
    # remote shell parses again.
    remote = args[j + 1 :]
    # OpenSSH also reads options after the host (`ssh host -t cmd`).
    remote = remote[_skip_options(remote, with_value):]
    if remote:
        return _check_command(" ".join(remote), depth + 1)
    return ""


def _shell_script(args):
    """For a shell's arguments: ("c", text) for -c, ("stdin", None) when it
    reads commands from standard input, ("file", None) for a script file."""
    i = 0
    reads_stdin_flag = False
    while i < len(args):
        arg = args[i]
        if arg == "--":
            return ("file", None) if i + 1 < len(args) and not reads_stdin_flag else ("stdin", None)
        if arg in _SHELL_VALUE_OPTIONS:
            i += 2
            continue
        if arg[:1] in ("-", "+") and len(arg) > 1 and not arg.startswith("--"):
            if "c" in arg[1:]:
                return ("c", args[i + 1] if i + 1 < len(args) else "")
            if "s" in arg[1:]:
                reads_stdin_flag = True
            i += 1
            continue
        if arg.startswith("--"):
            i += 1
            continue
        return ("stdin", None) if reads_stdin_flag else ("file", None)
    return ("stdin", None)


def _check_shell(args, depth):
    kind, text = _shell_script(args)
    return _check_command(text, depth + 1) if kind == "c" and text else ""


def _reads_stdin_shell(argv):
    """True when this simple command is a shell reading commands from stdin."""
    argv = _strip_leading(argv)
    return bool(argv) and os.path.basename(argv[0]) in _SHELLS and _shell_script(argv[1:])[0] == "stdin"


def _strip_leading(argv):
    argv = list(argv)
    while argv and (argv[0] in _LEADING_KEYWORDS or _ASSIGNMENT.match(argv[0])):
        argv = argv[1:]
    return argv


def _check_argv(argv, depth):
    """Judge one simple command, given as its words."""
    if depth > _MAX_DEPTH:
        return ""
    argv = _strip_leading(argv)
    if not argv:
        return ""
    cmd = os.path.basename(argv[0])
    args = argv[1:]

    if cmd == "printenv":
        return "printenv"
    if cmd == "env":
        return _check_env(args, depth)
    if cmd == "set":
        return "set with no arguments" if not args else ""
    if cmd == "export":
        return "export with no name" if not [a for a in args if not a.startswith("-")] else ""
    if cmd in ("declare", "typeset"):
        flags = "".join(a[1:] for a in args if a[:1] in ("-", "+") and len(a) > 1)
        operands = [a for a in args if a[:1] not in ("-", "+")]
        if "p" in flags:
            return f"{cmd} -p"
        if not operands and not (flags and set(flags) <= set("fF")):
            return f"{cmd} with no name"
        return ""
    if cmd in ("readonly", "local"):
        flags = "".join(a[1:] for a in args if a[:1] == "-" and len(a) > 1)
        if "p" in flags or not [a for a in args if not a.startswith("-")]:
            return f"{cmd} listing variables"
        return ""
    if cmd == "launchctl":
        if args and args[0] in ("print", "getenv", "export", "procinfo", "dumpstate"):
            return f"launchctl {args[0]}"
        return ""
    if cmd == "ps":
        return _check_ps(args)
    if cmd == "railway":
        return _check_railway(args, depth)
    if cmd in ("docker", "podman"):
        return _check_docker(cmd, args, depth)
    if cmd == "security":
        return _check_security(args)
    if cmd in _SHELLS:
        return _check_shell(args, depth)
    if cmd == "eval":
        return _check_command(" ".join(args), depth + 1)
    if cmd == "ssh":
        return _check_ssh(args, depth)
    if cmd in ("sudo", "doas"):
        j = _skip_options(args, {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U", "-r", "-t"})
        return _check_argv(args[j:], depth + 1)
    if cmd == "command" and any(a in ("-v", "-V") for a in args[:2]):
        # `command -v env` looks a name up; it runs nothing.
        return ""
    if cmd in ("command", "builtin", "exec", "nohup", "time", "noglob", "caffeinate", "stdbuf", "unbuffer"):
        j = _skip_options(args, {"-a", "-t", "-w"})
        return _check_argv(args[j:], depth + 1)
    if cmd == "script":
        # script [-q] [-t time] file command...
        j = _skip_options(args, {"-t", "-T", "-F"})
        return _check_argv(args[j + 1 :], depth + 1)
    if cmd == "find":
        for k, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                inner = []
                for word in args[k + 1 :]:
                    if word in (";", "+"):
                        break
                    inner.append(word)
                label = _check_argv(inner, depth + 1)
                if label:
                    return label
        return ""
    if cmd == "nice":
        j = _skip_options(args, {"-n"})
        return _check_argv(args[j:], depth + 1)
    if cmd in ("timeout", "gtimeout"):
        j = _skip_options(args, {"-s", "-k", "--signal", "--kill-after"})
        return _check_argv(args[j + 1 :], depth + 1)
    if cmd == "xargs":
        j = _skip_options(args, {"-n", "-I", "-J", "-L", "-P", "-s", "-E", "-d", "-R", "-S"})
        return _check_argv(args[j:], depth + 1)
    if cmd == "watch":
        j = _skip_options(args, {"-n", "--interval"})
        return _check_command(" ".join(args[j:]), depth + 1)
    runs_after_dashes = cmd in ("op", "kubectl", "llm-auth", "credentials.py") or (
        cmd.startswith("python") and args and os.path.basename(args[0]) == "credentials.py"
    )
    if runs_after_dashes:
        tail = _after_double_dash(args)
        return _check_argv(tail, depth + 1) if tail else ""
    return ""


def _check_command(command, depth=0):
    """Label of the first environment dump in a command string, else ""."""
    if depth > _MAX_DEPTH or not command.strip():
        return ""
    tokens = _tokens(command)
    if tokens is None:
        return _fallback(command)
    previous = []
    for argv, words, herestrings, piped in _segments(tokens):
        for word in words:
            if _PROC_ENVIRON.search(word):
                return "/proc/<pid>/environ"
        label = _check_argv(argv, depth)
        if label:
            return label
        for word in words:
            for inner in _substitutions(word):
                label = _check_command(inner, depth + 1)
                if label:
                    return label
        if _reads_stdin_shell(argv):
            # `bash <<< printenv`, `echo env | sh`: the text a shell reads
            # from standard input is a command.
            fed = list(herestrings)
            source = _strip_leading(previous)
            if piped and source and os.path.basename(source[0]) in ("echo", "printf"):
                fed.append(" ".join(a for a in source[1:] if a not in ("-n", "-e", "-E")))
            for text in fed:
                label = _check_command(text.replace("\\n", "\n"), depth + 1)
                if label:
                    return label
        previous = argv
    return ""


def _fallback(text):
    """The high-signal forms matched on raw text, for input the parser cannot read."""
    for label, pattern in _FALLBACK:
        if pattern.search(text):
            return label
    return ""


# shlex builds a token one character at a time, so a long word costs time
# that grows with the square of its length: a 450 000 character command ran
# past the guard's 3 second timeout, and a hook that times out does not deny.
# A command this large is denied unread rather than judged too late.
_MAX_COMMAND = 64 * 1024


def detect(command):
    """Public entry: the label for a command string, or ""."""
    command = command or ""
    if len(command) > _MAX_COMMAND:
        return f"command over {_MAX_COMMAND // 1024} KiB, too large to judge"
    return _check_command(command)


def command_of(payload):
    """The shell command a PreToolUse payload would run, or None.

    Any tool whose input carries a `command` (or Codex's `cmd`) is judged,
    whatever the tool is called: the shell tool is Bash, run_shell_command
    or Shell by runtime, and other tools run a shell command too (Monitor, an
    MCP server's start_process). A list-form command is joined as argv.
    """
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    for key in ("command", "cmd"):
        command = tool_input.get(key)
        if isinstance(command, list):
            return shlex.join(str(part) for part in command)
        if isinstance(command, str):
            return command
    return None


def detect_in_payload(payload):
    return detect(command_of(payload))


def _main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode not in ("detect", "detect-payload"):
        sys.stderr.write("usage: env-dump-detect.py detect|detect-payload\n")
        return 64
    text = sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape")
    try:
        if mode == "detect":
            label = detect(text)
        else:
            try:
                payload = json.loads(text or "{}")
            except ValueError:
                payload = {}
            label = detect_in_payload(payload)
    except Exception:  # noqa: BLE001 - a detector bug must not fail open
        # The guard allows whatever this prints nothing for, so an exception
        # falls back to the raw-text scan rather than to silence.
        label = _fallback(text)
    if label:
        print(label)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
