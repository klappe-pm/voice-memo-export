# token-shaped-values

A value is token-shaped when the pattern set in `hooks/lib/guard-utils.sh` matches it: cloud and API key prefixes, JWTs, PEM blocks, long hex or base64 runs adjacent to key/token/secret. That detector is the single definition. Every rule that says "secret" or "token-shaped" means this; do not reason about whether something looks like a secret, run the detector.
