# Context Engineering

Agent Forge optimizes for restartability and high signal, not prompt bulk.

## Priority Order

1. Read the smallest durable truth surface first.
2. Load rich skills only when the task actually needs them.
3. Convert long research or implementation sessions into compact artifacts.
4. Hand off artifacts, not whole transcripts.

## Artifacts Over Chat History

Preferred artifacts:

- task brief
- evidence pack
- implementation brief
- scorecard
- handoff

## Model Escalation

Use a premium model when:

- the problem is broad, ambiguous, or source-heavy
- multiple artifacts need to be designed coherently
- a framework or doctrine decision will shape many future runs

Drop to a cheaper model when:

- the brief is decision complete
- the repo surface is already grounded
- the task is mostly execution or verification

## Compaction Rules

- keep goals, constraints, and acceptance criteria at the top
- keep unresolved questions explicit
- link or reference sources instead of repeating them
- remove narrative that does not change the next decision

## When To Compact

Trigger compaction at these moments:

- After a research phase completes — convert raw findings into an evidence pack before planning begins.
- Before switching teams — the new team should receive an artifact, not the old team's full context.
- Before handing off to a cheaper model — compress the brief to be self-contained at lower context budgets.
- When conversation has exceeded ~20 tool calls — signal that accumulated context is growing; produce a handoff or brief.
- After completing a meaningful work chunk — don't wait for the session to end; compact incrementally.

Compaction output should be one of the preferred artifacts (task brief, evidence pack, implementation brief, handoff).

## Failure Modes

- too many global skills in every project
- repeating the same repo facts in every prompt
- planning and review mixed into one worker
- long research notes handed to builders without triage
