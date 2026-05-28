# Common drift modes + anti-patterns for external grounding

Grounding-side rationalizations that look like verification but skip either source-quality or claim-credibility, and the recurring shapes that produce `confirmed` labels without one of the two axes. See `../SKILL.md` for the dual-axis gate each entry below is contrasting against.


| Rationalization | What's actually happening |
| --- | --- |
| "I recall this API as `foo.bar(...)`." | Model memory is not evidence. SOTA LLMs follow internal priors even after retrieval (GitChameleon, RustEvo²). Run an executable probe before answering. |
| "The docs say X — that's enough for `confirmed`." | Authority without claim-credibility (SIFT/Admiralty). Find a lateral corroborator and run the probe before promoting. |
| "The latest docs describe this option." | Latest docs describe the latest release. Anchor the local version first; latest docs are `version-mismatched` for projects not on latest. |
| "It's vendored in the repo, so it must be current." | Vendored docs decay (Tan/Treude 2024). Check `mtime(doc) > mtime(symbol)`; a stale vendored doc next to a recently refactored symbol is `stale`. |
| "Single-axis acceptance is enough." | Three sub-cases collapse to the same drift: (a) single official source with no lateral check (`inconclusive`, not `confirmed`); (b) probe runs green but no lateral check on what the source actually claims (`single-source` masked as `confirmed`); (c) authority is high so no probe (the 14-tier ranking is necessary, not sufficient). All three need the missing axis filled. |
| "The model name the user mentioned doesn't exist — typo?" | Knowledge-cutoff bias (Class F), first-encounter form. Default assumption: unfamiliar names post-date training cutoff. Verify before correcting. |
| "I corrected this name once already, the user is wrong." | Knowledge-cutoff bias (Class F), persistence form. Across a multi-turn chat the agent re-flags a name it already accepted, because the parametric prior reasserts itself. Once a name has been verified or accepted in this session, do not re-correct it on subsequent turns without new evidence. |
| "`package.json` says X, so X is what's installed." | Transitive resolution can pin Y instead of X due to peer-dep constraints, version overrides, or workspace-level resolutions. The local anchor is the resolved lockfile entry, not the manifest declaration. Read `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` for the actual resolved version. |

## Anti-patterns (each item explains why it fails)

- **Treating model memory as evidence.** Training data ages; SOTA LLMs hit 48–51% on version-conditioned generation. Memory fails because it cannot distinguish "I remember this from the docs" from "I remember this from a deprecated tutorial." The executable probe is what disambiguates retrieval from reality.

- **Knowledge-cutoff "correction".** Flagging a current name as a typo because it does not appear in training data. Fails because the training cutoff truncates evidence, not reality. The user is more likely current than the agent on names that post-date training.

- **Conflating source authority with claim correctness.** A high-authority source describing a different version than the local anchor is still wrong for the local project. Authority is necessary; source-supports-claim plus version fit is what makes it sufficient *(NATO Admiralty Code; SIFT)*.

- **Treating retrieval as confirmation.** RAG retrieves; it does not verify. Even with retrieved docs, models follow internal priors *(GitChameleon 2.0)*. Retrieval enables the probe; the probe is the verification.

- **Promoting single-source claims to `confirmed`.** SIFT (Wineburg/Caulfield 2017–2019) shows empirically that single-source acceptance is the failure mode of internet-era literacy. Find a second source or run an independent probe before promoting.
