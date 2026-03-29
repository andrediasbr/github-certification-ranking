#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Certifications Rankings Generator
Generates TOP 10 rankings for Brazil, Americas, Europe, Asia, Oceania, and World
"""

import csv
import glob
import json
import os
import requests
from collections import defaultdict
from datetime import datetime

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
        
        # Extract company name and sanitize pipe characters (breaks markdown tables)
        company = data.get('data', {}).get('current_organization_name', '')
        if company:
            company = company.replace('|', '/')
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
                                'profile_url': profile_url
                            })
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"⚠️  Error processing {csv_file}: {e}")
            continue
    
    print(f"✅ Loaded {len(users)} users from all files")
    return users

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
    """Generate TOP 10 markdown file with position-based ranking (tied users on same row)"""
    
    # Filter users if filter function provided
    if filter_func:
        filtered_users = [u for u in users if filter_func(u)]
    else:
        filtered_users = users
    
    # Sort by badges (descending) then by name (alphabetically)
    sorted_users = sorted(filtered_users, key=lambda x: (-x['badges'], x['name'].lower()))
    
    # Group users into positions (tied users share a position)
    positions = []  # list of (position_number, [users])
    current_pos = 0
    prev_badges = None
    
    for i, user in enumerate(sorted_users):
        if user['badges'] != prev_badges:
            current_pos += 1
            prev_badges = user['badges']
            if current_pos > 10:
                break
            positions.append((current_pos, [user]))
        else:
            if current_pos <= 10:
                positions[-1][1].append(user)
    
    # Cap display: if a position has too many tied users, show first N and a count
    MAX_USERS_PER_POSITION = 20
    
    # Collect all users across positions for company fetching (capped)
    all_ranked_users = []
    for pos, pos_users in positions:
        all_ranked_users.extend(pos_users[:MAX_USERS_PER_POSITION])
    
    # Fetch company information for ranked users
    print(f"  Fetching company info for {len(all_ranked_users)} ranked users...")
    for user in all_ranked_users:
        company = fetch_user_company(user.get('profile_url', ''))
        user['company'] = company
    
    # Get outdated CSVs
    outdated = get_outdated_csvs()
    
    # Generate markdown content
    content = f"""# {title}

> Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

## 🏆 Top 10 GitHub Certifications Leaders

| Rank | Name | Badges | Company | Country |
|------|------|--------|---------|---------|
"""
    
    for pos, pos_users in positions:
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
        rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
        
        # Cap display for positions with many tied users
        display_users = pos_users[:MAX_USERS_PER_POSITION]
        overflow = len(pos_users) - MAX_USERS_PER_POSITION
        
        # Build cell content for each column, joining tied users with <br>
        names = []
        companies = []
        countries = []
        for user in display_users:
            if user.get('profile_url'):
                profile_url = f"https://www.credly.com{user['profile_url']}"
                names.append(f"[{user['name']}]({profile_url})")
            else:
                names.append(user['name'])
            companies.append(user.get('company', ''))
            countries.append(user['country'])
        
        if overflow > 0:
            names.append(f"*... and {overflow} more*")
            companies.append('')
            countries.append('')
        
        name_cell = '<br>'.join(names)
        badge_cell = str(pos_users[0]['badges'])
        company_cell = '<br>'.join(companies)
        country_cell = '<br>'.join(countries)
        
        content += f"| {rank_display} | {name_cell} | {badge_cell} | {company_cell} | {country_cell} |\n"
    
    # --- Company Rankings (TOP 5) --- based on ranked users' companies
    company_stats = defaultdict(lambda: {'badges': 0, 'users': 0})
    for user in all_ranked_users:
        company = user.get('company', '')
        if company:
            company_stats[company]['badges'] += user['badges']
            company_stats[company]['users'] += 1
    
    if company_stats:
        sorted_companies = sorted(company_stats.items(), key=lambda x: (-x[1]['badges'], -x[1]['users'], x[0].lower()))
        
        # Build TOP 5 positions (with ties)
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
    
    # --- Country Rankings (TOP 5) --- only for multi-country rankings
    unique_countries = set(u['country'] for u in filtered_users)
    if len(unique_countries) > 1:
        country_stats = defaultdict(lambda: {'badges': 0, 'users': 0})
        for user in filtered_users:
            country_stats[user['country']]['badges'] += user['badges']
            country_stats[user['country']]['users'] += 1
        
        sorted_countries = sorted(country_stats.items(), key=lambda x: (-x[1]['badges'], -x[1]['users'], x[0].lower()))
        
        # Build TOP 5 positions (with ties)
        country_positions = []
        prev_badges = None
        current_pos = 0
        for country_name, stats in sorted_countries:
            if stats['badges'] != prev_badges:
                current_pos += 1
                prev_badges = stats['badges']
                if current_pos > 5:
                    break
                country_positions.append((current_pos, [(country_name, stats)]))
            else:
                if current_pos <= 5:
                    country_positions[-1][1].append((country_name, stats))
        
        if country_positions:
            content += f"""
---

## 🌐 Top 5 Countries

| Rank | Country | Total Badges | Certified Users |
|------|---------|--------------|-----------------|
"""
            for pos, countries_list in country_positions:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
                rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
                
                country_names = '<br>'.join(c[0] for c in countries_list)
                badges_cell = str(countries_list[0][1]['badges'])
                users_cell = '<br>'.join(str(c[1]['users']) for c in countries_list)
                
                content += f"| {rank_display} | {country_names} | {badges_cell} | {users_cell} |\n"
    
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
- **Highest Badge Count**: {all_ranked_users[0]['badges'] if all_ranked_users else 0}

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
    
    content += "\n*Data sourced from GitHub Certifications via Credly API*\n"
    
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
    
    # Read all CSV files
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
        "🗽 TOP 10 GitHub Certifications - Americas",
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
        "� TOP 10 GitHub Certifications - Asia",
        "TOP10_ASIA.md",
        lambda u: u['continent'] == 'Asia'
    )
    
    # Generate TOP 10 Africa
    generate_markdown_top10(
        users,
        "🦁 TOP 10 GitHub Certifications - Africa",
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
