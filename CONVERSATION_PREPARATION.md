# Conversation analysis — preparation only

Status: NOT ENABLED. Existing per-element structural checks continue unchanged.

## Scope to approve before implementation
- User selects a supported conversation in the genuine toolbar, explicitly opts in, and can stop at any time.
- No background conversation-history access, transcript export, account identity, contact details, typed text, cookies, or cloud/AI processing.
- A future adapter may expose only ephemeral opaque candidate IDs, standardized observed risk flags, and incomplete-coverage indicators, never raw message payloads.
- Keep a capped, coalesced queue and small yielding discovery batches; never accumulate an entire livestream or history.
- Clear state on Stop, navigation, conversation switch, and permission revocation; reject stale revisions before processing or rendering.
- Conversation-level claims (such as grooming, identity, or intent) require separate approval and validation; existing clues cannot establish them.

## Proposed interface, not a running API
`{scope: ephemeral ID, revision: integer, candidates: [{element_id, standardized_flags}], coverage: {truncated, candidates_scanned}}`

Scope IDs must be opaque, document-local, and never names, account IDs, or full URLs. Candidate and retained-result limits must be explicit and tested before enabling an adapter. No endpoint or additional collection is installed by this preparation.

## Acceptance gate
Synthetic fixtures only. Demonstrate bounded 10,000-message work, recycled-node/stale-revision rejection, no raw text in outbound traffic or storage, complete Stop cleanup, and cautious incomplete/error results before proposing activation.