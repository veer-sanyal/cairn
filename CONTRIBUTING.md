# Contributing

Issues and bug reports are welcome — open one on GitHub.

Want to share how an instance is going? Cairn collects nothing automatically (telemetry is local
JSONL, never networked), so outcomes are opt-in: compute your own stats locally and paste them
via the [instance-stats issue template](.github/ISSUE_TEMPLATE/instance-stats.md).

Kernel changes ship through versioned plugin releases, never silent self-modification (P10) —
propose them as issues; `/cairn:upgrade` migrates instances with a changelog diff.
