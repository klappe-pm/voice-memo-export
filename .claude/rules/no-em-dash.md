# no-em-dash

Never use a dash as punctuation in authored prose. This prohibits em dashes, en dashes, spaced hyphens (` - `), and double hyphens (`--`). Use a comma, period, colon, semicolon, or parentheses instead. Applies to notes, docs, plans, commit messages, PR and issue bodies, generated reports, and conversation output.

Hyphens remain valid inside compound words (`pre-commit`, `read-only`) and in code, paths, flags, and identifiers. Numeric ranges use "to" (`3 to 5`), not a dash. A list item marker at line start (`- item`) is structure, not punctuation.

Absolute, not stylistic: a file's existing dash usage is not a reason to reproduce it. When editing a file that contains them, fix the sentences you touch.

Quote source text that contains dashes verbatim only inside a code fence.
