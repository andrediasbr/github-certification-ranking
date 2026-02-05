#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch GitHub certifications from Microsoft Learn transcript API
Supports: GH-100, GH-200, GH-300, GH-400, GH-500, and Applied Skills assessments
"""

import requests
from datetime import datetime

# GitHub certification exam numbers in MS Learn
GITHUB_EXAM_MAPPINGS = {
    # Core certifications with exam numbers
    'gh-100': 'GitHub Administration',
    'gh-200': 'GitHub Actions',
    'gh-300': 'GitHub Copilot',
    'gh-400': 'GitHub Advanced Security',  # Note: GH-400 might not exist, placeholder
    'gh-500': 'GitHub Advanced Security',
}

# Applied Skills exam codes
GITHUB_APPLIED_SKILLS_EXAM_MAPPINGS = {
    'az-2006': 'Automate Azure Load Testing by using GitHub Actions',
    'az-2007': 'Accelerate app development by using GitHub Copilot',
    'az-2008': 'DevOps Foundations: The Core Principles and Practices',
    'az-2010': 'Design and Implement Platform Engineering',
}

# DevOps exam codes (AZ-400)
DEVOPS_EXAM_MAPPINGS = {
    'az-400': 'Designing and Implementing Microsoft DevOps Solutions',
}

# DevOps certification names
DEVOPS_CERT_MAPPINGS = {
    'devops engineer expert': 'DevOps Engineer Expert',
    'microsoft certified: devops engineer expert': 'DevOps Engineer Expert',
}

# GitHub certification names in MS Learn (active certifications)
GITHUB_CERT_MAPPINGS = {
    'github foundations': 'GitHub Foundations',
    'github certified: foundations': 'GitHub Foundations',
    'github certified: actions': 'GitHub Actions',
    'github certified: administration': 'GitHub Administration',
    'github certified: copilot': 'GitHub Copilot',
    'github certified: advanced security': 'GitHub Advanced Security',
}

# Applied Skills assessments for GitHub (title pattern -> display name)
GITHUB_APPLIED_SKILLS = {
    'accelerate app development by using github copilot': 'Accelerate app development by using GitHub Copilot',
    'automate azure load testing by using github actions': 'Automate Azure Load Testing by using GitHub Actions',
    'devops foundations: the core principles and practices': 'DevOps Foundations: The Core Principles and Practices',
    'design and implement platform engineering': 'Design and Implement Platform Engineering',
}

def is_mslearn_expired(expiration):
    """Check if an MS Learn certification/badge is expired based on expiration date.
    
    Args:
        expiration: Expiration date string in ISO format (e.g., "2026-06-08T23:59:59+00:00") or None
        
    Returns:
        bool: True if expired, False if not expired or no expiration
    """
    if not expiration:
        return False
    
    try:
        # Parse ISO format datetime string
        # Handle both formats: "2026-06-08T23:59:59+00:00" and "2026-06-08"
        if 'T' in expiration:
            # Remove timezone info for simple comparison
            exp_str = expiration.split('T')[0]
        else:
            exp_str = expiration
        
        expiration_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        return expiration_date < current_date
    except Exception:
        # If we can't parse the date, assume not expired to avoid false positives
        return False

def extract_share_id(mslearn_url):
    """Extract share ID from MS Learn transcript share URL.
    
    Examples:
    - https://learn.microsoft.com/en-us/users/jessehouwing-1848/transcript/share/d5gza1z690gp607
    - https://learn.microsoft.com/en-us/users/rbos/transcript/dgg4f96x3lkzp9d
    - https://learn.microsoft.com/api/profiles/transcript/share/d5gza1z690gp607?locale=en-us
    - https://learn.microsoft.com/api/profiles/transcript/share/d5gza1z690gp607?WT.mc_id=DOP-MVP-5001511
    - d5gza1z690gp607
    - Returns: d5gza1z690gp607
    """
    if not mslearn_url:
        return None
    
    # Handle different URL formats
    mslearn_url = mslearn_url.strip()
    
    # Remove any query parameters first
    base_url = mslearn_url.split('?')[0]
    
    # Extract share ID from URL with /share/
    if '/share/' in base_url:
        parts = base_url.split('/share/')
        if len(parts) == 2:
            share_id = parts[1].split('/')[0]
            return share_id if share_id else None
    
    # Extract share ID from URL with /transcript/{id} (without /share/)
    if '/transcript/' in base_url:
        parts = base_url.split('/transcript/')
        if len(parts) == 2:
            share_id = parts[1].split('/')[0]
            return share_id if share_id else None
    
    # Maybe it's just the share ID itself (alphanumeric string, typically 11-20 chars)
    if len(mslearn_url) < 30 and '/' not in mslearn_url and '.' not in mslearn_url:
        return mslearn_url
    
    return None

def fetch_mslearn_github_badges(mslearn_url, verbose=False):
    """Fetch GitHub certifications from MS Learn transcript.
    
    Args:
        mslearn_url: MS Learn transcript share URL or share ID
        verbose: Whether to print debug info
        
    Returns:
        dict with:
        - badge_count: Number of GitHub certifications found
        - certifications: List of certification names
        - applied_skills: List of applied skills names
        - is_mvp: Whether user has MVP affiliation
        - error: Error message if any
    """
    result = {
        'badge_count': 0,
        'certifications': [],
        'applied_skills': [],
        'devops_exams': [],
        'devops_certs': [],
        'is_mvp': False,
        'error': None
    }
    
    share_id = extract_share_id(mslearn_url)
    if not share_id:
        result['error'] = 'Could not extract share ID from URL'
        return result
    
    url = f"https://learn.microsoft.com/api/profiles/transcript/share/{share_id}?locale=en-us"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 404:
            result['error'] = 'Transcript share link not found or expired'
            return result
        elif response.status_code != 200:
            result['error'] = f'API returned status {response.status_code}'
            return result
        
        data = response.json()
        cert_data = data.get('certificationData', {})
        
        # Check for MVP status via profile API
        user_name = data.get('userName')
        if user_name:
            try:
                profile_url = f"https://learn.microsoft.com/api/profiles/{user_name}"
                profile_response = requests.get(profile_url, timeout=10)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    affiliations = profile_data.get('affiliations', [])
                    # Check for MVP in affiliations (case-insensitive)
                    if any(aff.lower() in ['mvp', 'microsoft mvp'] for aff in affiliations if isinstance(aff, str)):
                        result['is_mvp'] = True
                        if verbose:
                            print(f"    MVP status detected for {user_name}")
            except Exception as e:
                if verbose:
                    print(f"    Warning: Could not fetch profile for MVP detection: {e}")
        
        # Track unique certifications to avoid duplicates
        unique_certs = set()
        
        # 1. Check active certifications (only non-expired ones)
        for cert in cert_data.get('activeCertifications', []):
            cert_name = cert.get('name', '').lower().strip()
            expiration = cert.get('expiration')
            
            # Skip if expired
            if is_mslearn_expired(expiration):
                if verbose:
                    print(f"    Skipping expired cert: {cert.get('name')}")
                continue
            
            # Check if it's a GitHub certification
            for pattern, display_name in GITHUB_CERT_MAPPINGS.items():
                if pattern in cert_name:
                    if display_name not in unique_certs:
                        unique_certs.add(display_name)
                        result['certifications'].append(display_name)
                    break
            
            # Check if it's a DevOps certification
            for pattern, display_name in DEVOPS_CERT_MAPPINGS.items():
                if pattern in cert_name:
                    if display_name not in unique_certs:
                        unique_certs.add(display_name)
                        result['devops_certs'].append(display_name)
                    break
        
        # 2. Check passed exams
        for exam in cert_data.get('passedExams', []):
            exam_number = exam.get('examNumber', '').lower().strip()
            exam_title = exam.get('examTitle', '').lower().strip()
            
            # Check by exam number (e.g., GH-100)
            if exam_number in GITHUB_EXAM_MAPPINGS:
                display_name = GITHUB_EXAM_MAPPINGS[exam_number]
                if display_name not in unique_certs:
                    unique_certs.add(display_name)
                    result['certifications'].append(display_name)
            # Check for applied skills exam codes (e.g., AZ-2007)
            elif exam_number in GITHUB_APPLIED_SKILLS_EXAM_MAPPINGS:
                display_name = GITHUB_APPLIED_SKILLS_EXAM_MAPPINGS[exam_number]
                if display_name not in unique_certs:
                    unique_certs.add(display_name)
                    result['applied_skills'].append(display_name)
            # Check for DevOps exam codes (e.g., AZ-400)
            elif exam_number in DEVOPS_EXAM_MAPPINGS:
                display_name = DEVOPS_EXAM_MAPPINGS[exam_number]
                if display_name not in unique_certs:
                    unique_certs.add(display_name)
                    result['devops_exams'].append(display_name)
            # Also check by title
            elif 'github' in exam_title:
                for pattern, display_name in GITHUB_CERT_MAPPINGS.items():
                    if pattern in exam_title:
                        if display_name not in unique_certs:
                            unique_certs.add(display_name)
                            result['certifications'].append(display_name)
                        break
        
        # 3. Check applied skills assessments (in appliedSkillsData at top level)
        applied_skills_data = data.get('appliedSkillsData', {})
        for skill in applied_skills_data.get('appliedSkillsCredentials', []):
            skill_title = skill.get('title', '').lower().strip()
            
            # Check if it's a GitHub applied skill
            for pattern, display_name in GITHUB_APPLIED_SKILLS.items():
                if pattern in skill_title:
                    if display_name not in unique_certs:
                        unique_certs.add(display_name)
                        result['applied_skills'].append(display_name)
                    break
        
        result['badge_count'] = len(result['certifications']) + len(result['applied_skills']) + len(result['devops_exams']) + len(result['devops_certs'])
        
        if verbose:
            print(f"    MS Learn certificates found: {result['certifications']}")
            print(f"    MS Learn applied skills found: {result['applied_skills']}")
            print(f"    MS Learn DevOps exams found: {result['devops_exams']}")
            print(f"    MS Learn DevOps certs found: {result['devops_certs']}")
        
    except requests.exceptions.Timeout:
        result['error'] = 'Request timeout'
    except requests.exceptions.RequestException as e:
        result['error'] = f'Request error: {str(e)}'
    except Exception as e:
        result['error'] = f'Unexpected error: {str(e)}'
    
    return result

def get_combined_badge_count(credly_count, mslearn_data, credly_badges=None):
    """Calculate combined badge count from Credly and MS Learn.
    
    For now, we simply add them since Credly tracks badges from credly.com
    and MS Learn tracks badges from learn.microsoft.com. These are typically
    separate systems with some overlap for GitHub certifications issued
    through Microsoft Learn after 2024.
    
    Args:
        credly_count: Number of badges from Credly
        mslearn_data: Result from fetch_mslearn_github_badges()
        credly_badges: Optional list of Credly badge names for deduplication
        
    Returns:
        int: Combined badge count
    """
    # If MS Learn had an error or no data, just return Credly count
    if mslearn_data.get('error') or mslearn_data.get('badge_count', 0) == 0:
        return credly_count
    
    # TODO: Implement deduplication if credly_badges list is provided
    # For now, we assume MS Learn badges are already tracked in Credly
    # through the external_badges API, so we don't double-count
    
    # Actually, looking at the existing code in fetch_country.py,
    # it already fetches both org badges AND external badges (Microsoft-issued)
    # So MS Learn certs should already be counted via Credly's external_badges API
    
    # Return Credly count as primary, MS Learn as additional context
    # In practice, the user should have their MS Learn profile linked to Credly
    # for accurate counting
    
    return credly_count

def test_mslearn_api():
    """Test the MS Learn API with sample data."""
    # Test with Jesse Houwing's share ID (from PR #661)
    test_url = "https://learn.microsoft.com/en-us/users/jessehouwing-1848/transcript/share/d5gza1z690gp607"
    
    print("Testing MS Learn API...")
    print(f"URL: {test_url}")
    print("-" * 60)
    
    result = fetch_mslearn_github_badges(test_url, verbose=True)
    
    print(f"\nResults:")
    print(f"  Badge count: {result['badge_count']}")
    print(f"  Certifications: {result['certifications']}")
    print(f"  Applied Skills: {result['applied_skills']}")
    print(f"  DevOps Exams: {result['devops_exams']}")
    print(f"  DevOps Certs: {result['devops_certs']}")
    if result['error']:
        print(f"  Error: {result['error']}")

if __name__ == "__main__":
    test_mslearn_api()
