# secret-resolution

## binding

Resolve secrets at runtime through secrets-v1 (`secret://<namespace>/<key>`). In config and code, reference each secret by a `secret://` URI that a configured provider resolves; 1Password via `op run --env-file` is one adapter. In shell, use `${VAR}` under `op run`. A `${VAR}` reference in a file is valid only if a documented injector populates it. Never hardcode a literal in any file, command, or artifact. Literals are covered by `no-secret-exposure`.

## shared-credential-launcher

The runtime-independent entry point is `$HOME/projects/active/0-llm-root/scripts/credentials.py`. Its adjacent `credential-profiles.json` maps stable secret URIs to 1Password references and maps profiles to application environment variables. It stores references only. Use the launcher for an authorized GitHub or provider API operation when the required profile is enrolled:

```bash
python3 "$HOME/projects/active/0-llm-root/scripts/credentials.py" run --profile github --cwd "$HOME/projects/active/0-llm-root" -- gh api user --jq .login
```

Set `--cwd` to the actual in-scope project. Profiles compose by repeating `--profile`; select only those the child needs. The executable after `--` can be an existing runtime, a future runtime, or a model router. The launcher is an explicit entry point, not a replacement for bare commands, a permission bypass, or a guarantee that a sandbox passes environment variables to its children. Missing enrollment and provider access are blockers, not reasons to repeat a working host login. `status` reports configuration, never authenticated success.

The source installer creates `$HOME/.local/bin/llm-auth` outside runtime-owned directories. It links to this launcher and copies no credentials. After reinstalling runtimes, run `bash "$HOME/projects/active/0-llm-root/scripts/install.sh"` to recover the entry point and resynchronize managed configuration. Retain the source reference map and provider vault; replacing a runtime binary does not require new profile enrollment. Native subscription sessions and hosted connections still follow their own provider-supported recovery.

The setup and acceptance procedure is `$HOME/projects/active/0-llm-root/docs/shared-credentials.md`. Hosted environments need a supported credential provider or their platform's GitHub integration. Vendor subscription sessions remain vendor-owned. A credential the operator's own sign-in produced may be stored as one vault item and replayed into the operator's own containers only through the runtime manifest in `scripts/credential-profiles.json` (`docs/adr/2026-09-23-develop-in-identical-containers-on-subscription-auth.md`, V-09 and V-10); it is never copied by hand, committed, logged, or sent to any host or person that is not the operator's. Do not inject a provider API profile merely to launch a subscription-authenticated runtime.
