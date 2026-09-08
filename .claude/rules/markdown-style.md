# markdown-style

## heading-format

1. H1 through H6 text is lowercase kebab-case.
2. H1 matches the filename stem.
3. No exceptions: version tokens, command names, plugin names, inline paths, tool names, and acronyms (API, YAML, JSON) are lowercased and hyphenated in heading text.
4. Any tooling that keys off heading literals must be updated to kebab form before linting that file.

## frontmatter

Opens on row 1 with `---`. Canonical key order:

```yaml
domain:
category:
sub-category:
topics:
types:
date-created:
date-revised:
status:
aliases:
tags:
```

- Project, folder, and file-specific keys go after `tags:`, sorted alphabetically A to Z.
- `status` values: `NEW`, `PROPOSED`, `ACCEPTED`, `DRAFT`, `INPRG`, `REVIEW`, `DONE`, `ARCHIVED`.
- `date-created` is set once and never changed. `date-revised` updates on every write that changes content, not on metadata-only fixes.

## array-values

Array values are deduped and sorted case-insensitively. Empty arrays are written as `key: []`.

Example:

```yaml
---
domain: real-estate
category: green-lappe
sub-category: snohomish
topics: []
types: []
date-created: 2026-06-18
date-revised: 2026-06-18
status: DRAFT
aliases: []
tags: []
---
```

Plans, features, decisions, risks, tasks, and status reports follow this order and add artifact-specific keys below `tags:`, sorted alphabetically.

## lists

1. Unordered lists use `-`, nested with two spaces.
2. One blank line before and after a list block; no blank lines between items unless items contain multiple paragraphs.

## code-blocks

1. Fenced code blocks use three backticks and a language tag.

## tables

1. Tables are pipe-style; escape literal pipes as `&#124;`.

## links

1. Links are inline Markdown to canonical sources.
2. Wikilinks resolve by filename stem, case-insensitive. A broken wikilink is left as-is and flagged in the same turn; do not create files to satisfy a wikilink.

## spacing

1. One blank line after frontmatter close and between sibling top-level sections.

## cross-references

See `no-hardwrapped-writing` and `no-em-dash` for prose constraints.
