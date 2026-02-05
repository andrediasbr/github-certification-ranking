#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Certifications Rankings Generator
Generates TOP 10 rankings for Brazil, Americas, Europe, Asia, Oceania, and World
Supports both Credly and MS Learn certification sources
"""

import csv
import glob
import json
import os
import requests
from collections import defaultdict
from datetime import datetime

# Import MS Learn badge fetching functionality
try:
    from fetch_mslearn_badges import fetch_mslearn_github_badges, extract_share_id
    MSLEARN_AVAILABLE = True
except ImportError:
    MSLEARN_AVAILABLE = False
    print("⚠️  MS Learn badge fetching not available (fetch_mslearn_badges.py not found)")


def is_badge_expired(expires_at_date):
    """Check if a badge is expired based on expires_at_date"""
    if not expires_at_date:  # null = never expires
        return False
    
    try:
        expiration_date = datetime.strptime(expires_at_date, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        return expiration_date < current_date
    except Exception:
        return False


def fetch_credly_badges(profile_url):
    """Fetch all non-expired GitHub and DevOps badge names from Credly for a user.
    Returns a tuple of (github_badges, devops_badges) as sets."""
    github_badges = set()
    devops_badges = set()
    
    # DevOps badge patterns (from Microsoft org in Credly)
    devops_patterns = ['az-400', 'devops engineer expert']
    
    if not profile_url:
        return github_badges, devops_badges
    
    try:
        # Extract username from profile_url (/users/username/badges)
        parts = profile_url.split('/')
        username = parts[2] if len(parts) > 2 and parts[1] == 'users' else None
        if not username:
            return github_badges, devops_badges
        
        page = 1
        while True:
            url = f"https://www.credly.com/users/{username}/badges.json?page={page}&per_page=100"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                break
            
            data = response.json()
            badge_list = data.get('data', [])
            if not badge_list:
                break
            
            for badge in badge_list:
                issuer = badge.get('issuer', {})
                entities = issuer.get('entities', [])
                badge_template = badge.get('badge_template', {})
                badge_name = badge_template.get('name', '')
                expires_at_date = badge.get('expires_at_date')
                
                # Skip expired badges
                if is_badge_expired(expires_at_date):
                    continue
                
                # Check if badge is from GitHub organization
                is_github_org = any(
                    entity.get('entity', {}).get('id') == '63074953-290b-4dce-86ce-ea04b4187219'
                    for entity in entities
                )
                
                if is_github_org and badge_name:
                    github_badges.add(badge_name)
                    continue
                
                # Check if badge is from Microsoft organization (for DevOps badges)
                is_microsoft_org = any(
                    entity.get('entity', {}).get('name', '').lower() == 'microsoft'
                    for entity in entities
                )
                
                if is_microsoft_org and badge_name:
                    badge_name_lower = badge_name.lower()
                    # Check if it's a DevOps badge
                    for pattern in devops_patterns:
                        if pattern in badge_name_lower:
                            devops_badges.add(badge_name)
                            break
            
            page += 1
            if page > 10:  # Safety limit
                break
        
    except Exception as e:
        pass  # Return whatever we got
    
    return github_badges, devops_badges


def get_merged_badge_count(profile_url, mslearn_url):
    """Get total badge count by merging Credly and MS Learn badges with deduplication.
    
    Returns: (total_count, credly_github_badges, credly_devops_badges, mslearn_certs, mslearn_skills, mslearn_devops_exams, mslearn_devops_certs, is_mvp)
    """
    # Get Credly badges (non-expired)
    credly_github_badges, credly_devops_badges = fetch_credly_badges(profile_url)
    
    # Get MS Learn badges
    mslearn_certs = []
    mslearn_skills = []
    mslearn_devops_exams = []
    mslearn_devops_certs = []
    is_mvp = False
    
    if mslearn_url and MSLEARN_AVAILABLE:
        mslearn_result = fetch_mslearn_github_badges(mslearn_url)
        mslearn_certs = mslearn_result.get('certifications', [])
        mslearn_skills = mslearn_result.get('applied_skills', [])
        mslearn_devops_exams = mslearn_result.get('devops_exams', [])
        mslearn_devops_certs = mslearn_result.get('devops_certs', [])
        is_mvp = mslearn_result.get('is_mvp', False)
    
    # Create unified sets for deduplication
    # GitHub badges: combine Credly GitHub badges with MS Learn GitHub certifications
    all_github_badges = set(credly_github_badges)
    for cert in mslearn_certs:
        all_github_badges.add(cert)
    
    # DevOps badges: combine Credly DevOps badges with MS Learn DevOps exams/certs
    # Normalize names for deduplication:
    # - Credly: "AZ-400: Designing and Implementing Microsoft DevOps Solutions"
    # - MS Learn exam: "Designing and Implementing Microsoft DevOps Solutions"
    # - Credly cert: "Microsoft Certified: DevOps Engineer Expert"
    # - MS Learn cert: "DevOps Engineer Expert"
    all_devops_badges = set()
    
    # Add Credly DevOps badges (they have full names)
    for badge in credly_devops_badges:
        all_devops_badges.add(badge.lower())  # Normalize to lowercase for comparison
    
    # Add MS Learn DevOps exams if not already present (check for partial match)
    for exam in mslearn_devops_exams:
        exam_lower = exam.lower()
        # Check if this exam is already in Credly (may have "AZ-400:" prefix in Credly)
        already_present = any(exam_lower in credly_badge.lower() for credly_badge in credly_devops_badges)
        if not already_present:
            all_devops_badges.add(exam_lower)
    
    # Add MS Learn DevOps certs if not already present
    for cert in mslearn_devops_certs:
        cert_lower = cert.lower()
        # Check if this cert is already in Credly
        already_present = any(cert_lower in credly_badge.lower() for credly_badge in credly_devops_badges)
        if not already_present:
            all_devops_badges.add(cert_lower)
    
    # Applied skills are always additional (not duplicates of Credly badges)
    all_applied_skills = set()
    for skill in mslearn_skills:
        all_applied_skills.add(skill)
    
    total_count = len(all_github_badges) + len(all_devops_badges) + len(all_applied_skills)
    
    return total_count, credly_github_badges, credly_devops_badges, mslearn_certs, mslearn_skills, mslearn_devops_exams, mslearn_devops_certs, is_mvp


# Continent mapping
CONTINENT_MAP = {
    # AMERICAS
    'antigua and barbuda': 'Americas', 'argentina': 'Americas', 'bahamas': 'Americas',
    'barbados': 'Americas', 'belize': 'Americas', 'bolivia': 'Americas',
    'brazil': 'Americas', 'canada': 'Americas', 'chile': 'Americas',
    'colombia': 'Americas', 'costa rica': 'Americas', 'cuba': 'Americas',
    'dominica': 'Americas', 'dominican republic': 'Americas', 'ecuador': 'Americas',
    'el salvador': 'Americas', 'grenada': 'Americas', 'guatemala': 'Americas',
    'haiti': 'Americas', 'honduras': 'Americas', 'jamaica': 'Americas',
    'mexico': 'Americas', 'nicaragua': 'Americas', 'panama': 'Americas',
    'paraguay': 'Americas', 'peru': 'Americas', 'saint kitts and nevis': 'Americas',
    'saint lucia': 'Americas', 'saint vincent and the grenadines': 'Americas',
    'suriname': 'Americas', 'trinidad and tobago': 'Americas', 'united states': 'Americas',
    'uruguay': 'Americas', 'venezuela': 'Americas', 'guyana': 'Americas',
    
    # EUROPE
    'albania': 'Europe', 'andorra': 'Europe', 'armenia': 'Europe',
    'austria': 'Europe', 'azerbaijan': 'Europe', 'belarus': 'Europe',
    'belgium': 'Europe', 'bosnia and herzegovina': 'Europe', 'bulgaria': 'Europe',
    'croatia': 'Europe', 'cyprus': 'Europe', 'czech republic': 'Europe',
    'denmark': 'Europe', 'estonia': 'Europe', 'finland': 'Europe',
    'france': 'Europe', 'georgia': 'Europe', 'germany': 'Europe',
    'greece': 'Europe', 'hungary': 'Europe', 'iceland': 'Europe',
    'ireland': 'Europe', 'italy': 'Europe', 'kosovo': 'Europe',
    'latvia': 'Europe', 'liechtenstein': 'Europe', 'lithuania': 'Europe',
    'luxembourg': 'Europe', 'malta': 'Europe', 'moldova': 'Europe',
    'monaco': 'Europe', 'montenegro': 'Europe', 'netherlands': 'Europe',
    'north macedonia': 'Europe', 'norway': 'Europe', 'poland': 'Europe',
    'portugal': 'Europe', 'romania': 'Europe', 'russia': 'Europe',
    'san marino': 'Europe', 'serbia': 'Europe', 'slovakia': 'Europe',
    'slovenia': 'Europe', 'spain': 'Europe', 'sweden': 'Europe',
    'switzerland': 'Europe', 'ukraine': 'Europe', 'united kingdom': 'Europe',
    'vatican city': 'Europe',
    
    # ASIA
    'afghanistan': 'Asia', 'bahrain': 'Asia', 'bangladesh': 'Asia',
    'bhutan': 'Asia', 'brunei': 'Asia', 'cambodia': 'Asia',
    'china': 'Asia', 'east timor': 'Asia', 'indonesia': 'Asia',
    'iran': 'Asia', 'iraq': 'Asia', 'israel': 'Asia',
    'japan': 'Asia', 'jordan': 'Asia', 'kazakhstan': 'Asia',
    'kuwait': 'Asia', 'kyrgyzstan': 'Asia', 'laos': 'Asia',
    'lebanon': 'Asia', 'malaysia': 'Asia', 'maldives': 'Asia',
    'mongolia': 'Asia', 'myanmar': 'Asia', 'nepal': 'Asia',
    'north korea': 'Asia', 'oman': 'Asia', 'pakistan': 'Asia',
    'palestine': 'Asia', 'philippines': 'Asia', 'qatar': 'Asia',
    'saudi arabia': 'Asia', 'singapore': 'Asia', 'south korea': 'Asia',
    'sri lanka': 'Asia', 'syria': 'Asia', 'taiwan': 'Asia',
    'tajikistan': 'Asia', 'thailand': 'Asia', 'turkey': 'Asia',
    'turkmenistan': 'Asia', 'united arab emirates': 'Asia', 'uzbekistan': 'Asia',
    'vietnam': 'Asia', 'yemen': 'Asia', 'timor leste': 'Asia', 'india': 'Asia',
    
    # AFRICA
    'algeria': 'Africa', 'angola': 'Africa', 'benin': 'Africa',
    'botswana': 'Africa', 'burkina faso': 'Africa', 'burundi': 'Africa',
    'cameroon': 'Africa', 'cape verde': 'Africa', 'central african republic': 'Africa',
    'chad': 'Africa', 'comoros': 'Africa', 'democratic republic of the congo': 'Africa',
    'djibouti': 'Africa', 'egypt': 'Africa', 'equatorial guinea': 'Africa',
    'eritrea': 'Africa', 'eswatini': 'Africa', 'ethiopia': 'Africa',
    'gabon': 'Africa', 'gambia': 'Africa', 'ghana': 'Africa',
    'guinea': 'Africa', 'guinea-bissau': 'Africa',
    'ivory coast': 'Africa', 'kenya': 'Africa', 'lesotho': 'Africa', 'liberia': 'Africa',
    'libya': 'Africa', 'madagascar': 'Africa', 'malawi': 'Africa',
    'mali': 'Africa', 'mauritania': 'Africa', 'mauritius': 'Africa',
    'morocco': 'Africa', 'mozambique': 'Africa', 'namibia': 'Africa',
    'niger': 'Africa', 'nigeria': 'Africa', 'republic of the congo': 'Africa',
    'rwanda': 'Africa', 'sao tome and principe': 'Africa', 'senegal': 'Africa',
    'seychelles': 'Africa', 'sierra leone': 'Africa', 'somalia': 'Africa',
    'south africa': 'Africa', 'south sudan': 'Africa', 'sudan': 'Africa',
    'tanzania': 'Africa', 'togo': 'Africa', 'tunisia': 'Africa',
    'uganda': 'Africa', 'zambia': 'Africa', 'zimbabwe': 'Africa',
    
    # OCEANIA
    'australia': 'Oceania', 'fiji': 'Oceania', 'kiribati': 'Oceania',
    'marshall islands': 'Oceania', 'micronesia': 'Oceania', 'nauru': 'Oceania',
    'new zealand': 'Oceania', 'palau': 'Oceania', 'papua new guinea': 'Oceania',
    'samoa': 'Oceania', 'solomon islands': 'Oceania', 'tonga': 'Oceania',
    'tuvalu': 'Oceania', 'vanuatu': 'Oceania',
}

def get_continent(country_name):
    """Get continent from country name"""
    country_lower = country_name.lower().replace('-', ' ')
    return CONTINENT_MAP.get(country_lower, 'Unknown')

def fetch_user_company(profile_url):
    """Fetch company name from user profile"""
    if not profile_url:
        return ''
    
    try:
        # Extract username from profile_url (/users/username/badges)
        username = profile_url.split('/')[2] if '/users/' in profile_url else ''
        if not username:
            return ''
        
        # Fetch user profile with JSON header
        url = f"https://www.credly.com/users/{username}"
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Extract company name
        company = data.get('data', {}).get('current_organization_name', '')
        return company if company else ''
    except:
        return ''

def load_metadata():
    """Load CSV metadata"""
    metadata_file = 'csv_metadata.json'
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}

def read_all_csv_files(base_path):
    """Read all CSV files and return users list"""
    users = []
    csv_files = glob.glob(os.path.join(base_path, 'datasource', 'github-certs-*.csv'))
    metadata = load_metadata()
    
    print(f"📂 Processing {len(csv_files)} CSV files...")
    
    for csv_file in csv_files:
        country = os.path.basename(csv_file).replace('github-certs-', '').replace('.csv', '')
        country_display = country.replace('-', ' ').title()
        continent = get_continent(country)
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        badge_count = int(row.get('badge_count', 0))
                        if badge_count > 0:
                            first_name = row.get('first_name', '').strip('"').strip()
                            middle_name = row.get('middle_name', '').strip('"').strip()
                            last_name = row.get('last_name', '').strip('"').strip()
                            profile_url = row.get('profile_url', '').strip('"').strip()
                            mslearn_url = row.get('mslearn_url', '').strip('"').strip() if row.get('mslearn_url') else ''
                            is_mvp = row.get('is_mvp', '').lower() == 'true'
                            
                            # Build full name
                            name_parts = [first_name]
                            if middle_name:
                                name_parts.append(middle_name)
                            if last_name:
                                name_parts.append(last_name)
                            full_name = ' '.join(name_parts)
                            
                            users.append({
                                'name': full_name,
                                'badges': badge_count,
                                'country': country_display,
                                'continent': continent,
                                'profile_url': profile_url,
                                'mslearn_url': mslearn_url,
                                'is_mvp': is_mvp
                            })
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"⚠️  Error processing {csv_file}: {e}")
            continue
    
    print(f"✅ Loaded {len(users)} users from all files")
    return users


def update_csv_badge_counts(base_path):
    """Update badge counts and MVP status in CSV files for users with MS Learn URLs.
    
    This merges Credly + MS Learn badges and writes the merged count + is_mvp back to CSV.
    """
    csv_files = glob.glob(os.path.join(base_path, 'datasource', 'github-certs-*.csv'))
    updated_count = 0
    
    print(f"📊 Updating badge counts for users with MS Learn URLs...")
    
    for csv_file in csv_files:
        rows = []
        has_updates = False
        
        try:
            # Read all rows
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames)
                
                # Ensure is_mvp column exists
                if 'is_mvp' not in fieldnames:
                    fieldnames.append('is_mvp')
                
                for row in reader:
                    mslearn_url = row.get('mslearn_url', '').strip()
                    profile_url = row.get('profile_url', '').strip()
                    
                    if mslearn_url:
                        # Get merged badge count and MVP status
                        merged_count, _, _, _, _, _, _, is_mvp = get_merged_badge_count(profile_url, mslearn_url)
                        old_count = int(row.get('badge_count', 0))
                        old_mvp = row.get('is_mvp', '').lower() == 'true'
                        
                        if merged_count != old_count or is_mvp != old_mvp:
                            row['badge_count'] = str(merged_count)
                            row['is_mvp'] = str(is_mvp)
                            has_updates = True
                            updated_count += 1
                            country = os.path.basename(csv_file).replace('github-certs-', '').replace('.csv', '')
                            mvp_str = " (MVP)" if is_mvp else ""
                            print(f"    {row.get('first_name', '')} {row.get('last_name', '')} ({country}): {old_count} → {merged_count}{mvp_str}")
                    else:
                        # Ensure is_mvp column has a value even for non-mslearn users
                        if 'is_mvp' not in row or not row.get('is_mvp'):
                            row['is_mvp'] = ''
                    
                    rows.append(row)
            
            # Write back if there were updates
            if has_updates:
                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
        
        except Exception as e:
            print(f"⚠️  Error updating {csv_file}: {e}")
            continue
    
    if updated_count > 0:
        print(f"✅ Updated {updated_count} users with merged badge counts")
    else:
        print(f"✅ No badge count updates needed")
def get_outdated_csvs():
    """Get list of CSVs that weren't updated in the last run"""
    metadata = load_metadata()
    current_time = datetime.now()
    outdated = []
    
    for country, info in metadata.items():
        last_updated = datetime.fromisoformat(info['last_updated'])
        hours_old = (current_time - last_updated).total_seconds() / 3600
        
        # Consider outdated if more than 25 hours old (1 day + buffer)
        if hours_old > 25:
            outdated.append({
                'country': country,
                'last_updated': last_updated.strftime('%Y-%m-%d %H:%M UTC'),
                'hours_old': int(hours_old)
            })
    
    return sorted(outdated, key=lambda x: x['hours_old'], reverse=True)

def generate_markdown_top10(users, title, filename, filter_func=None):
    """Generate TOP 10 markdown file"""
    
    # Filter users if filter function provided
    if filter_func:
        filtered_users = [u for u in users if filter_func(u)]
    else:
        filtered_users = users
    
    # Sort by badges (descending) then by name (alphabetically)
    sorted_users = sorted(filtered_users, key=lambda x: (-x['badges'], x['name'].lower()))
    
    # Determine which users to include (top 10, but include ties)
    top_users = []
    current_rank = 0
    prev_badges = None
    rank_count = 0
    
    for user in sorted_users:
        # Increment rank_count for each user processed
        rank_count += 1
        
        # Assign rank: if badges changed, update current_rank to rank_count
        if user['badges'] != prev_badges:
            current_rank = rank_count
            prev_badges = user['badges']
        
        # Include user if:
        # - current_rank <= 10, OR
        # - current_rank > 10 but has same badges as someone at rank 10
        if current_rank <= 10:
            top_users.append((current_rank, user))
        elif top_users and user['badges'] == top_users[-1][1]['badges']:
            # Include tied users even if rank > 10
            top_users.append((current_rank, user))
        else:
            # No more users to include
            break
    
    # Fetch company information for ranked users
    print(f"  Fetching company info for {len(top_users)} ranked users...")
    for rank, user in top_users:
        company = fetch_user_company(user.get('profile_url', ''))
        user['company'] = company
    
    # Note: is_mvp is already loaded from CSV by read_all_csv_files()
    
    # Get outdated CSVs
    outdated = get_outdated_csvs()
    
    # Generate markdown content
    content = f"""# {title}

> Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

## 🏆 Top 10 GitHub Certifications Leaders

| Rank | Name | Badges | Company | Country |
|------|------|--------|---------|---------|
"""
    
    prev_rank = None
    for rank, user in top_users:
        # Show rank number only if it's different from previous
        if rank != prev_rank:
            # Add medal emoji for top 3 ranks (first occurrence only)
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, '')
            rank_display = f"{medal} #{rank}" if medal else f"#{rank}"
        else:
            # For tied users: empty cell
            rank_display = ""
        
        # Add profile link if available
        name_display = user['name']
        if user.get('profile_url'):
            profile_url = f"https://www.credly.com{user['profile_url']}"
            name_display = f"[{user['name']}]({profile_url})"
        
        # Add MVP badge if user is a Microsoft MVP
        if user.get('is_mvp'):
            name_display += ' <img src="images/mvp.svg" alt="Microsoft MVP" width="16" height="16"/>'
        
        # Add MS Learn indicator if user has MS Learn profile
        if user.get('mslearn_url'):
            name_display += " 📚"
        
        company_display = user.get('company', '')
        content += f"| {rank_display} | {name_display} | {user['badges']} | {company_display} | {user['country']} |\n"
        prev_rank = rank
    
    # Add statistics
    if filtered_users:
        total_users = len(filtered_users)
        total_badges = sum(u['badges'] for u in filtered_users)
        avg_badges = total_badges / total_users if total_users > 0 else 0
        
        content += f"""
---

## 📊 Statistics

- **Total Certified Users**: {total_users:,}
- **Total Badges Earned**: {total_badges:,}
- **Average Badges per User**: {avg_badges:.2f}
- **Highest Badge Count**: {top_users[0][1]['badges'] if top_users else 0}

---
"""
    
    # Add outdated data warning if applicable
    if outdated:
        content += """
## ⚠️ Data Freshness Warning

The following countries have data that was not updated in the last run:

| Country | Last Updated | Hours Old |
|---------|--------------|-----------|
"""
        for item in outdated[:10]:  # Show max 10
            content += f"| {item['country']} | {item['last_updated']} | {item['hours_old']}h |\n"
        
        if len(outdated) > 10:
            content += f"\n*... and {len(outdated) - 10} more countries*\n"
        
        content += "\n---\n"
    
    content += """
*Data sourced from GitHub Certifications via Credly API and Microsoft Learn*

> <img src="images/mvp.svg" alt="Microsoft MVP" width="16" height="16"/> = Microsoft MVP
>
> 📚 = User has linked MS Learn transcript (may include additional GitHub certifications: GH-100, GH-200, GH-300, GH-400, GH-500 and Applied Skills)
"""
    
    # Write to file
    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Generated: {filename}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("GitHub Certifications Rankings Generator")
    print("=" * 80)
    print()
    
    # Get base path
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # First, update badge counts in CSV files for users with MS Learn URLs
    update_csv_badge_counts(base_path)
    print()
    
    # Read all CSV files (now with updated badge counts)
    users = read_all_csv_files(base_path)
    
    if not users:
        print("❌ No users found in CSV files!")
        return
    
    print()
    print("📝 Generating markdown files...")
    print()
    
    # Generate TOP 10 Brazil
    generate_markdown_top10(
        users,
        "🇧🇷 TOP 10 GitHub Certifications - Brazil",
        "TOP10_BRAZIL.md",
        lambda u: u['country'].lower() == 'brazil'
    )
    
    # Generate TOP 10 Americas
    generate_markdown_top10(
        users,
        "🌎 TOP 10 GitHub Certifications - Americas",
        "TOP10_AMERICAS.md",
        lambda u: u['continent'] == 'Americas'
    )
    
    # Generate TOP 10 Europe
    generate_markdown_top10(
        users,
        "🇪🇺 TOP 10 GitHub Certifications - Europe",
        "TOP10_EUROPE.md",
        lambda u: u['continent'] == 'Europe'
    )
    
    # Generate TOP 10 Asia
    generate_markdown_top10(
        users,
        "🌏 TOP 10 GitHub Certifications - Asia",
        "TOP10_ASIA.md",
        lambda u: u['continent'] == 'Asia'
    )
    
    # Generate TOP 10 Africa
    generate_markdown_top10(
        users,
        "🌍 TOP 10 GitHub Certifications - Africa",
        "TOP10_AFRICA.md",
        lambda u: u['continent'] == 'Africa'
    )
    
    # Generate TOP 10 Oceania
    generate_markdown_top10(
        users,
        "🌊 TOP 10 GitHub Certifications - Oceania",
        "TOP10_OCEANIA.md",
        lambda u: u['continent'] == 'Oceania'
    )
    
    # Generate TOP 10 Global
    generate_markdown_top10(
        users,
        "🌍 TOP 10 GitHub Certifications - Global",
        "TOP10_WORLD.md",
        None  # No filter, all users
    )
    
    print()
    print("=" * 80)
    print("✨ All rankings generated successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
