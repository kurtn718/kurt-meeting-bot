"""
Recall.ai API wrapper module
Handles all interactions with the Recall.ai API for bot creation and management.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
RECALL_API_KEY = os.getenv("RECALL_API_KEY", "your_api_key_here")
BASE_URL = "https://us-west-2.recall.ai/api/v1"


def create_bot_with_realtime_and_chat(meeting_url, webhook_url):
    """
    Create a bot that captures:
    - Real-time transcription via AssemblyAI
    - Chat messages
    - Meeting recording

    Args:
        meeting_url: The Zoom/Teams/Meet meeting URL
        webhook_url: The webhook endpoint to receive events

    Returns:
        dict: Bot data including bot ID, or None if creation failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "meeting_url": meeting_url,
        "bot_name": "Kurt's Clone",
        "automatic_leave": {
            "waiting_room_timeout": 600,  # Stay in waiting room for 10 mins
            "noone_joined_timeout": 600,   # Wait 10 mins if no one joins
            "everyone_left_timeout": 2     # Leave 2 secs after everyone leaves
        },
        "chat": {
            "on_bot_joined": {
                "send_to": "everyone",
                "message": "👋 Kurt's Clone here! I'm the upgraded version. Mention 'Kurt' or '@kurtbot' in chat to talk to me, or DM me anytime! Ask me 'how were you created?' to learn my origin story. 😎"
            }
        },
        "recording_config": {
            "recording_mode": "speaker_view",  # Explicitly enable recording
            "transcript": {
                "provider": {
                    "assembly_ai_v3_streaming": {
                        "punctuate": True,
                        "format_text": True
                    }
                }
            },
            "realtime_endpoints": [
                {
                    "type": "webhook",
                    "url": webhook_url,
                    "events": ["participant_events.chat_message"]
                }
            ]
        }
    }

    response = requests.post(f"{BASE_URL}/bot/", json=payload, headers=headers)

    if response.status_code == 201:
        bot_data = response.json()
        print(f"✅ Bot created successfully! ID: {bot_data['id']}")
        return bot_data
    else:
        print(f"❌ Error creating bot: {response.status_code}")
        print(response.text)
        return None


def send_chat_message(bot_id, to, message):
    """
    Send a chat message in the meeting

    Args:
        bot_id: The bot's UUID
        to: Either "everyone" or a participant ID
        message: The message text to send

    Returns:
        dict: Response data, or None if sending failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "to": to,
        "message": message
    }

    response = requests.post(
        f"{BASE_URL}/bot/{bot_id}/send_chat_message/",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        print(f"✅ Message sent: {message}")
        return response.json()
    else:
        print(f"❌ Error sending message: {response.status_code}")
        print(response.text)
        return None


def create_async_transcript(recording_id):
    """
    Generate a high-quality async transcript using AssemblyAI

    Args:
        recording_id: The recording's UUID

    Returns:
        dict: Transcript data including transcript ID, or None if creation failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "provider": {
            "assembly_ai_async": {
                "language_code": "en_us",
                "punctuate": True,
                "format_text": True,
                "speaker_labels": True,
                "disfluencies": False,
                "sentiment_analysis": True,
                "auto_chapters": True,
                "entity_detection": True
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/recording/{recording_id}/create_transcript/",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        transcript_data = response.json()
        print(f"✅ Async transcript requested! ID: {transcript_data['id']}")
        return transcript_data
    else:
        print(f"❌ Error creating async transcript: {response.status_code}")
        print(response.text)
        return None


def get_transcript(transcript_id):
    """
    Retrieve the completed async transcript

    Args:
        transcript_id: The transcript's UUID

    Returns:
        dict: Transcript data, or None if retrieval failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(
        f"{BASE_URL}/transcript/{transcript_id}/",
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error getting transcript: {response.status_code}")
        return None


def download_transcript_file(transcript_id, output_file="transcript.json"):
    """
    Download the transcript JSON file

    Args:
        transcript_id: The transcript's UUID
        output_file: Path where transcript should be saved

    Returns:
        bool: True if download succeeded, False otherwise
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}"
    }

    # First get the transcript to get the download URL
    transcript = get_transcript(transcript_id)

    if transcript and transcript['data']['download_url']:
        download_url = transcript['data']['download_url']

        response = requests.get(download_url)

        if response.status_code == 200:
            with open(output_file, 'w') as f:
                f.write(response.text)
            print(f"✅ Transcript downloaded to {output_file}")
            return True

    print("❌ Could not download transcript")
    return False


def get_bot_status(bot_id):
    """
    Check the current status of a bot

    Args:
        bot_id: The bot's UUID

    Returns:
        dict: Bot status data, or None if retrieval failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(f"{BASE_URL}/bot/{bot_id}/", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error getting bot status: {response.status_code}")
        return None


def list_bots():
    """
    List all bots

    Returns:
        list: List of bot data, or None if retrieval failed
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(f"{BASE_URL}/bot/", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error listing bots: {response.status_code}")
        print(response.text)
        return None


def remove_bot(bot_id):
    """
    Remove a bot from the meeting (makes the bot leave)

    Args:
        bot_id: The bot's UUID

    Returns:
        bool: True if removal succeeded, False otherwise
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.delete(f"{BASE_URL}/bot/{bot_id}/", headers=headers)

    if response.status_code == 204:
        print(f"✅ Bot {bot_id} removed successfully")
        return True
    else:
        print(f"❌ Error removing bot: {response.status_code}")
        print(response.text)
        return False


def leave_meeting(bot_id):
    """
    Make a bot leave the meeting it's currently in

    Args:
        bot_id: The bot's UUID

    Returns:
        bool: True if leave command succeeded, False otherwise
    """
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/bot/{bot_id}/leave_call/",
        headers=headers
    )

    if response.status_code == 200:
        print(f"✅ Bot {bot_id} is leaving the meeting")
        return True
    else:
        print(f"❌ Error making bot leave: {response.status_code}")
        print(response.text)
        return False
