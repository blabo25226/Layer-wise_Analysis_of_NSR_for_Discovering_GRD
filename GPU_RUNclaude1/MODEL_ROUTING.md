# Claude Model and Agent Routing

## Principle

The Max plan provides enough usage headroom that scientific judgment should favor quality over aggressive token savings.

Use stable Claude Code model aliases in agent frontmatter:
- `opus`
- `sonnet`
- `haiku`

Aliases are preferred over hard-coded model IDs so that the configuration can follow the current model tier.

As of this campaign initialization, current Anthropic active tiers include Opus 5 and Sonnet 5. The files use aliases rather than version IDs.

## Recommended routing

### Opus
Use for tasks where a wrong judgment can invalidate research:
- research supervisor
- hypothesis generation
- methodology
- results interpretation
- statistical criticism
- reproducibility audit
- independent review
- replication decision

### Sonnet
Use for high-volume competent execution:
- implementation
- experiment operations
- report assembly
- artifact curation

### Haiku
Optional for low-level extraction only:
- log scanning
- locating files
- mechanical aggregation

Do not use Haiku as the final scientific decision-maker.

## Escalation

A Sonnet subagent should return to the Opus supervisor when:
- a preregistered assumption breaks
- multiple plausible interpretations remain
- a test leak is suspected
- an experiment must be redesigned
- a surprising result appears
- a major code change changes scientific meaning
