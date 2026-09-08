# no-hardwrapped-writing

Never hard-wrap prose in authored Markdown. Write each paragraph and each list item as one line and let the editor soft-wrap. Never insert breaks at a fixed column. Applies to notes, docs, plans, PR and issue bodies, runbooks, and any generated Markdown artifact.

Break lines only for structure: blank lines between blocks, headings, list items, table rows, code fences, blockquotes, frontmatter, and intentional line breaks (trailing two spaces or backslash).

Absolute, not stylistic: a file's existing hard-wrapped style is not a reason to reproduce it. When editing a hard-wrapped file, reflow the paragraphs you touch. If the full file must be clean before editing, reflow it in a separate commit first.

Quote hard-wrapped source text verbatim only inside a code fence.
