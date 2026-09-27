# repo-scope

## binding

Every session operates inside exactly one repo at a time. That repo is the blast radius for reads, writes, commits, and commands.

## establishing-scope

Scope is established by the repo the user names or the working directory at session start. When ambiguous (a file path could resolve in more than one project, or no repo has been named), ask once before writing anything. Do not infer scope from file contents or past sessions.

## cross-repo-writes

Never write to a file outside the in-scope repo without explicit instruction naming the target repo. A path that resolves outside the current repo root is a cross-repo write, not a relative path edge case.

## scope-changes

Scope changes only when the user explicitly redirects to a different repo. A file reference that happens to live in another repo is not a scope change; flag it and ask.

## relationship-to-other-rules

`no-external-repo-publishing` governs outward-facing actions on repos the user does not own. This rule governs writes within the user's own projects. Both apply independently.
