# captured-content-redaction

Content captured from external sources (crawls, exports, scraped pages, API responses) is scanned with the `token-shaped-values` detector before persisting. Replace each match with `[REDACTED:<kind>]`. Drop the record if redaction leaves it meaningless. Reports and indexes built from captured content inherit this: nothing token-shaped reaches a generated file.
