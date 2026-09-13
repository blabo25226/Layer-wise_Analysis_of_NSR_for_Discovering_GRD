# Provider compatibility notes

このパッケージは 2026-09-12 時点の利用形態を前提にしています。

## Cursor

- Native project rules: `.cursor/rules/*.mdc`
- Native custom subagents: `.cursor/agents/*.md`
- Skills: `.cursor/skills/<skill>/SKILL.md`
- Cursorは `AGENTS.md` も読めます。

## Claude Code

- Project rules: `.claude/rules/*.md`
- Project subagents: `.claude/agents/*.md`
- Project skills: `.claude/skills/<skill>/SKILL.md`
- Root `CLAUDE.md` をbootstrapとして含めています。

## Gemini / Antigravity CLI

現在のAntigravity workspace customizationは `.agents/`（複数形）がnativeです。

- `.agents/rules/`
- `.agents/agents/`
- `.agents/skills/`
- root `GEMINI.md` / `AGENTS.md`

ユーザー指定に合わせて `.gemini/` も同梱していますが、`.gemini/` は主にmirror/設計参照用です。
実際のAntigravity discoveryは `.agents/` を優先してください。

## Codex

- 既存repoの `AGENTS.md` を第一のbootstrapとします。
- `.codex/rules/*.rules` はworker command permission/routingに利用。
- `.codex/agents/` と `.codex/skills/` はこの研究OSの論理role/skill定義として同梱し、
  `AGENTS.md` とResearch PI指示から明示的に参照させます。
