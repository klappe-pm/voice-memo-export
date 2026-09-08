# llm-root-control-plane

This generated snapshot is the active shared configuration declaration for this project. The canonical source is `~/projects/active/0-llm-root/control-plane.md`.

# control-plane

Generated inventory and deployment declaration for llm-root. Run `scripts/reconcile-control-plane.py` after adding, moving, or deleting a managed source file or project. Existing opt-in cells remain authoritative for surviving options. New global resources opt in globally, new active projects receive the shared instruction and rules baseline, and new executable resources stay project opt-in until selected.

## projects

The manifest is generated from managed checkouts and `projects-root/`. A checkout move updates status and tier. A project disappears only after both its checkout and project-local source are gone.

| project | status | tier | template | origin |
|---|---|---|---|---|
| deepwiki-open | inactive | normal | base | klappe-pm/deepwiki-open |
| experimentation-tools | archived | low | base | - |
| experimentation-vault | active | high | base | klappe-pm/experimentation |
| fantasy-bros | inactive | normal | base | klappe-pm/fantasy-bros |
| get-a-job | inactive | normal | base | klappe-pm/get-a-job |
| green-lappe-properties | archived | low | base | klappe-pm/green-lappe-properties |
| harness | inactive | normal | base | klappe-pm/harness |
| jobs | inactive | normal | base | klappe-pm/jobs |
| lappe-linter | archived | low | base | klappe-pm/lappe-linter |
| launch-darkly | inactive | normal | base | klappe-pm/career-jobs |
| legal-tbi | active | normal | base | klappe-pm/legal-tbi |
| llama.cpp | external | low | base | ggml-org/llama.cpp |
| Money Manager LLM | archived | low | base | klappe-pm/power-prompts |
| open-design | external | low | base | nexu-io/open-design |
| product-management-plugin | inactive | normal | base | klappe-pm/product-management-plugin |
| product-workbench | active | high | base | klappe-pm/product-workbench |
| regulatory-ingredients-labels-laws | inactive | normal | base | klappe-pm/regulatory-ingredients-labels-laws |
| session-data | archived | low | base | klappe-pm/session-data |
| tokscale | external | low | base | junhoyeo/tokscale |
| vault-maker | inactive | normal | base | - |
| voice-memo-export | active | normal | base | klappe-pm/voice-memo-export |
| voice-to-vps | active | high | base | klappe-pm/voice-to-vps |
| wall-bros | active | high | base | klappe-pm/wall-bros |
| whiffletree | active | normal | base | klappe-pm/whiffletree |

## configuration

Each table has `global` first, then active project columns in alphabetical order. Column A links to the source file. `x` opts in and any other cell opts out.

## instruction-file

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [AGENTS.md](AGENTS.md) | x | x | x | x | x | x | x | x |

## rules

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [rule:captured-content-redaction](rules/captured-content-redaction.md) | x | x | x | x | x | x | x | x |
| [rule:command-cwd-scoping](rules/command-cwd-scoping.md) | x | x | x | x | x | x | x | x |
| [rule:find-fix-document](rules/find-fix-document.md) | x | x | x | x | x | x | x | x |
| [rule:guard-bypass-approval](rules/guard-bypass-approval.md) | x | x | x | x | x | x | x | x |
| [rule:irreversible-external-actions](rules/irreversible-external-actions.md) | x | x | x | x | x | x | x | x |
| [rule:macos-shell](rules/macos-shell.md) | x | x | x | x | x | x | x | x |
| [rule:manual-changes-authoritative](rules/manual-changes-authoritative.md) | x | x | x | x | x | x | x | x |
| [rule:markdown-style](rules/markdown-style.md) | x | x | x | x | x | x | x | x |
| [rule:memory-criteria](rules/memory-criteria.md) | x | x | x | x | x | x | x | x |
| [rule:naming-conventions](rules/naming-conventions.md) | x | x | x | x | x | x | x | x |
| [rule:no-em-dash](rules/no-em-dash.md) | x | x | x | x | x | x | x | x |
| [rule:no-external-repo-publishing](rules/no-external-repo-publishing.md) | x | x | x | x | x | x | x | x |
| [rule:no-hardwrapped-writing](rules/no-hardwrapped-writing.md) | x | x | x | x | x | x | x | x |
| [rule:no-model-attribution](rules/no-model-attribution.md) | x | x | x | x | x | x | x | x |
| [rule:no-secret-exposure](rules/no-secret-exposure.md) | x | x | x | x | x | x | x | x |
| [rule:obsidian-vault-writes](rules/obsidian-vault-writes.md) | x | x | x | x | x | x | x | x |
| [rule:output-format-contract](rules/output-format-contract.md) | x | x | x | x | x | x | x | x |
| [rule:repo-scope](rules/repo-scope.md) | x | x | x | x | x | x | x | x |
| [rule:secret-exposure-response](rules/secret-exposure-response.md) | x | x | x | x | x | x | x | x |
| [rule:secret-resolution](rules/secret-resolution.md) | x | x | x | x | x | x | x | x |
| [rule:secrets-handling](rules/secrets-handling.md) | x | x | x | x | x | x | x | x |
| [rule:secrets-out-of-git](rules/secrets-out-of-git.md) | x | x | x | x | x | x | x | x |
| [rule:shell-discipline](rules/shell-discipline.md) | x | x | x | x | x | x | x | x |
| [rule:third-party-identity](rules/third-party-identity.md) | x | x | x | x | x | x | x | x |
| [rule:token-shaped-values](rules/token-shaped-values.md) | x | x | x | x | x | x | x | x |
| [rule:work-product-confidentiality](rules/work-product-confidentiality.md) | x | x | x | x | x | x | x | x |

## hooks-post-tool-use

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:reconcile-control-plane](hooks/reconcile-control-plane.sh) | x |  |  |  |  |  |  |  |
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |

## hooks-pre-tool-use

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:no-emdash-guard](hooks/no-emdash-guard.sh) | x | x |  |  |  | x |  |  |
| [hook:no-hardwrap-guard](hooks/no-hardwrap-guard.sh) | x | x |  |  |  | x |  |  |
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |

## hooks-session-start

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:worktree-validate](hooks/worktree-validate.sh) | x |  |  |  |  |  |  |  |

## hooks-user-prompt-submit

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:prompt-capture](hooks/prompt-capture.sh) | x |  |  |  |  |  |  |  |

## hooks-worktree-create

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:worktree-create](hooks/worktree-create.sh) | x |  |  |  |  |  |  |  |

## hooks-worktree-remove

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [hook:worktree-remove](hooks/worktree-remove.sh) | x |  |  |  |  |  |  |  |

## skills

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [skill:agentsview-finding-history](skills/agentsview-finding-history/SKILL.md) | x |  |  |  |  |  |  |  |
| [skill:commit-and-pr](skills/commit-and-pr/SKILL.md) | x | x | x | x |  |  | x | x |
| [skill:defuddle](skills/defuddle/SKILL.md) | x |  |  |  |  |  |  |  |
| [skill:experimentation-design](skills/experimentation-design/SKILL.md) | x | x |  | x |  |  |  |  |
| [skill:fix-documents](skills/fix-documents/SKILL.md) | x |  |  |  |  |  |  |  |
| [skill:get-linked-context](skills/get-linked-context/SKILL.md) | x |  |  |  |  |  |  |  |
| [skill:git-worktree](skills/git-worktree/SKILL.md) | x | x | x | x |  |  | x | x |
| [skill:impeccable](skills/impeccable/SKILL.md) |  |  |  |  |  |  |  |  |
| [skill:karpathy-guidelines](skills/karpathy-guidelines/SKILL.md) | x |  |  |  |  |  |  |  |
| [skill:legal-discovery](skills/legal-discovery/SKILL.md) |  |  | x |  |  |  |  |  |
| [skill:obsidian-bases](skills/obsidian-bases/SKILL.md) | x | x |  |  |  |  |  |  |
| [skill:obsidian-cli](skills/obsidian-cli/SKILL.md) | x | x |  |  |  |  |  |  |
| [skill:obsidian-markdown](skills/obsidian-markdown/SKILL.md) | x | x |  |  |  |  |  |  |
| [skill:pdf-extraction](skills/pdf-extraction/SKILL.md) | x |  | x |  |  |  |  |  |
| [skill:skill-creator](skills/skill-creator/SKILL.md) | x |  |  |  |  |  |  |  |

## commands

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [command:backlog-new](commands/backlog-new.md) | x |  |  |  |  |  |  |  |
| [command:commit](commands/commit.md) | x |  |  |  |  |  |  |  |
| [command:feature-dev](commands/feature-dev.md) | x |  |  |  |  |  |  |  |
| [command:new-sdk-app](commands/new-sdk-app.md) | x |  |  |  |  |  |  |  |
| [command:project-state-review](commands/project-state-review.md) | x |  |  |  |  |  |  |  |
| [command:reflect](commands/reflect.md) | x |  |  |  |  |  |  |  |
| [command:task](commands/task.md) | x |  |  |  |  |  |  |  |

## agents

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [agent:agent-sdk-verifier-py](agents/agent-sdk-verifier-py.md) | x |  |  |  |  |  |  |  |
| [agent:agent-sdk-verifier-ts](agents/agent-sdk-verifier-ts.md) | x |  |  |  |  |  |  |  |
| [agent:code-architect](agents/code-architect.md) | x |  |  |  |  |  |  |  |
| [agent:code-explorer](agents/code-explorer.md) | x |  |  |  |  |  |  |  |
| [agent:code-reviewer](agents/code-reviewer.md) | x |  |  |  |  |  |  |  |
| [agent:code-simplifier](agents/code-simplifier.md) | x |  |  |  |  |  |  |  |
| [agent:comment-analyzer](agents/comment-analyzer.md) | x |  |  |  |  |  |  |  |
| [agent:dependencies-tracker](agents/dependencies-tracker.md) | x |  |  |  |  |  |  |  |
| [agent:frontmatter-tech](agents/frontmatter-tech.md) | x |  |  |  |  |  |  |  |
| [agent:graph-cartographer](agents/graph-cartographer.md) | x |  |  |  |  |  |  |  |
| [agent:pr-test-analyzer](agents/pr-test-analyzer.md) | x |  |  |  |  |  |  |  |
| [agent:precommit-guard](agents/precommit-guard.md) | x |  |  |  |  |  |  |  |
| [agent:product-management](agents/product-management.md) | x |  |  | x |  |  |  |  |
| [agent:question-tracker](agents/question-tracker.md) | x |  |  |  |  |  |  |  |
| [agent:refactor-cluster-planner](agents/refactor-cluster-planner.md) | x |  |  |  |  |  |  |  |
| [agent:silent-failure-hunter](agents/silent-failure-hunter.md) | x |  |  |  |  |  |  |  |
| [agent:spec-scribe](agents/spec-scribe.md) | x |  |  |  |  |  |  |  |
| [agent:type-design-analyzer](agents/type-design-analyzer.md) | x |  |  |  |  |  |  |  |
| [agent:worktree-pr-orchestrator](agents/worktree-pr-orchestrator.md) | x |  |  |  |  |  |  |  |

## project-local-configuration

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [project:AGENTS.md](projects-root/wall-bros/AGENTS.md) |  | x | x | x |  | x | x | x |
| [project:scripts](projects-root/legal-tbi/scripts/log-model-change.sh) |  |  | x |  |  |  |  |  |

## runtimes

| option | global | experimentation-vault | legal-tbi | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|
| [runtime:claude](scripts/adapters/claude.py) | x |  |  |  |  |  |  |  |
| [runtime:codex](scripts/adapters/codex.py) | x |  |  |  |  |  |  |  |
| [runtime:cursor](scripts/adapters/cursor.py) | x |  |  |  |  |  |  |  |
| [runtime:gemini](scripts/adapters/gemini.py) | x |  |  |  |  |  |  |  |
| [runtime:opencode](scripts/adapters/opencode.py) | x |  |  |  |  |  |  |  |
