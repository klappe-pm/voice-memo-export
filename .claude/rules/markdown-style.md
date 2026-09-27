# markdown-style

## binding

Headings are lowercase kebab-case; a reserved filename's H1 keeps its literal, uppercase, with extension. Frontmatter opens on row 1 with `---` in canonical key order (domain, category, sub-category, topics, types, date-created, date-revised, status, aliases, tags, then file-specific keys sorted A to Z). `date-created` never changes; `date-revised` updates on content changes. Array values are deduped, sorted case-insensitively; an empty array is `key: []`. Unordered lists use `-`, nested two spaces, one blank line around the block, none between items. Code fences carry a language tag. Tables are pipe-style, `&#124;` for a literal pipe. Links are inline Markdown; a wikilink resolves by filename stem, case-insensitive, and a broken one is flagged, not created. One blank line follows frontmatter and separates sections.

## heading-format

1. H1 through H6 text is lowercase kebab-case, except the H1 of a reserved filename under rule 5.
2. The H1 matches the filename: its stem for an ordinary file, the full reserved literal under rule 5.
3. Within rule 1 there are no further exceptions: version tokens, command names, plugin names, inline paths, tool names, and acronyms (API, YAML, JSON) are lowercased and hyphenated in heading text.
4. Any tooling that keys off heading literals must be updated to kebab form before linting that file.
5. A reserved filename keeps its literal in the H1, uppercase and with its extension: `README.md` opens with `# README.MD`, `MEMORY.md` with `# MEMORY.MD`. `naming-conventions` lists which names are reserved. This covers the H1 only. Every other heading in the file is kebab-case under rule 1, and a file whose name is not reserved is untouched by this rule.

Rule 5 exists because rules 1 and 2 pull against each other on exactly these files. A reserved name is deliberately not kebab-case, so forcing its heading to kebab makes the document disagree with the filename it is named after. The literal is what a reader recognises, and it is what these files already carried in practice before the rule said so.

A project may keep an owner-selected title on a reserved file at its repository root, where the H1 is the project's name rather than a filename echo. That is a per-project exemption recorded in that project's own checker, not a licence to vary the convention elsewhere in the tree.

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
