# secret-resolution

Resolve secrets at runtime through secrets-v1 (`secret://<namespace>/<key>`). In config and code, reference each secret by a `secret://` URI that a configured provider resolves; 1Password via `op run --env-file` is one adapter. In shell, use `${VAR}` under `op run`. A `${VAR}` reference in a file is valid only if a documented injector populates it. Never hardcode a literal in any file, command, or artifact. Literals are covered by `no-secret-exposure`.
