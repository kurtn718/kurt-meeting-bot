#!/usr/bin/env python3
"""
Meeting Bot Scheduler
Automatically joins meetings at scheduled times (default: 8:00 PM daily)
Run this script locally on your machine to auto-join meetings.
"""

import os
import sys
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv
from recall_api import create_bot_with_realtime_and_chat

# Load environment variables
load_dotenv()

# Configuration from .env
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MEETING_URL = os.getenv("MEETING_URL")  # Default meeting URL
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "20:00")  # Default: 8:00 PM


def join_meeting():
    """
    Join the configured meeting
    """
    print(f"\n{'=' * 60}")
    print(f"🕐 Scheduled join triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    # Validate configuration
    if not WEBHOOK_URL:
        print("❌ Error: WEBHOOK_URL not configured in .env file")
        return

    if not MEETING_URL:
        print("❌ Error: MEETING_URL not configured in .env file")
        print("Please add MEETING_URL to your .env file")
        return

    print(f"🚀 Creating bot for meeting: {MEETING_URL}")
    print(f"📡 Using webhook: {WEBHOOK_URL}")
    print()

    # Create the bot
    bot_data = create_bot_with_realtime_and_chat(MEETING_URL, WEBHOOK_URL)

    if bot_data:
        bot_id = bot_data['id']
        print(f"\n✅ Bot created successfully!")
        print(f"📋 Bot ID: {bot_id}")
        print(f"🎉 Bot is joining the meeting now...")
    else:
        print("\n❌ Failed to create bot. Check error messages above.")

    print(f"\n{'=' * 60}\n")


def main():
    """
    Main scheduler loop
    """
    print("🤖 Kurt's Clone - Meeting Bot Scheduler")
    print("=" * 60)
    print(f"⏰ Schedule Time: {SCHEDULE_TIME} daily")
    print(f"📡 Webhook URL: {WEBHOOK_URL or 'NOT CONFIGURED'}")
    print(f"🔗 Meeting URL: {MEETING_URL or 'NOT CONFIGURED'}")
    print("=" * 60)

    if not WEBHOOK_URL:
        print("\n❌ Error: WEBHOOK_URL not configured in .env")
        print("Please add WEBHOOK_URL to your .env file")
        sys.exit(1)

    if not MEETING_URL:
        print("\n⚠️  Warning: MEETING_URL not configured in .env")
        print("Add MEETING_URL to your .env file, or the scheduler won't work")
        print("Example: MEETING_URL=https://zoom.us/j/123456789")
        sys.exit(1)

    # Schedule the daily meeting join
    schedule.every().day.at(SCHEDULE_TIME).do(join_meeting)

    print(f"\n✅ Scheduler is running!")
    print(f"📅 Bot will auto-join at {SCHEDULE_TIME} every day")
    print(f"🔄 Press Ctrl+C to stop\n")

    # Optional: Join immediately for testing
    if "--now" in sys.argv:
        print("🧪 Test mode: Joining meeting immediately...")
        join_meeting()

    # Run the scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
