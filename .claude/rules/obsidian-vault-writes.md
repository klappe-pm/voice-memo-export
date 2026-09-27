# obsidian-vault-writes

## binding

Never create a file to satisfy a broken wikilink in an Obsidian vault (a directory with `.obsidian/` at its root); leave the link as it is and flag it in the same turn. Never move, rename, or delete a vault file, create a folder, or add, remove, or reorder frontmatter keys without explicit instruction. Vault frontmatter follows `markdown-style` key order, and `date-revised` updates on every content write. Never convert wikilinks to Markdown links, or Markdown links to wikilinks unless instructed. `no-hardwrapped-writing` and `no-em-dash` apply without exception.

## structure

Obsidian vaults are the primary persistent store for notes, plans, projects, and research. Writes to vault files carry extra constraints beyond standard Markdown rules.

Never create a file to satisfy a broken wikilink. A broken wikilink is left as-is and flagged in the same turn. The user decides whether the target file should exist.

Never move, rename, or delete a vault file without explicit instruction. Obsidian's wikilink graph depends on filename stability; a rename silently breaks every note that references the old stem.

Folder structure inside a vault is canonical. Do not create new folders without explicit instruction.

## frontmatter

Every vault file that has frontmatter must conform to `markdown-style` key order. Do not add, remove, or reorder frontmatter keys without instruction. `date-revised` updates on every content write.

## wikilinks

Wikilinks use the filename stem, case-insensitive, with no path prefix unless the vault has duplicate stems. Never convert wikilinks to standard Markdown links. Never convert standard Markdown links to wikilinks unless instructed.

## prose

See `no-hardwrapped-writing` and `no-em-dash`. Both apply without exception inside vault files.

## scope

These constraints apply to any file written inside a directory identified as an Obsidian vault (contains a `.obsidian/` directory at its root).
