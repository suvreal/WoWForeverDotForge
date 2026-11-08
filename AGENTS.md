# Project conventions

- Use `BEL: {MESSAGE}` for pull request titles/messages.
- Run `python3 -m unittest discover -v` after package-manager changes.
- Keep credentials, state, addon archives and backups outside the repository.
- Preserve strict `_forever_` targeting, TOC compatibility checks, local-change protection and backup/rollback behavior.
- CurseForge integration uses the official API with the user's own key. Respect distribution restrictions; do not fabricate download URLs when the API withholds them.
