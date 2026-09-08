# naming-conventions

Filenames are lowercase kebab-case, never underscores. Directories follow the same convention. Reserved uppercase names (`README.md`, `CLAUDE.md`, `MEMORY.md`, `CODEX.md`, `GEMINI.md`, `AGENTS.md`, `*.pointer`) stay literal.

## key-documents

Any document referenced by a `CLAUDE.md`, hook, script, or rule is a key document. Key documents must not be referenced by their dated filename. Instead, create a stable `.pointer` file with a fixed canonical name (e.g. `LATEST.pointer`) whose sole content is the relative path to the target. All `CLAUDE.md` files, hooks, scripts, and rules reference only the pointer path.

Pointer file format:

```
relative/path/to/target-file.md
```

One path per file. Path is relative to the directory containing the pointer file. Comments are not permitted; the file contains only the path. The pointer file itself is never dated or versioned. When the target is renamed or superseded, update only the pointer file.
