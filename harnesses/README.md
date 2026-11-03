# Agent Harness Integrations

The canonical skill source is `skills/<skill-id>/SKILL.md`. Keep one source of
truth and install it into each harness's native discovery directory. Do not
maintain hand-edited copies of all 101 skills in multiple adapter folders.

## Supported paths

| Harness | Native project/user location | Integration in this repository |
|---|---|---|
| Claude Code | `~/.claude/skills/<id>/SKILL.md` or native plugin | Native plugin metadata in `.claude-plugin/`; installer can target the user skill directory |
| OpenAI Codex | `~/.agents/skills/<id>/SKILL.md` | `install.sh --harness codex` / `install.ps1 -Harness codex` |
| OpenCode | `~/.config/opencode/skills/<id>/SKILL.md` | `install.sh --harness opencode` / `install.ps1 -Harness opencode` |
| Cursor | `.cursor/rules/*.mdc` or root `AGENTS.md` | Starter rule at `.cursor/rules/esp32-domain.mdc`; use the same canonical skills through the generic installer where Agent Skills discovery is enabled |
| Gemini CLI | root/workspace `GEMINI.md`; Agent Skills discovery is version-dependent | Starter context at `GEMINI.md`; use the skills integration supported by the installed CLI version |
| Generic Agent Skills | harness-specific Agent Skills directory | `install.sh --target <directory>` / `install.ps1 -Target <directory>` |

## Install

Linux/macOS:

```bash
./install.sh --harness codex
./install.sh --harness opencode
./install.sh --harness claude
./install.sh --harness all
```

Windows PowerShell:

```powershell
.\install.ps1 -Harness codex
.\install.ps1 -Harness opencode
.\install.ps1 -Harness claude
.\install.ps1 -Harness all
```

Use `--dry-run` / `-DryRun` before writing. Existing skill folders are left
untouched unless `--force` / `-Force` is explicitly supplied. The installer
copies the canonical `SKILL.md`, per-skill license and references; it does not
install runtime hooks, change model settings, grant tool permissions or claim
feature parity between harnesses.

## Why the adapters are intentionally thin

Harnesses differ in how they load persistent instructions, skills, tools,
plugins and hooks. A shared skill corpus is portable; runtime lifecycle,
permissions and hooks are not. This repository therefore provides a common
knowledge layer and small native entry points instead of pretending every
harness supports the same capabilities.

## Official format references

- Codex customization: https://developers.openai.com/codex/customization/
- Cursor rules: https://docs.cursor.com/context/rules
- Gemini CLI context: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md
- OpenCode skills: https://opencode.ai/docs/skills
- VS Code Agent Skills locations: https://code.visualstudio.com/docs/agent-customization/agent-skills
