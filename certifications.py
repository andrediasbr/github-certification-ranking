#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared certification allowlists.
"""

ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS = {
    'GitHub Copilot',
    'GitHub Actions',
    'GitHub Advanced Security',
    'GitHub Foundations',
    'GitHub Administration',
    'Microsoft Certified: DevOps Engineer Expert',
    'Microsoft Applied Skills: Accelerate AI-assisted development by using GitHub Copilot',
    'Microsoft Applied Skills: Accelerate app development by using GitHub Copilot',
    'Microsoft Applied Skills: Automate Azure Load Testing by using GitHub Actions',
    'Microsoft Applied Skills: Resolve GitHub issues by using GitHub Copilot',
}

# Map of renamed/duplicate badges to their canonical name.
# When Microsoft renames a badge, add the old name as key and the current name as value.
BADGE_NAME_ALIASES = {
    'Microsoft Applied Skills: Accelerate app development by using GitHub Copilot':
        'Microsoft Applied Skills: Accelerate AI-assisted development by using GitHub Copilot',
}


def normalize_badge_name(badge_name):
    """Normalize badge name to its canonical form to avoid counting renamed badges as duplicates."""
    return BADGE_NAME_ALIASES.get(badge_name, badge_name)
