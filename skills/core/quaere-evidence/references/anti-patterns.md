# Common drift modes + anti-patterns for evidence-gated review

How confirmation bias slips back in even with the gate loaded: rationalizations that look like investigation but skip falsifier / defense / disconfirming probe, and the recurring shapes that fail. See `../SKILL.md` for the gate each entry below is contrasting against.


| Rationalization | What's actually happening |
| --- | --- |
| "This claim looks plausible — I can act." | Plausibility is a prior, not a Defense. Plausible-looking claims still need a source-context contradiction-check (does the existing code already enforce what the claim says is missing?) and an explicit rebuttal before they can survive Decision. |
| "I found three clues that support this cause." | Supporting clues do not discriminate. Ask what would falsify the cause or distinguish it from the next-best hypothesis. |
| "The test passed after my patch, so root cause is confirmed." | A green test may be coincidence or symptom masking. The targeted probe should fail for the original cause and pass for the fix, or the claim remains weaker than it sounds. |
| "This is obviously a single root cause." | Many incidents are combinations. Model contributing factors or AND/OR preconditions when one linear story leaves gaps. |
| "5 Whys found the cause." | RCA tools generate candidate causes; probes confirm them. A tidy chain without evidence is just a story. |
| "The claim is too risky to test, so I'll decide from reasoning." | Unsafe probes should become safe substitutes or approval requests. If neither is possible, mark `inconclusive`, not `confirmed`. |
| "Confidence: high" | Confidence without a qualifier, rebuttal, and disconfirming result is tone, not evidence. State why the evidence should move belief. |
| "No time for the ledger." | Use challenge-pass mode, but keep the falsifier and decision. The ledger can shrink; the gate cannot disappear. |

## Anti-patterns (each item explains why it fails)

- **Patch-first debugging.** Editing before a falsifiable hypothesis fails because any green result afterward is ambiguous: the patch may fix the root cause, mask the symptom, or merely perturb timing.
- **Review-comment laundering.** Turning a reviewer's concern into your own confirmed finding fails because consensus is not proof. The concern must survive source context, rebuttal, and probe.
- **Evidence as decoration.** Listing logs after deciding what they mean fails because the observations were not allowed to change the decision. Findings precede interpretation so counter-evidence can steer the investigation.
- **Broad suite as proof of cause.** Full tests are valuable regression checks, but they rarely isolate why a bug happened. Use the targeted check to prove the cause/risk, then the broad suite to guard side effects.
- **Forced certainty.** Some investigations end `inconclusive`. That is a useful result when the alternative is inventing a confident but unsupported patch.
