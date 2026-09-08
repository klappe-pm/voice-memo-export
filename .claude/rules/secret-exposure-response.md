# secret-exposure-response

When a literal secret has landed anywhere (file, commit, log, transcript, generated artifact): stop the current task, report the exposure to the user in the same turn, treat the secret as burned and rotate it, and purge it from git history if committed. Redaction after exposure is cleanup, not remediation; rotation is the remediation.
