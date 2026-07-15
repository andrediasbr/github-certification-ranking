#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared certification allowlists and resilient fetch helpers.
"""

import os
import time

import requests

# HTTP status codes worth retrying (rate limiting + transient server errors).
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def request_with_retries(url, timeout=30, max_retries=3, base_delay=3):
    """GET a URL with retries and exponential backoff on transient failures.

    Retries on connection/timeout/SSL errors and on retryable HTTP status codes
    (429, 500, 502, 503, 504). Non-retryable HTTP errors (e.g. 404) raise
    immediately. Raises the last exception if every attempt fails so callers can
    distinguish a genuine failure from an empty-but-successful response.
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code in RETRYABLE_STATUS:
                raise requests.HTTPError(
                    f"{response.status_code} Server Error", response=response
                )
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            last_exc = e
            if status in RETRYABLE_STATUS and attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
        except (requests.ConnectionError, requests.Timeout) as e:
            # requests.exceptions.SSLError subclasses ConnectionError, so
            # transient TLS handshake failures are retried here too.
            last_exc = e
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
    raise last_exc


def count_existing_rows(csv_path):
    """Return the number of data rows (excluding header) in an existing CSV.

    Returns 0 when the file is missing or unreadable. Used to guard against
    overwriting good data with a smaller/degraded dataset from a failed run.
    """
    if not os.path.exists(csv_path):
        return 0
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


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
    'Microsoft Applied Skills: Manage GitHub secret scanning with GitHub Copilot',
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
