# llm-root-control-plane

This generated snapshot is the active shared configuration declaration for this project. The canonical source is `~/projects/active/0-llm-root/control-plane.md`.

# control-plane

Generated inventory and deployment declaration for llm-root. Run `scripts/reconcile-control-plane.py` after adding, moving, or deleting a managed source file or project. Existing opt-in cells remain authoritative for surviving options. New global resources opt in globally, new active projects receive the shared instruction and rules baseline, and new executable resources stay project opt-in until selected.

## projects

The manifest is generated from managed checkouts and `projects-root/`. A checkout move updates status and tier. A project disappears only after both its checkout and project-local source are gone.

| project | status | tier | template | origin |
|---|---|---|---|---|
| a-product-discovery | active | normal | base | klappe-pm/a-product-discovery |
| agent-graph | active | normal | base | klappe-pm/agent-graph |
| clients | active | normal | base | klappe-pm/clients |
| deepwiki-open | inactive | normal | base | klappe-pm/deepwiki-open |
| experimentation-tools | archived | low | base | - |
| experimentation-vault | active | normal | base | klappe-pm/experimentation |
| fantasy-bros | inactive | normal | base | klappe-pm/nfl-draft-2026 |
| flock-off | unmanaged | - | base | - |
| get-a-job | inactive | normal | base | klappe-pm/get-a-job |
| green-lappe-properties | archived | low | base | klappe-pm/green-lappe-properties |
| harness | inactive | normal | base | klappe-pm/harness |
| jobs | inactive | normal | base | klappe-pm/jobs |
| jobs-v2000 | active | normal | base | klappe-pm/jobs-v2000 |
| lappe-linter | active | normal | base | klappe-pm/lappe-linter |
| lattice-lock | archived | low | base | klappe-pm/lattice-lock |
| launch-darkly | inactive | normal | base | klappe-pm/career-jobs |
| legal-tbi | active | normal | base | klappe-pm/legal-tbi |
| llama.cpp | external | low | base | ggml-org/llama.cpp |
| Money Manager LLM | archived | low | base | klappe-pm/power-prompts |
| obsidian-stuff | active | normal | base | klappe-pm/obsidian-stuff |
| OnePersonCompany | active | one-person-company | base | tashfeenahmed/OnePersonCompany |
| open-design | external | low | base | nexu-io/open-design |
| product-management-plugin | inactive | normal | base | klappe-pm/product-management-plugin |
| product-workbench | active | normal | base | klappe-pm/product-workbench |
| regulatory-ingredients-labels-laws | inactive | normal | base | klappe-pm/regulatory-ingredients-labels-laws |
| session-data | archived | low | base | klappe-pm/session-data |
| tokscale | external | low | base | junhoyeo/tokscale |
| vault-maker | inactive | normal | base | - |
| voice-memo-export | active | normal | base | klappe-pm/voice-memo-export |
| voice-to-vps | active | normal | base | klappe-pm/voice-to-vps |
| wall-bros | active | normal | base | klappe-pm/wall-bros |
| whiffletree | active | normal | base | klappe-pm/whiffletree |

## configuration

Each table has `global` first, then active project columns in alphabetical order. Column A links to the source file. `x` opts in and any other cell opts out.

## instruction-file

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [AGENTS.md](AGENTS.md) | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |

## rules

| option | tier | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [rule:captured-content-redaction](rules/captured-content-redaction.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:command-cwd-scoping](rules/command-cwd-scoping.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:delegated-quality-passes](rules/delegated-quality-passes.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:docs-provenance-frontmatter](rules/docs-provenance-frontmatter.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:find-fix-document](rules/find-fix-document.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:finish-or-record-scope-change](rules/finish-or-record-scope-change.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:guard-bypass-approval](rules/guard-bypass-approval.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:irreversible-external-actions](rules/irreversible-external-actions.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:macos-shell](rules/macos-shell.md) | project | x |  | x |  | x | x | x | x | x |  | x | x | x | x | x |
| [rule:manual-changes-authoritative](rules/manual-changes-authoritative.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:markdown-style](rules/markdown-style.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:memory-criteria](rules/memory-criteria.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:naming-conventions](rules/naming-conventions.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:no-agent-attribution](rules/no-agent-attribution.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:no-em-dash](rules/no-em-dash.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:no-external-repo-publishing](rules/no-external-repo-publishing.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:no-hardwrapped-writing](rules/no-hardwrapped-writing.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:no-secret-exposure](rules/no-secret-exposure.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:obsidian-vault-writes](rules/obsidian-vault-writes.md) | project | x |  | x |  | x | x | x | x | x |  | x | x | x | x | x |
| [rule:open-decision-elicitation](rules/open-decision-elicitation.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:output-format-contract](rules/output-format-contract.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:repo-scope](rules/repo-scope.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:resume-send-format-contract](rules/resume-send-format-contract.md) | project | x |  | x |  | x | x | x | x | x |  | x | x | x | x | x |
| [rule:secret-exposure-response](rules/secret-exposure-response.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:secret-resolution](rules/secret-resolution.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:secrets-out-of-git](rules/secrets-out-of-git.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:session-handoff-on-pr](rules/session-handoff-on-pr.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:shell-discipline](rules/shell-discipline.md) | common | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| [rule:third-party-identity](rules/third-party-identity.md) | project | x |  | x |  | x | x | x | x | x |  | x | x | x | x | x |
| [rule:token-shaped-values](rules/token-shaped-values.md) | global | x | x | x | x | x | x | x | x | x | x | x | x | x | x | x |

## hooks-post-tool-use

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:reconcile-control-plane](hooks/reconcile-control-plane.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:tool-budget-guard](hooks/tool-budget-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-post-tool-use-failure

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:tool-budget-guard](hooks/tool-budget-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-pre-tool-use

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:env-dump-guard](hooks/env-dump-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:no-attribution-guard](hooks/no-attribution-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:prose-guard](hooks/prose-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:tool-budget-guard](hooks/tool-budget-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-session-start

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:session-start](hooks/session-start.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hook:worktree-validate](hooks/worktree-validate.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-stop

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:require-pr-on-stop](hooks/require-pr-on-stop.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-subagent-start

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-subagent-stop

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:subagent-cap-guard](hooks/subagent-cap-guard.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-user-prompt-submit

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:prompt-capture](hooks/prompt-capture.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-worktree-create

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:worktree-create](hooks/worktree-create.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## hooks-worktree-remove

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [hook:worktree-remove](hooks/worktree-remove.sh) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## skills

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [skill:amazon-interview](skills/amazon-interview/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:brainstorming](skills/brainstorming/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:commit-and-pr](skills/commit-and-pr/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:company-researcher](skills/company-researcher/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:coordinated-plan-execution](skills/coordinated-plan-execution/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:defuddle](skills/defuddle/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:design-control-plane](skills/design-control-plane/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:experimentation-design](skills/experimentation-design/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:explain-mode](skills/explain-mode/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:fix-documents](skills/fix-documents/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:get-linked-context](skills/get-linked-context/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:git-worktree](skills/git-worktree/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:impeccable](skills/impeccable/SKILL.md) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:karpathy-guidelines](skills/karpathy-guidelines/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:legal-discovery](skills/legal-discovery/SKILL.md) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:market-researcher](skills/market-researcher/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:mock-interviewer](skills/mock-interviewer/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:obsidian-bases](skills/obsidian-bases/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:obsidian-cli](skills/obsidian-cli/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:obsidian-markdown](skills/obsidian-markdown/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:pdf-extraction](skills/pdf-extraction/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:role-researcher](skills/role-researcher/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:skill-creator](skills/skill-creator/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:star-stories](skills/star-stories/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:systematic-debugging](skills/systematic-debugging/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:test-driven-development](skills/test-driven-development/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:use-railway](skills/use-railway/SKILL.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [skill:vault-refactor](skills/vault-refactor/SKILL.md) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## commands

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [command:commit](commands/commit.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [command:feature-dev](commands/feature-dev.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [command:new-sdk-app](commands/new-sdk-app.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [command:project-state-review](commands/project-state-review.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [command:reflect](commands/reflect.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## agents

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [agent:agent-sdk-verifier-py](agents/agent-sdk-verifier-py.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:agent-sdk-verifier-ts](agents/agent-sdk-verifier-ts.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:code-reviewer](agents/code-reviewer.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:code-simplifier](agents/code-simplifier.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:comment-analyzer](agents/comment-analyzer.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:dependencies-tracker](agents/dependencies-tracker.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:frontmatter-tech](agents/frontmatter-tech.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:graph-cartographer](agents/graph-cartographer.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:pr-test-analyzer](agents/pr-test-analyzer.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:precommit-guard](agents/precommit-guard.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:product-management](agents/product-management.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:question-tracker](agents/question-tracker.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:refactor-cluster-planner](agents/refactor-cluster-planner.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:silent-failure-hunter](agents/silent-failure-hunter.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:type-design-analyzer](agents/type-design-analyzer.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [agent:worktree-pr-orchestrator](agents/worktree-pr-orchestrator.md) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## mcp-servers

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [mcp:railway](components.json) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## project-local-configuration

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [project:agents](projects-root/jobs-v2000/agents/claim-evidence-auditor.md) |  |  |  |  |  | x |  |  |  |  |  |  |  |  |  |
| [project:AGENTS.md](projects-root/wall-bros/AGENTS.md) |  | x | x |  | x | x |  | x |  |  | x |  | x | x | x |
| [project:hooks](projects-root/product-workbench/hooks/hooks.json) |  |  |  |  |  |  |  |  |  |  | x |  |  |  |  |
| [project:scripts](projects-root/legal-tbi/scripts/log-model-change.sh) |  |  |  |  |  |  |  | x |  |  |  |  |  |  |  |

## runtimes

| option | global | a-product-discovery | agent-graph | clients | experimentation-vault | jobs-v2000 | lappe-linter | legal-tbi | obsidian-stuff | OnePersonCompany | product-workbench | voice-memo-export | voice-to-vps | wall-bros | whiffletree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [runtime:claude](scripts/adapters/claude.py) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [runtime:codex](scripts/adapters/codex.py) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [runtime:cursor](scripts/adapters/cursor.py) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [runtime:gemini](scripts/adapters/gemini.py) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [runtime:opencode](scripts/adapters/opencode.py) | x |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
