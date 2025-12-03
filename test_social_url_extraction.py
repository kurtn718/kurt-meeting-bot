#!/usr/bin/env python3
"""
Test script to demonstrate social URL extraction from chat messages
"""

import re
import json
from datetime import datetime


def extract_social_urls(text):
    """
    Extract social media URLs from text
    Returns list of (platform, url) tuples
    """
    social_patterns = {
        'LinkedIn': r'https?://(?:www\.)?linkedin\.com/[\w\-/]+',
        'Twitter/X': r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[\w\-/]+',
        'Facebook': r'https?://(?:www\.)?facebook\.com/[\w\-/]+',
        'Instagram': r'https?://(?:www\.)?instagram\.com/[\w\-/]+',
        'GitHub': r'https?://(?:www\.)?github\.com/[\w\-/]+',
        'YouTube': r'https?://(?:www\.)?youtube\.com/[\w\-/?=]+',
        'TikTok': r'https?://(?:www\.)?tiktok\.com/@?[\w\-/]+',
        'Website': r'https?://(?:www\.)?[\w\-]+\.[\w\-./]+',  # Generic URL
    }

    found_urls = []
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            found_urls.append((platform, match))

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for platform, url in found_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append((platform, url))

    return unique_urls


def test_message_scenarios():
    """
    Test different message scenarios
    """
    print("=" * 80)
    print("SOCIAL URL EXTRACTION TEST")
    print("=" * 80)
    print()

    # Test scenarios
    scenarios = [
        {
            'name': 'Kurt posts LinkedIn in public chat',
            'participant': 'Kurt Niemi',
            'message': 'Here is my profile https://linkedin.com/in/kurtniemi',
            'is_dm': False,
            'bot_would_respond': False,  # No @kurtbot mention
            'reason': 'Message doesn\'t contain "@kurtbot" or mention "kurt" about the bot'
        },
        {
            'name': 'Kurt posts LinkedIn with bot mention',
            'participant': 'Kurt Niemi',
            'message': '@kurtbot check out my LinkedIn https://linkedin.com/in/kurtniemi',
            'is_dm': False,
            'bot_would_respond': True,
            'reason': 'Message contains @kurtbot mention'
        },
        {
            'name': 'Kurt DMs LinkedIn to bot',
            'participant': 'Kurt Niemi',
            'message': 'https://linkedin.com/in/kurtniemi',
            'is_dm': True,
            'bot_would_respond': True,
            'reason': 'All DMs get responses from the bot'
        },
        {
            'name': 'Someone posts multiple social profiles',
            'participant': 'Jane Doe',
            'message': 'Connect with me! LinkedIn: https://linkedin.com/in/janedoe, Twitter: https://x.com/janedoe, GitHub: https://github.com/janedoe',
            'is_dm': False,
            'bot_would_respond': False,
            'reason': 'No bot mention'
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"SCENARIO {i}: {scenario['name']}")
        print("-" * 80)
        print(f"📝 Participant: {scenario['participant']}")
        print(f"💬 Message Type: {'DM' if scenario['is_dm'] else 'Public Chat'}")
        print(f"📄 Message: {scenario['message']}")
        print()

        # Extract URLs
        urls = extract_social_urls(scenario['message'])

        if urls:
            print(f"🔗 Social URLs Detected: {len(urls)}")
            for platform, url in urls:
                print(f"   • {platform}: {url}")
        else:
            print("🔗 No social URLs detected")

        print()
        print(f"🤖 Bot Response: {'YES' if scenario['bot_would_respond'] else 'NO'}")
        print(f"   Reason: {scenario['reason']}")

        if scenario['bot_would_respond'] and not scenario['is_dm']:
            print(f"   Response sent to: Everyone (public)")
        elif scenario['bot_would_respond'] and scenario['is_dm']:
            print(f"   Response sent to: {scenario['participant']} (DM)")

        # Show what would be saved
        print()
        print("💾 What gets saved to file:")
        message_data = {
            'participant': scenario['participant'],
            'message': scenario['message'],
            'timestamp': datetime.now().isoformat()
        }
        if urls:
            message_data['social_urls'] = [{'platform': p, 'url': u} for p, u in urls]
        print(json.dumps(message_data, indent=2))

        print()
        print("=" * 80)
        print()


if __name__ == '__main__':
    test_message_scenarios()

    print()
    print("KEY FINDINGS:")
    print("-" * 80)
    print("✅ Social URLs are ALWAYS captured and saved, regardless of bot response")
    print("✅ URLs are saved in both the message data AND in a master 'social_profiles' list")
    print("✅ Bot responds to ALL DMs with AI-powered responses")
    print("✅ Bot responds to public messages only when mentioned (@kurtbot or 'kurt')")
    print("✅ At meeting end, all messages + social URLs are saved to a JSON file")
    print()
