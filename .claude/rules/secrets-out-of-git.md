# secrets-out-of-git

## binding

`settings.local.json`, env files, credentials, private keys, and OAuth artifacts are gitignored and never staged. `.env.example` with placeholder values is allowed. The pre-commit scan (`scripts/git-hooks/check-staged-secrets.sh`) runs the `token-shaped-values` detector on staged content and blocks matches. If a secret was already committed, follow `secret-exposure-response`.
