#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch GitHub Certifications for a single country
Includes both verified (GitHub org) and unverified (Microsoft external) badges
"""

import csv
import json
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from certifications import (
    ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS,
    normalize_badge_name,
    request_with_retries,
    count_existing_rows,
    is_excluded_badge,
    get_badge_expiry_date,
    is_badge_expired,
    fetch_user_company,
    configure_utf8_output,
)

def fetch_github_external_badges(user_id):
    """Fetch GitHub external badges (Microsoft-issued) for a user, excluding expired ones and duplicates"""
    # Use set to track unique badge names and avoid duplicates
    unique_badge_names = set()
    page = 1
    
    try:
        total_pages = 1  # updated from page-1 metadata to skip a trailing empty-page fetch
        while page <= total_pages:
            url = f"https://www.credly.com/api/v1/users/{user_id}/external_badges/open_badges/public?page={page}&page_size=100"
            response = request_with_retries(url, timeout=30)
            data = response.json()
            total_pages = min(data.get('metadata', {}).get('total_pages', 1) or 1, 10)
            
            badges = data.get('data', [])
            if not badges:
                break
            
            for badge in badges:
                external_badge = badge.get('external_badge', {})
                badge_name = external_badge.get('badge_name', '')
                issuer_name = external_badge.get('issuer_name', '')
                expires_at_date = get_badge_expiry_date(badge)
                
                # Check if it's an allowed GitHub certification issued by Microsoft and not expired
                if issuer_name == 'Microsoft' and badge_name.strip() in ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS:
                    if not is_badge_expired(expires_at_date):
                        # Only count if badge name is unique (normalize to handle renamed badges)
                        unique_badge_names.add(normalize_badge_name(badge_name.strip()))
            
            page += 1
        
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
        total_pages = 1  # updated from page-1 metadata to skip a trailing empty-page fetch
        while page <= total_pages:
            url = f"https://www.credly.com/users/{user_id}/badges.json?page={page}&per_page=48"
            response = request_with_retries(url, timeout=30)
            data = response.json()
            total_pages = min(data.get('metadata', {}).get('total_pages', 1) or 1, 10)
            
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
        
        return unique_badge_names
    except Exception as e:
        # If badges endpoint fails, return empty set
        print(f"    ⚠️  Warning: Failed to fetch org badges for user {user_id}: {str(e)}")
        return set()

def fetch_country_data(country):
    """Fetch all data for a country"""
    base_url = f"https://www.credly.com/api/v1/directory?organization_id=63074953-290b-4dce-86ce-ea04b4187219&sort=-total_badge_count&filter%5Blocation_name%5D={country.replace(' ', '%20')}&per=50&page="
    
    all_users = []
    page = 1
    incomplete = False
    
    print(f"Fetching data for {country}...")
    
    while True:
        url = f"{base_url}{page}&format=json"
        
        try:
            response = request_with_retries(url, timeout=30)
            data = response.json()
            
            users = data.get('data', [])
            if not users:
                break
            
            all_users.extend(users)
            print(f"  Page {page}: {len(users)} users")
            page += 1
            
        except Exception as e:
            # Page failed even after retries. Mark the run incomplete so the
            # caller preserves the previous CSV instead of dropping users.
            print(f"  ❌ Error on page {page} after retries: {e}")
            incomplete = True
            break
    
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
        with ThreadPoolExecutor(max_workers=10) as executor:
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

    return all_users, incomplete

def save_to_csv(country, users, output_dir='datasource', incomplete=False):
    """Save users to CSV file.

    Safeguard: never overwrite an existing CSV with a degraded dataset. If the
    run was incomplete (a page failed after retries) or the new dataset is
    substantially smaller than what is already on disk, keep the previous file
    so users are not silently dropped from the ranking. Returns the output path
    on success, or None when the write was skipped to preserve good data.
    """
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
    
    print(f"\nSaved to {output_file}")
    return output_file

def main():
    """Main execution"""
    configure_utf8_output()
    if len(sys.argv) < 2:
        print("Usage: ./fetch_country.py <country_name>")
        print("Example: ./fetch_country.py Brazil")
        print("         ./fetch_country.py \"United States\"")
        sys.exit(1)
    
    country = sys.argv[1]
    
    print("=" * 80)
    print(f"Fetching GitHub certifications for: {country}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    users, incomplete = fetch_country_data(country)
    
    # Preserve previous CSV when the run is incomplete or degraded.
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

if __name__ == "__main__":
    main()
