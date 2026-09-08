# no-secret-exposure

Never place a literal token-shaped value (see `token-shaped-values`) in any file, command, log, stdout, generated artifact, or the conversation. Never read `.env`, `settings.local.json`, credential files, or raw `env`/`printenv` output into context. Never pass a secret as a command argument or capture one with `$(op read …)`; both land in shell history and the transcript. To verify a secret resolved, check existence, length, or the first four characters only. If a value is exposed anyway, follow `secret-exposure-response`.
