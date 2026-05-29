# Mutation passes — operator catalog

Step 4 of the invention probe generates candidates by forcing a *named mechanism*
against a *named assumption* (from step 3). Use at least four different operators —
four samples of the same operator is volume, not divergence. Each operator below has
a one-line definition and a worked mini-example against a running default.

Running default for the examples: **"add a rate limiter to the API to stop abuse"**
(assumption A1: abuse is best stopped at request time; A2: the limit is per-user;
A3: the cost we care about is server load).

## Inversion — make the opposite of the default useful

Take the default's core action and ask what its inverse would buy.

- Example: instead of *limiting* requests, *invite* them — expose a cheap, generous
  read replica / cache tier so abuse traffic lands somewhere harmless and the
  expensive path stays untouched. Breaks A1 (stop at request time → absorb, don't
  stop).

## Subtraction — remove a part assumed necessary

Delete a component the default treats as required and see if the system still works.

- Example: remove per-user identity from the limit entirely; shape traffic by
  *cost of the operation* not *who sent it*. Breaks A2 (per-user → per-cost).

## Transfer — import a structure from another domain

Borrow a mechanism that solved a structurally similar problem elsewhere.

- Example: import congestion pricing from road traffic — price requests dynamically
  by current load instead of a hard cap. Breaks A1 + A3 (binary block → continuous
  price; load → willingness-to-pay).

## Recomposition — split the system and reconnect it differently

Break the system into parts and wire them in a new order or topology.

- Example: split "authenticate" and "admit" — admit everyone to a queue, authenticate
  lazily only when the expensive resource is about to be touched. Breaks A1 (gate at
  entry → gate at the expensive step).

## Constraint shift — optimize a different bottleneck

Change which constraint the design is built around.

- Example: the real bottleneck is not server load but a downstream paid API quota;
  optimize for *that* quota, and server-side limiting becomes irrelevant. Breaks A3
  (server load → external quota).

## Adversarial design — assume the obvious solution will be gamed

Assume a motivated attacker defeats the default, and design for the world after that.

- Example: a per-user rate limit is trivially beaten by rotating accounts; design
  around proof-of-work or cost-to-attacker instead, so abuse is self-limiting
  economically. Breaks A2 (per-user identity is forgeable).

## Temporal shift — move work earlier, later, or into a background loop

Change *when* the work happens.

- Example: do not limit at request time at all; reconcile asynchronously — accept
  everything, detect abuse in a background pass, and claw back / bill later. Breaks
  A1 (synchronous gate → asynchronous reconciliation).

## Using the catalog

- Pick operators that attack *different* assumptions; if three operators all break A1,
  you have explored one axis, not four.
- Each candidate must still name broken assumption / mechanism / expected gain /
  likely failure mode (SKILL.md step 4). An operator that produces a candidate you
  cannot fill those four for is a dead end — drop it.
- Operators combine (Transfer + Constraint shift gave congestion pricing). Naming both
  is fine; naming neither is the drift.
