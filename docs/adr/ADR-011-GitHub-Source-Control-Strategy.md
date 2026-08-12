Status: Accepted

Context
-------
The codebase appears to be hosted on GitHub (repository metadata attached). Development is organized into branches and changes are intended to be committed and pushed (evidence: `git push` in terminal history). Tests and CI should be run before merging.

Decision
--------
Use GitHub for source control, feature-branch workflows, and pull requests for code review. Keep main branch as the primary integration branch and use short-lived feature branches for development.

Consequences
------------
- Encourages code review and safer integration via PRs.
- Requires a policy for branch naming, PR review, and CI gatekeeping (not yet encoded in repository; to be added as CI config files).

Alternatives Considered
-----------------------
- Trunk-based development without PRs — rejected for this team due to preference for reviewable PRs.
