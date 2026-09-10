# Model and Agent Routing

Use quality-first routing.

Corrected 2026-09-10: an earlier version of this line justified the routing by "this campaign is
expected to run under a Claude Max plan". That premise was false. The account is an organization
seat (`seatTier: team_labs_standard`, `organizationType: claude_team`, org "Nakamura Lab"), not a
personal Max plan. The routing below is unchanged, but its justification is not the plan: it is that
a wrong call in these roles is expensive to retract. See `GPU_RUNclaude1/research_state.md` §5b for
the measured account state and the observed access constraints.

Use Opus-tier agents for:
- supervision
- hypothesis generation
- literature judgment
- methodology
- results interpretation
- statistics
- reproducibility audit
- independent review
- replication

Use Sonnet-tier agents for:
- implementation
- experiment operations
- report assembly
- artifact curation

Use Haiku only for mechanical extraction if separately configured.

Subagents should use preloaded skills listed in their frontmatter.
The supervisor integrates conflicting agent outputs.
