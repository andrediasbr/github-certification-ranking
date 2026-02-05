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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Use set to track unique badge names and avoid duplicates
        unique_badge_names = set()
        for badge in data.get('data', []):
            external_badge = badge.get('external_badge', {})
            badge_name = external_badge.get('badge_name', '')
            issuer_name = external_badge.get('issuer_name', '')
            expires_at_date = badge.get('expires_at_date')
            
            # Check if it's a GitHub certification issued by Microsoft and not expired
            if issuer_name == 'Microsoft' and 'GitHub' in badge_name:
                if not is_badge_expired(expires_at_date):
                    # Only count if badge name is unique
                    unique_badge_names.add(badge_name)
        
        return len(unique_badge_names)
    except Exception as e:
        # If external badges endpoint fails, return 0 (user may have no external badges)
        print(f"    ⚠️  Warning: Failed to fetch external badges for user {user_id}: {str(e)}")
        return 0

# DevOps badge patterns (from Microsoft org in Credly)
DEVOPS_BADGE_PATTERNS = {
    'az-400': 'AZ-400: Designing and Implementing Microsoft DevOps Solutions',
    'devops engineer expert': 'Microsoft Certified: DevOps Engineer Expert',
}

def fetch_devops_badges(user_id):
    """Fetch Microsoft DevOps badges from regular badges API, excluding expired ones"""
    unique_badge_names = set()
    page = 1
    
    try:
        while True:
            url = f"https://www.credly.com/users/{user_id}/badges.json?page={page}&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            badges = data.get('data', [])
            if not badges:
                break
            
            for badge in badges:
                # Check if badge is from Microsoft organization
                issuer = badge.get('issuer', {})
                entities = issuer.get('entities', [])
                is_microsoft_org = False
                
                for entity in entities:
                    org_data = entity.get('entity', {})
                    org_name = org_data.get('name', '').lower()
                    if org_name == 'microsoft':
                        is_microsoft_org = True
                        break
                
                if is_microsoft_org:
                    badge_template = badge.get('badge_template', {})
                    badge_name = badge_template.get('name', '')
                    badge_name_lower = badge_name.lower()
                    
                    # Check if it's a DevOps badge
                    is_devops_badge = False
                    for pattern in DEVOPS_BADGE_PATTERNS.keys():
                        if pattern in badge_name_lower:
                            is_devops_badge = True
                            break
                    
                    if is_devops_badge:
                        expires_at_date = badge.get('expires_at_date')
                        if not is_badge_expired(expires_at_date):
                            unique_badge_names.add(badge_name)
            
            page += 1
            
            # Safety limit to avoid infinite loops
            if page > 10:
                break
        
        return len(unique_badge_names)
    except Exception as e:
        print(f"    ⚠️  Warning: Failed to fetch DevOps badges for user {user_id}: {str(e)}")
        return 0

def fetch_github_org_badges(user_id):
    """Fetch GitHub badges issued directly by GitHub org, excluding expired ones and duplicates"""
    # Use set to track unique badge names and avoid duplicates
    unique_badge_names = set()
    page = 1
    
    try:
        while True:
            url = f"https://www.credly.com/users/{user_id}/badges.json?page={page}&per_page=100"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
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
                        # Get badge name and only count if unique
                        badge_template = badge.get('badge_template', {})
                        badge_name = badge_template.get('name', '')
                        if badge_name:
                            unique_badge_names.add(badge_name)
            
            page += 1
            
            # Safety limit to avoid infinite loops
            if page > 10:
                break
        
        return len(unique_badge_names)
    except Exception as e:
        # If badges endpoint fails, return 0
        print(f"    ⚠️  Warning: Failed to fetch org badges for user {user_id}: {str(e)}")
        return 0

def fetch_country_data(country):
    """Fetch all data for a country"""
    base_url = f"https://www.credly.com/api/v1/directory?organization_id=63074953-290b-4dce-86ce-ea04b4187219&sort=alphabetical&filter%5Blocation_name%5D={country.replace(' ', '%20')}&page="
    
    all_users = []
    page = 1
    
    print(f"Fetching data for {country}...")
    
    while True:
        url = f"{base_url}{page}&format=json"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            users = data.get('data', [])
            if not users:
                break
            
            all_users.extend(users)
            print(f"  Page {page}: {len(users)} users")
            page += 1
            
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
    
    # Optimization: Only fetch detailed badges for top candidates
    # This reduces requests from thousands to ~50-100
    if all_users:
        # Sort by directory badge_count (includes expired) to get top candidates
        all_users_sorted = sorted(all_users, key=lambda x: x.get('badge_count', 0), reverse=True)
        
        # Take top 30 candidates (with safety margin for ties and expired badges)
        # If fewer users, take all
        top_candidates = all_users_sorted[:min(30, len(all_users_sorted))]
        
        print(f"  Fetching detailed badges for top {len(top_candidates)} candidates (to check expiration)...")
        user_badge_counts = {}
        
        def fetch_all_badges(user_id):
            """Fetch org badges, external badges, and DevOps badges"""
            org_count = fetch_github_org_badges(user_id)
            external_count = fetch_github_external_badges(user_id)
            devops_count = fetch_devops_badges(user_id)
            return org_count + external_count + devops_count
        
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
    
    return all_users

def save_to_csv(country, users, output_dir='datasource'):
    """Save users to CSV file, preserving existing mslearn_url and is_mvp values"""
    os.makedirs(output_dir, exist_ok=True)
    
    file_suffix = country.lower().replace(' ', '-')
    output_file = f"{output_dir}/github-certs-{file_suffix}.csv"
    
    # Load existing mslearn_url and is_mvp values to preserve them
    existing_mslearn_urls = {}
    existing_mvp_status = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    profile_url = row.get('profile_url', '').strip()
                    mslearn_url = row.get('mslearn_url', '').strip()
                    is_mvp = row.get('is_mvp', '').strip()
                    if profile_url:
                        if mslearn_url:
                            existing_mslearn_urls[profile_url] = mslearn_url
                        if is_mvp:
                            existing_mvp_status[profile_url] = is_mvp
            preserved_count = len(existing_mslearn_urls) + len(existing_mvp_status)
            if preserved_count > 0:
                print(f"  Preserving {len(existing_mslearn_urls)} MS Learn URLs and {len(existing_mvp_status)} MVP statuses")
        except Exception as e:
            print(f"  Warning: Could not read existing CSV for data preservation: {e}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['first_name', 'middle_name', 'last_name', 'badge_count', 'profile_url', 'mslearn_url', 'is_mvp'])
        
        for user in users:
            profile_url = user.get('url', '')
            # Preserve existing mslearn_url and is_mvp if available
            mslearn_url = existing_mslearn_urls.get(profile_url, user.get('mslearn_url', ''))
            is_mvp = existing_mvp_status.get(profile_url, user.get('is_mvp', ''))
            
            writer.writerow([
                user.get('first_name', ''),
                user.get('middle_name', ''),
                user.get('last_name', ''),
                user.get('badge_count', 0),
                profile_url,
                mslearn_url,
                is_mvp
            ])
    
    print(f"\nSaved to {output_file}")
    return output_file

def main():
    """Main execution"""
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
    
    users = fetch_country_data(country)
    
    # Always save CSV, even if empty (to maintain consistency)
    save_to_csv(country, users)
    print()
    print("=" * 80)
    print(f"✅ Success! Downloaded {len(users)} users")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    sys.exit(0)

if __name__ == "__main__":
    main()
