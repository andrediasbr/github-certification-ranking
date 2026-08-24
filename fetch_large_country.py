#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Specialized script for fetching large countries with parallel page requests
"""

import csv
import json
import sys
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from certifications import (
    ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS,
    normalize_badge_name,
    request_with_retries,
    count_existing_rows,
    is_excluded_badge,
    fetch_user_company,
    configure_utf8_output,
)

def is_badge_expired(expires_at_date):
    """Check if a badge is expired based on expires_at_date"""
    if not expires_at_date:  # null = never expires
        return False
    
    try:
        # Parse date string (format: "YYYY-MM-DD")
        expiration_date = datetime.strptime(expires_at_date, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        return expiration_date < current_date
    except Exception:
        # If we can't parse the date, assume not expired to avoid false positives
        return False

def fetch_github_external_badges(user_id):
    """Fetch GitHub external badges (Microsoft-issued) for a user, excluding expired ones and duplicates"""
    # Use set to track unique badge names and avoid duplicates
    unique_badge_names = set()
    page = 1
    
    try:
        while True:
            url = f"https://www.credly.com/api/v1/users/{user_id}/external_badges/open_badges/public?page={page}&page_size=100"
            response = request_with_retries(url, timeout=30)
            data = response.json()
            
            badges = data.get('data', [])
            if not badges:
                break
            
            for badge in badges:
                external_badge = badge.get('external_badge', {})
                badge_name = external_badge.get('badge_name', '')
                issuer_name = external_badge.get('issuer_name', '')
                expires_at_date = external_badge.get('expires_at_date')
                
                # Check if it's an allowed GitHub certification issued by Microsoft and not expired
                if issuer_name == 'Microsoft' and badge_name.strip() in ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS:
                    if not is_badge_expired(expires_at_date):
                        # Only count if badge name is unique (normalize to handle renamed badges)
                        unique_badge_names.add(normalize_badge_name(badge_name.strip()))
            
            page += 1
            
            # Safety limit to avoid infinite loops
            if page > 10:
                break
        
        return unique_badge_names
    except Exception as e:
        # If external badges endpoint fails, return empty set (user may have no external badges)
        print(f"    ⚠️  Warning: Failed to fetch external badges for user {user_id}: {str(e)}")
        return set()

def fetch_github_org_badges(user_id):
    """Fetch GitHub badges issued directly by GitHub org, excluding expired ones and duplicates"""
    # Use set to track unique badge names and avoid duplicates
    unique_badge_names = set()
    page = 1
    
    try:
        while True:
            url = f"https://www.credly.com/users/{user_id}/badges.json?page={page}&per_page=48"
            response = request_with_retries(url, timeout=30)
            data = response.json()
            
            badges = data.get('data', [])
            if not badges:
                break
            
            # Count only non-expired badges from GitHub organization
            for badge in badges:
                # Check if badge is from GitHub organization
                issuer = badge.get('issuer', {})
                entities = issuer.get('entities', [])
                is_github_org = False
                
                for entity in entities:
                    org_data = entity.get('entity', {})
                    if org_data.get('id') == '63074953-290b-4dce-86ce-ea04b4187219':  # GitHub org ID
                        is_github_org = True
                        break
                
                if is_github_org:
                    expires_at_date = badge.get('expires_at_date')
                    if not is_badge_expired(expires_at_date):
                        # Get badge name and only count if unique and not excluded
                        badge_template = badge.get('badge_template', {})
                        badge_name = badge_template.get('name', '')
                        if badge_name and not is_excluded_badge(badge_name):
                            unique_badge_names.add(badge_name)
            
            page += 1
            
            # Safety limit to avoid infinite loops
            if page > 10:
                break
        
        return unique_badge_names
    except Exception as e:
        # If badges endpoint fails, return empty set
        print(f"    ⚠️  Warning: Failed to fetch org badges for user {user_id}: {str(e)}")
        return set()

def fetch_page(country, page):
    """Fetch a single page for a country (without detailed badge fetching), with retries.

    Returns (page, users, total_pages, total_count, ok) where ok is False when the
    page could not be fetched even after retries. total_count exposes the
    directory's reported size so the caller can detect the 10,000-result cap.
    Callers use ok to detect silently dropped pages instead of treating a failed
    page as an empty (but valid) result.
    """
    url = f"https://www.credly.com/api/v1/directory?organization_id=63074953-290b-4dce-86ce-ea04b4187219&sort=-total_badge_count&filter%5Blocation_name%5D={country.replace(' ', '%20')}&per=50&page={page}&format=json"
    
    try:
        response = request_with_retries(url, timeout=30)
        data = response.json()
        
        # Get pagination info from metadata
        metadata = data.get('metadata', {})
        total_pages = metadata.get('total_pages', 0)
        total_count = metadata.get('total_count', 0)
        
        # Just return users with directory badge_count (may include expired)
        # We'll fetch detailed badges only for top candidates later
        users = data.get('data', [])
        
        return (page, users, total_pages, total_count, True)
    except Exception as e:
        print(f"  ❌ Error on page {page} after retries: {e}")
        return (page, [], 0, 0, False)

def fetch_org_badge_names():
    """Return every badge name issued by the GitHub org (certs, credentials, awards).

    Used to enumerate users in locations that exceed the directory's 10,000-result
    cap: no single badge exceeds the cap, so iterating each badge and deduping
    recovers the full user set.
    """
    url = "https://www.credly.com/api/v1/directory/search/badge?query=&organization_id=63074953-290b-4dce-86ce-ea04b4187219"
    try:
        response = request_with_retries(url, timeout=30)
        return response.json().get('data', {}).get('search_results', [])
    except Exception as e:
        print(f"  ❌ Failed to fetch org badge names: {e}")
        return []


def fetch_badge_page(country, badge_name, page):
    """Fetch one page of a location filtered by a single badge, sorted by recent activity.

    Sorting by -activity_date keeps the most recently active earners first, so if
    a badge ever did exceed the cap the freshest data is retained. Returns
    (page, users, total_pages, ok).
    """
    url = (
        "https://www.credly.com/api/v1/directory"
        "?organization_id=63074953-290b-4dce-86ce-ea04b4187219"
        f"&filter%5Blocation_name%5D={quote(country)}"
        f"&filter%5Bbadge_name%5D={quote(badge_name)}"
        f"&sort=-activity_date&per=50&page={page}&format=json"
    )
    try:
        response = request_with_retries(url, timeout=30)
        data = response.json()
        total_pages = data.get('metadata', {}).get('total_pages', 0)
        return (page, data.get('data', []), total_pages, True)
    except Exception as e:
        print(f"    ❌ Error on '{badge_name}' page {page} after retries: {e}")
        return (page, [], 0, False)


def fetch_country_by_badges(country, max_workers=20):
    """Enumerate every user in a location that exceeds the 10,000-result cap.

    Credly silently drops results past 10,000 in the plain location listing. We
    instead query the location filtered by each org badge (none exceeds the cap)
    and dedupe by user id to recover the complete set. Returns
    (all_users, incomplete) where incomplete is True if any page failed after
    retries, so the caller can preserve the previous CSV.
    """
    badge_names = fetch_org_badge_names()
    if not badge_names:
        print("  ❌ No badge names returned; cannot enumerate users.")
        return [], True

    # Page through every valid GitHub org badge (certifications AND sales/delivery
    # credentials), skipping only the community/award badges in EXCLUDED_BADGES.
    # Enumerating all valid badges recovers users who hold a sales credential
    # alongside (or instead of) a real certification, so no earner is dropped.
    badge_names = [b for b in badge_names if not is_excluded_badge(b.strip())]
    if not badge_names:
        print("  ❌ No valid badges to enumerate.")
        return [], True

    print(f"  Enumerating {len(badge_names)} valid badges for {country}: {', '.join(badge_names)}")
    users_by_id = {}
    incomplete = False

    # Phase 1: first page of each badge to learn its page count (and collect page-1 users).
    badge_total_pages = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_badge_page, country, b, 1): b for b in badge_names}
        for future in as_completed(futures):
            badge_name = futures[future]
            _page, users, total_pages, ok = future.result()
            if not ok:
                incomplete = True
                continue
            badge_total_pages[badge_name] = total_pages
            for u in users:
                uid = u.get('id')
                if uid and uid not in users_by_id:
                    users_by_id[uid] = u

    # Phase 2: remaining pages of every badge, all in one pool for max throughput.
    tasks = [(b, p) for b, tp in badge_total_pages.items() for p in range(2, tp + 1)]
    if tasks:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_badge_page, country, b, p): (b, p) for b, p in tasks}
            completed = 0
            for future in as_completed(futures):
                _page, users, _tp, ok = future.result()
                if not ok:
                    incomplete = True
                else:
                    for u in users:
                        uid = u.get('id')
                        if uid and uid not in users_by_id:
                            users_by_id[uid] = u
                completed += 1
                if completed % 200 == 0:
                    print(f"  Progress: {completed}/{len(tasks)} badge-pages ({len(users_by_id)} unique users)")

    print(f"  ✓ Enumerated {len(users_by_id)} unique users across {len(badge_names)} badges")
    return list(users_by_id.values()), incomplete


def fetch_country_parallel(country, max_workers=20):
    """Fetch all pages for a country in parallel.

    Returns (all_users, failed_pages). failed_pages is non-empty when one or
    more pages could not be fetched after retries, signalling an incomplete run.
    """
    print(f"Fetching {country} with parallel requests...")
    
    # First page tells us the page count and whether the location hits the
    # directory's 10,000-result cap.
    _, _, total_pages, total_count, ok = fetch_page(country, 1)
    
    if not ok:
        print(f"❌ Could not fetch first page for {country} after retries")
        return [], [1]
    
    if total_pages == 0:
        print(f"No data found for {country}")
        return [], []
    
    if total_count >= 10000:
        # Location is capped: enumerate per badge to recover every user.
        print(f"⚠️  {country} hits the 10,000-result directory cap "
              f"(total_count={total_count}); enumerating users per badge...")
        all_users, badge_incomplete = fetch_country_by_badges(country, max_workers=max_workers)
        failed_pages = ['badge-enumeration'] if badge_incomplete else []
        print(f"✓ Completed: {len(all_users)} unique users via per-badge enumeration")
    else:
        print(f"Total pages: {total_pages}")
        all_users = []
        failed_pages = []
        
        # Fetch all pages in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_page, country, page): page 
                       for page in range(1, total_pages + 1)}
            
            completed = 0
            for future in as_completed(futures):
                page, users, _, _, ok = future.result()
                if ok:
                    all_users.extend(users)
                else:
                    failed_pages.append(page)
                completed += 1
                
                if completed % 100 == 0:
                    print(f"  Progress: {completed}/{total_pages} pages ({len(all_users)} users)")
        
        if failed_pages:
            print(f"  ⚠️  {len(failed_pages)} page(s) failed after retries: {sorted(failed_pages)[:10]}")
        print(f"✓ Completed: {len(all_users)} users from {total_pages} pages")
    
    # Fetch detailed badges AND company for every user in a single pass. We
    # already pay one round-trip per user for the company lookup, so folding the
    # badge fetch into the same pass adds no extra passes while counting
    # Microsoft-issued (external) GitHub certs for everyone. A prior top-50
    # limit undercounted earners whose certs are mostly external, because the
    # directory badge_count only reflects verified GitHub-org badges.
    if all_users:
        def fetch_badges_and_company(user):
            """Populate valid (non-expired) badge_count and company for one user."""
            user_id = user.get('id')
            if user_id:
                org_names = fetch_github_org_badges(user_id)
                external_names = fetch_github_external_badges(user_id)
                user['badge_count'] = len(org_names | external_names)
            else:
                user['badge_count'] = 0
            try:
                user['company'] = fetch_user_company(user.get('url', '')) or ''
            except Exception:
                user['company'] = ''
            return user

        print(f"  Fetching detailed badges + company for {len(all_users)} users...")
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_user = {
                executor.submit(fetch_badges_and_company, user): user
                for user in all_users
            }
            total = len(future_to_user)
            completed = 0
            for future in as_completed(future_to_user):
                user = future_to_user[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"    ⚠️  Error processing user {user.get('id')}: {str(e)}")
                    user['badge_count'] = 0
                    user['company'] = ''
                completed += 1
                if completed % 500 == 0 or completed == total:
                    print(f"    Progress: {completed}/{total} users", flush=True)
    
    return all_users, failed_pages

def save_to_csv(country, users, output_dir='datasource', incomplete=False):
    """Save users to CSV file.

    Safeguard: never overwrite an existing CSV with a degraded dataset. If the
    run was incomplete (a page failed after retries) or the new dataset is
    substantially smaller than what is already on disk, keep the previous file
    so users are not silently dropped from the ranking. Returns the output path
    on success, or None when the write was skipped to preserve good data.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    file_suffix = country.lower().replace(' ', '-')
    output_file = f"{output_dir}/github-certs-{file_suffix}.csv"
    
    existing_count = count_existing_rows(output_file)
    new_count = len(users)
    
    if existing_count > 0 and (incomplete or new_count < existing_count * 0.9):
        print(
            f"🛑 Refusing to overwrite {output_file}: existing={existing_count}, "
            f"new={new_count}, incomplete={incomplete}. Keeping previous data "
            f"to avoid dropping users."
        )
        return None
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['first_name', 'middle_name', 'last_name', 'badge_count', 'profile_url', 'company'])
        
        for user in users:
            writer.writerow([
                user.get('first_name', ''),
                user.get('middle_name', ''),
                user.get('last_name', ''),
                user.get('badge_count', 0),
                user.get('url', ''),
                user.get('company', '')
            ])
    
    print(f"Saved to {output_file}")
    return output_file

def main():
    """Main execution"""
    configure_utf8_output()
    if len(sys.argv) < 2:
        print("Usage: ./fetch_large_country.py <country_name>")
        print("Example: ./fetch_large_country.py India")
        sys.exit(1)
    
    country = sys.argv[1]
    
    print("=" * 80)
    print(f"Fetching large country: {country}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Fetch with parallel requests (20 concurrent pages)
    users, failed_pages = fetch_country_parallel(country, max_workers=20)
    incomplete = len(failed_pages) > 0
    
    if users:
        saved = save_to_csv(country, users, incomplete=incomplete)
        if saved is None:
            print()
            print("=" * 80)
            print("❌ Incomplete run — kept previous CSV to avoid data loss")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            sys.exit(1)
        print()
        print("=" * 80)
        print(f"✅ Success! Downloaded {len(users)} users")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ No users found")
        sys.exit(1)

if __name__ == "__main__":
    main()
