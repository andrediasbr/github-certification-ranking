#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Specialized script for fetching large countries with parallel page requests
"""

import csv
import json
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from certifications import (
    ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS,
    normalize_badge_name,
    request_with_retries,
    count_existing_rows,
)

EXCLUDED_BADGES = {
    'GitHub Sales Professional',
}

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
    url = f"https://www.credly.com/api/v1/users/{user_id}/external_badges/open_badges/public?page=1&page_size=48"
    
    try:
        response = request_with_retries(url, timeout=30)
        data = response.json()
        
        # Use set to track unique badge names and avoid duplicates
        unique_badge_names = set()
        for badge in data.get('data', []):
            external_badge = badge.get('external_badge', {})
            badge_name = external_badge.get('badge_name', '')
            issuer_name = external_badge.get('issuer_name', '')
            expires_at_date = badge.get('expires_at_date')
            
            # Check if it's an allowed GitHub certification issued by Microsoft and not expired
            if issuer_name == 'Microsoft' and badge_name.strip() in ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS:
                if not is_badge_expired(expires_at_date):
                    # Only count if badge name is unique (normalize to handle renamed badges)
                    unique_badge_names.add(normalize_badge_name(badge_name.strip()))
        
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
            url = f"https://www.credly.com/users/{user_id}/badges.json?page={page}&per_page=100"
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
                        if badge_name and badge_name not in EXCLUDED_BADGES:
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

    Returns (page, users, total_pages, ok) where ok is False when the page could
    not be fetched even after retries. Callers use ok to detect silently dropped
    pages instead of treating a failed page as an empty (but valid) result.
    """
    url = f"https://www.credly.com/api/v1/directory?organization_id=63074953-290b-4dce-86ce-ea04b4187219&sort=-total_badge_count&filter%5Blocation_name%5D={country.replace(' ', '%20')}&page={page}&format=json"
    
    try:
        response = request_with_retries(url, timeout=30)
        data = response.json()
        
        # Get total_pages from metadata
        metadata = data.get('metadata', {})
        total_pages = metadata.get('total_pages', 0)
        
        # Just return users with directory badge_count (may include expired)
        # We'll fetch detailed badges only for top candidates later
        users = data.get('data', [])
        
        return (page, users, total_pages, True)
    except Exception as e:
        print(f"  ❌ Error on page {page} after retries: {e}")
        return (page, [], 0, False)

def fetch_country_parallel(country, max_workers=20):
    """Fetch all pages for a country in parallel.

    Returns (all_users, failed_pages). failed_pages is non-empty when one or
    more pages could not be fetched after retries, signalling an incomplete run.
    """
    print(f"Fetching {country} with parallel requests...")
    
    # First, get the total number of pages
    _, _, total_pages, ok = fetch_page(country, 1)
    
    if not ok:
        print(f"❌ Could not fetch first page for {country} after retries")
        return [], [1]
    
    if total_pages == 0:
        print(f"No data found for {country}")
        return [], []
    
    print(f"Total pages: {total_pages}")
    
    all_users = []
    failed_pages = []
    
    # Fetch all pages in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_page, country, page): page 
                   for page in range(1, total_pages + 1)}
        
        completed = 0
        for future in as_completed(futures):
            page, users, _, ok = future.result()
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
    
    # Optimization: Only fetch detailed badges for top candidates
    # This reduces requests from thousands to ~50-100
    if all_users:
        # Sort by directory badge_count (includes expired) to get top candidates
        all_users_sorted = sorted(all_users, key=lambda x: x.get('badge_count', 0), reverse=True)
        
        # Take top 50 candidates (safety margin for ties, expired badges, and position-based ranking)
        # If fewer users, take all
        top_candidates = all_users_sorted[:min(50, len(all_users_sorted))]
        
        print(f"  Fetching detailed badges for top {len(top_candidates)} candidates (to check expiration)...")
        user_badge_counts = {}
        
        def fetch_all_badges(user_id):
            """Fetch both org badges and external badges, deduplicating by name across sources"""
            org_names = fetch_github_org_badges(user_id)
            external_names = fetch_github_external_badges(user_id)
            return len(org_names | external_names)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_user = {
                executor.submit(fetch_all_badges, user.get('id')): user.get('id')
                for user in top_candidates if user.get('id')
            }
            
            completed = 0
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    badge_count = future.result()
                    user_badge_counts[user_id] = badge_count
                    completed += 1
                except Exception as e:
                    print(f"    ⚠️  Error fetching badges for user {user_id}: {str(e)}")
                    user_badge_counts[user_id] = 0
        
        print(f"  Processed {len(user_badge_counts)} top candidates")
        
        # Update badge counts with valid (non-expired) badges only for top candidates
        # Keep original badge_count for others (they won't be in rankings anyway)
        for user in all_users:
            user_id = user.get('id')
            if user_id and user_id in user_badge_counts:
                user['badge_count'] = user_badge_counts[user_id]
    
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
        writer.writerow(['first_name', 'middle_name', 'last_name', 'badge_count', 'profile_url'])
        
        for user in users:
            writer.writerow([
                user.get('first_name', ''),
                user.get('middle_name', ''),
                user.get('last_name', ''),
                user.get('badge_count', 0),
                user.get('url', '')
            ])
    
    print(f"Saved to {output_file}")
    return output_file

def main():
    """Main execution"""
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
