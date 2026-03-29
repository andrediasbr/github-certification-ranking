#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate community-only ranking for Brazil
Excludes partner-exclusive certifications, keeping only community certifications:
- GitHub Administration
- GitHub Advanced Security
- GitHub Actions
- GitHub Copilot
- GitHub Foundations
- Microsoft Certified: DevOps Engineer Expert
- Microsoft Applied Skills (GitHub-related)
"""

import csv
import json
import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Community certifications allowed from GitHub org on Credly
ALLOWED_ORG_BADGES = {
    'GitHub Administration',
    'GitHub Advanced Security',
    'GitHub Actions',
    'GitHub Copilot',
    'GitHub Foundations',
}

# Community certifications allowed from Microsoft (external badges)
ALLOWED_MICROSOFT_BADGES = {
    'GitHub Copilot',
    'GitHub Actions',
    'GitHub Advanced Security',
    'GitHub Foundations',
    'GitHub Administration',
    'Microsoft Certified: DevOps Engineer Expert',
    'Microsoft Applied Skills: Accelerate AI-assisted development by using GitHub Copilot',
    'Microsoft Applied Skills: Accelerate app development by using GitHub Copilot',
    'Microsoft Applied Skills: Automate Azure Load Testing by using GitHub Actions',
}

GITHUB_ORG_ID = '63074953-290b-4dce-86ce-ea04b4187219'


def is_badge_expired(expires_at_date):
    """Check if a badge is expired based on expires_at_date"""
    if not expires_at_date:
        return False
    try:
        expiration_date = datetime.strptime(expires_at_date, "%Y-%m-%d").date()
        return expiration_date < datetime.now().date()
    except Exception:
        return False


def fetch_community_org_badges(user_id):
    """Fetch only community GitHub org badges (no partner certs)"""
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
                issuer = badge.get('issuer', {})
                entities = issuer.get('entities', [])
                is_github_org = any(
                    entity.get('entity', {}).get('id') == GITHUB_ORG_ID
                    for entity in entities
                )

                if is_github_org:
                    expires_at_date = badge.get('expires_at_date')
                    if not is_badge_expired(expires_at_date):
                        badge_name = badge.get('badge_template', {}).get('name', '')
                        if badge_name in ALLOWED_ORG_BADGES:
                            unique_badge_names.add(badge_name)

            page += 1
            if page > 10:
                break

        return unique_badge_names
    except Exception as e:
        print(f"    ⚠️  Warning: Failed to fetch org badges for user {user_id}: {e}")
        return set()


def fetch_community_external_badges(user_id):
    """Fetch community external badges (Microsoft-issued)"""
    url = f"https://www.credly.com/api/v1/users/{user_id}/external_badges/open_badges/public?page=1&page_size=48"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        unique_badge_names = set()
        for badge in data.get('data', []):
            external_badge = badge.get('external_badge', {})
            badge_name = external_badge.get('badge_name', '').strip()
            issuer_name = external_badge.get('issuer_name', '')
            expires_at_date = badge.get('expires_at_date')

            if issuer_name == 'Microsoft' and badge_name in ALLOWED_MICROSOFT_BADGES:
                if not is_badge_expired(expires_at_date):
                    unique_badge_names.add(badge_name)

        return unique_badge_names
    except Exception as e:
        print(f"    ⚠️  Warning: Failed to fetch external badges for user {user_id}: {e}")
        return set()


def fetch_all_community_badges(user_id):
    """Fetch all community badges (org + external), deduplicated by name"""
    org_badges = fetch_community_org_badges(user_id)
    external_badges = fetch_community_external_badges(user_id)
    all_badges = org_badges | external_badges
    return len(all_badges)


def fetch_badges_and_company(user_id, profile_url):
    """Fetch community badge count and company in one go"""
    badge_count = fetch_all_community_badges(user_id)
    company = fetch_user_company(profile_url)
    return badge_count, company


def fetch_page(country, page):
    """Fetch a single page for a country directory"""
    url = f"https://www.credly.com/api/v1/directory?organization_id={GITHUB_ORG_ID}&sort=alphabetical&filter%5Blocation_name%5D={country.replace(' ', '%20')}&page={page}&format=json"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        metadata = data.get('metadata', {})
        total_pages = metadata.get('total_pages', 0)
        users = data.get('data', [])

        return (page, users, total_pages)
    except Exception as e:
        print(f"  ❌ Error on page {page}: {e}")
        return (page, [], 0)


def fetch_brazil_users():
    """Fetch all GitHub certified users from Brazil directory using parallel requests"""
    print("📂 Fetching Brazil directory from Credly (parallel)...")

    # First, get total pages
    _, first_users, total_pages = fetch_page("Brazil", 1)

    if total_pages == 0:
        print("❌ No data found for Brazil")
        return []

    print(f"  Total pages: {total_pages}")

    all_users = []

    # Fetch all pages in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(fetch_page, "Brazil", page): page
            for page in range(1, total_pages + 1)
        }

        completed = 0
        for future in as_completed(futures):
            page, users, _ = future.result()
            all_users.extend(users)
            completed += 1

            if completed % 50 == 0:
                print(f"  Progress: {completed}/{total_pages} pages ({len(all_users)} users)")

    print(f"✅ Found {len(all_users)} users in directory")
    return all_users


def fetch_user_company(profile_url):
    """Fetch company name from user profile"""
    if not profile_url:
        return ''
    try:
        username = profile_url.split('/')[2] if '/users/' in profile_url else ''
        if not username:
            return ''
        url = f"https://www.credly.com/users/{username}"
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        company = data.get('data', {}).get('current_organization_name', '')
        if company:
            company = company.replace('|', '/')
        return company if company else ''
    except Exception:
        return ''


def generate_ranking(users):
    """Generate TOP10_BRAZIL_COMMUNITY.md"""
    # Sort by badges (descending) then by name (alphabetically)
    sorted_users = sorted(users, key=lambda x: (-x['badges'], x['name'].lower()))

    # Group users into positions (tied users share a position)
    positions = []
    current_pos = 0
    prev_badges = None

    for user in sorted_users:
        if user['badges'] != prev_badges:
            current_pos += 1
            prev_badges = user['badges']
            if current_pos > 10:
                break
            positions.append((current_pos, [user]))
        else:
            if current_pos <= 10:
                positions[-1][1].append(user)

    MAX_USERS_PER_POSITION = 20

    # Collect ranked users for display
    all_ranked_users = []
    for pos, pos_users in positions:
        all_ranked_users.extend(pos_users[:MAX_USERS_PER_POSITION])

    # Generate markdown
    content = f"""# 🇧🇷 TOP 10 GitHub Certifications - Brazil (Community Only)

> Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}
>
> This ranking includes only community certifications (excludes partner-exclusive badges).
>
> **Included certifications:** GitHub Foundations, GitHub Actions, GitHub Copilot, GitHub Administration,
> GitHub Advanced Security, Microsoft Certified: DevOps Engineer Expert, and Microsoft Applied Skills.

## 🏆 Top 10 GitHub Certifications Leaders

| Rank | Name | Badges | Company |
|------|------|--------|---------|
"""

    for pos, pos_users in positions:
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
        rank_display = f"{medal} #{pos}" if medal else f"#{pos}"

        display_users = pos_users[:MAX_USERS_PER_POSITION]
        overflow = len(pos_users) - MAX_USERS_PER_POSITION

        names = []
        companies = []
        for user in display_users:
            if user.get('profile_url'):
                profile_url = f"https://www.credly.com{user['profile_url']}"
                names.append(f"[{user['name']}]({profile_url})")
            else:
                names.append(user['name'])
            companies.append(user.get('company', ''))

        if overflow > 0:
            names.append(f"*... and {overflow} more*")
            companies.append('')

        name_cell = '<br>'.join(names)
        badge_cell = str(pos_users[0]['badges'])
        company_cell = '<br>'.join(companies)

        content += f"| {rank_display} | {name_cell} | {badge_cell} | {company_cell} |\n"

    # Company Rankings (TOP 5) — based on ALL users, not just ranked
    company_stats = defaultdict(lambda: {'badges': 0, 'users': 0})
    for user in sorted_users:
        company = user.get('company', '')
        if company:
            company_stats[company]['badges'] += user['badges']
            company_stats[company]['users'] += 1

    if company_stats:
        sorted_companies = sorted(company_stats.items(), key=lambda x: (-x[1]['badges'], -x[1]['users'], x[0].lower()))

        company_positions = []
        prev_badges = None
        current_pos = 0
        for company_name, stats in sorted_companies:
            if stats['badges'] != prev_badges:
                current_pos += 1
                prev_badges = stats['badges']
                if current_pos > 5:
                    break
                company_positions.append((current_pos, [(company_name, stats)]))
            else:
                if current_pos <= 5:
                    company_positions[-1][1].append((company_name, stats))

        if company_positions:
            content += f"""
---

## 🏢 Top 5 Companies

| Rank | Company | Total Badges | Certified Users |
|------|---------|--------------|-----------------|
"""
            for pos, companies in company_positions:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
                rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
                company_names = '<br>'.join(c[0] for c in companies)
                badges_cell = str(companies[0][1]['badges'])
                users_cell = '<br>'.join(str(c[1]['users']) for c in companies)
                content += f"| {rank_display} | {company_names} | {badges_cell} | {users_cell} |\n"

    # Statistics
    if users:
        filtered = [u for u in users if u['badges'] > 0]
        total_users = len(filtered)
        total_badges = sum(u['badges'] for u in filtered)
        avg_badges = total_badges / total_users if total_users > 0 else 0

        content += f"""
---

## 📊 Statistics

- **Total Certified Users**: {total_users:,}
- **Total Badges Earned**: {total_badges:,}
- **Average Badges per User**: {avg_badges:.2f}
- **Highest Badge Count**: {all_ranked_users[0]['badges'] if all_ranked_users else 0}

---
"""

    content += "\n*Data sourced from GitHub Certifications via Credly API (community certifications only)*\n"

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TOP10_BRAZIL_COMMUNITY.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Generated: TOP10_BRAZIL_COMMUNITY.md")


def main():
    print("=" * 80)
    print("GitHub Certifications - Brazil Community Ranking")
    print("(Excludes partner-exclusive certifications)")
    print("=" * 80)
    print()

    # Fetch Brazil users from directory
    directory_users = fetch_brazil_users()
    if not directory_users:
        print("❌ No users found!")
        return

    # Fetch community badge counts for ALL users (not just top N by directory count,
    # since directory badge_count includes partner badges which we exclude here)
    print(f"\n📂 Fetching community badge counts for all {len(directory_users)} users...")

    # Fetch community-only badge counts and company in parallel
    users = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_user = {
            executor.submit(fetch_badges_and_company, user.get('id'), user.get('url', '')): user
            for user in directory_users if user.get('id')
        }

        completed = 0
        for future in as_completed(future_to_user):
            user_data = future_to_user[future]
            try:
                badge_count, company = future.result()
                completed += 1

                first_name = (user_data.get('first_name') or '').strip()
                middle_name = (user_data.get('middle_name') or '').strip()
                last_name = (user_data.get('last_name') or '').strip()

                name_parts = [first_name]
                if middle_name:
                    name_parts.append(middle_name)
                if last_name:
                    name_parts.append(last_name)

                users.append({
                    'name': ' '.join(name_parts),
                    'badges': badge_count,
                    'country': 'Brazil',
                    'profile_url': user_data.get('url', ''),
                    'company': company,
                })

                if completed % 100 == 0:
                    print(f"  Processed {completed}/{len(future_to_user)} users...")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

    # Filter out users with 0 community badges
    users = [u for u in users if u['badges'] > 0]
    print(f"✅ Found {len(users)} users with community certifications")

    print("\n📝 Generating community ranking...")
    generate_ranking(users)

    print()
    print("=" * 80)
    print("✨ Community ranking generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
