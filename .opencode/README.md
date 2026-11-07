# OpenCode integration

OpenCode supports project skills under `.opencode/skills/<name>/SKILL.md`,
`.agents/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md`.
The canonical corpus in this repository remains `skills/`; install it into
OpenCode's user directory with:

```bash
./install.sh --harness opencode
```

or on Windows:

```powershell
.\install.ps1 -Harness opencode
```

OpenCode loads skill metadata for discovery and the skill body on demand.
Permissions are controlled by OpenCode configuration; this repository's
installer does not change those permissions. See
https://opencode.ai/docs/skills for the current native behavior.
