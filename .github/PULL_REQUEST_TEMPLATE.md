## What and why

<!-- Short description of the change. -->

## Checklist

- [ ] Tests pass locally (`make test`) and lint is clean (`make lint`).
- [ ] No secrets, credentials or real client data anywhere (only `[Voorbeeld]` data).
- [ ] Read-only by default is preserved; `OCTOPUS_WRITE_ENABLED` is not set in any example.
- [ ] Daily limits respected: no new tool calls a 2/day endpoint without cache or sync.
- [ ] Nothing uses the Management API, the file-import API or any paid plan.
- [ ] Uncertain behaviour is marked "verifieer actuele regel" and listed in `docs/OPEN-QUESTIONS.md`.
- [ ] Docs and CHANGELOG updated when behaviour changes.
- [ ] Tool names (`octopus_*`) are not renamed without a deprecation note.
