# Model and Agent Routing

Use quality-first routing because this campaign is expected to run under a Claude Max plan.

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
