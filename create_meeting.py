#!/usr/bin/env python3
"""
Create Meeting Bot CLI
Standalone script to create a Recall.ai bot for a specific meeting.
"""

import os
import sys
from dotenv import load_dotenv
from recall_api import create_bot_with_realtime_and_chat, get_bot_status

# Load environment variables
load_dotenv()

# Get webhook URL from environment
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


def main():
    """
    Main function to create a bot for a meeting
    """
    print("🤖 Kurt's Clone - Meeting Bot Creator")
    print("=" * 50)

    # Validate webhook URL is configured
    if not WEBHOOK_URL or WEBHOOK_URL == "":
        print("❌ Error: WEBHOOK_URL not configured in .env file")
        print("Please add WEBHOOK_URL=https://your-domain.com/webhook/recall to your .env file")
        sys.exit(1)

    print(f"✓ Webhook URL: {WEBHOOK_URL}")
    print()

    # Get meeting URL from command line or prompt
    if len(sys.argv) > 1:
        meeting_url = sys.argv[1]
    else:
        meeting_url = input("Enter Zoom/Teams/Meet meeting URL: ").strip()

    if not meeting_url:
        print("❌ Error: Meeting URL is required")
        sys.exit(1)

    print(f"\n🚀 Creating bot for meeting: {meeting_url}")
    print(f"📡 Using webhook: {WEBHOOK_URL}")
    print()

    # Create the bot
    bot_data = create_bot_with_realtime_and_chat(meeting_url, WEBHOOK_URL)

    if bot_data:
        bot_id = bot_data['id']
        print(f"\n✅ Bot created successfully!")
        print(f"📋 Bot ID: {bot_id}")
        print(f"\n🎉 Bot will join the meeting shortly...")
        print(f"\n💡 Try these fun interactions:")
        print(f"   - DM the bot: 'joke' for a dad joke")
        print(f"   - DM the bot: 'motivation' for funny motivation")
        print(f"   - DM the bot: 'roast' for a gentle meeting roast")
        print(f"   - DM the bot: 'fact' for a fun fact")
        print(f"   - Or just chat naturally with Kurt's Clone!")
        print(f"\n📊 To check bot status later, use:")
        print(f"   python -c \"from recall_api import get_bot_status; print(get_bot_status('{bot_id}'))\"")
    else:
        print("\n❌ Failed to create bot. Please check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
