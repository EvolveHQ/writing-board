# Run an authorized queue item

Read root `AGENT.md`, `.docflow/CONVENTIONS.md`, the catalog, and the lowest
numbered pending plan covered by the current assignment. Follow the relevant
decision's acceptance criteria. Unrelated queued work is not implicitly authorized.

Implement and run `python scripts/verify.py`. Resolve failures before committing.
Use signed Conventional Commits and the required decision rationale footer.
The sole integrator stages and commits; helpers keep to their assigned paths.

After the implementation commit, record its SHA in the plan completion footer,
move the plan into `done/`, update decision status and revision/approval rows,
and regenerate the catalog. Commit those completion changes separately. Push
only within the task's publication authorization. Successful push completes the
item. Do not amend the completion commit to make its footer name itself.

Stop when authorized scope is complete, the queue is empty, or a missing
dependency prevents progress. Report unresolved failures precisely. Never bypass
the verification gate, silently change the chosen integration policy or continue
unrelated work because it happens to be next in the queue.
