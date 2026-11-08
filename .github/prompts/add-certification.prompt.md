---
description: "Add or exclude a GitHub certification from the ranking system"
agent: "agent"
argument-hint: "Action and certification name (e.g., 'exclude GitHub Sales Professional' or 'allow GitHub Copilot')"
---
Manage certifications in the ranking system:

**To allow a new Microsoft-issued certification**: Add it to the `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS` set in `certifications.py`.

**To exclude a certification from rankings**: Add it to the `EXCLUDED_BADGES` set in `certifications.py`. Use this for certifications that can no longer be earned or badges that are not certifications. For whole families of award badges, add a name prefix to `EXCLUDED_BADGE_PREFIXES` instead.

**To handle a renamed badge**: Map the old name to the current name in `BADGE_NAME_ALIASES` in `certifications.py` so it is not counted twice.

**To stop a certification from expiring**: Add it to `NON_EXPIRING_BADGES` in `certifications.py`.

The certification name must match exactly as it appears on Credly. `certifications.py` is the single source of truth; the fetch scripts and `generate_rankings.py` import these sets. Update the badge lists in `README.md` when the set of tracked certifications changes.
