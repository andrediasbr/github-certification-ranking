---
description: "Add or exclude a GitHub certification from the ranking system"
agent: "agent"
argument-hint: "Action and certification name (e.g., 'exclude GitHub Sales Professional' or 'allow GitHub Copilot')"
---
Manage certifications in the ranking system:

**To allow a new Microsoft-issued certification**: Add it to the `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS` set in both `fetch_country.py` and `fetch_large_country.py`.

**To exclude a certification from rankings**: Add it to the `EXCLUDED_BADGES` set in both `fetch_country.py` and `fetch_large_country.py`. Use this for certifications that can no longer be earned.

The certification name must match exactly as it appears on Credly. Keep the sets in both files synchronized.
