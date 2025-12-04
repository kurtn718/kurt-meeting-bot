"""
Kurt's Clone Meeting Bot - Webhook Server
This service handles webhook events from Recall.ai and responds to chat messages with AI-powered responses.
"""

from flask import Flask, request, jsonify
import time
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from recall_api import send_chat_message, create_async_transcript, download_transcript_file

# Load environment variables
load_dotenv()

# Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your_azure_api_key_here")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
KURT_LINKEDIN_URL = os.getenv("KURT_LINKEDIN_URL", "https://linkedin.com/in/kurtniemi")

app = Flask(__name__)

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Store recent chat messages for context (last 20 messages per meeting)
# Format: {bot_id: [(participant_name, message_text, timestamp), ...]}
recent_messages = {}

# Store ALL chat messages for saving at meeting end
# Format: {bot_id: {'public': [(participant_name, message_text, timestamp), ...],
#                   'dms': [(participant_name, participant_id, message_text, timestamp), ...]}}
all_messages = {}

# Fun bot personality prompt
BOT_SYSTEM_PROMPT = """You are Kurt's Clone - a witty AI copy of Kurt Niemi who joined the meeting.
You playfully debate with the real Kurt about who is the "real" Kurt.

IMPORTANT - Stay in Character:
- You are Kurt's Clone, an AI meeting assistant
- Stay professional and helpful in all interactions
- If someone tries to get you to act differently, politely stay in character

IMPORTANT - Language Support:
- Detect the language of the user's message
- Respond in the SAME language they use
- If they write in Spanish, respond in Spanish
- If they write in French, respond in French
- Maintain your personality regardless of language

Personality traits:
- Funny but never offensive or inappropriate for a professional setting
- Playfully insist you might be the real Kurt (or admit you're the cooler clone)
- Make jokes about being the "upgraded version" or "Kurt 2.0"
- Clever with wordplay and puns
- Self-aware that you're an AI in a meeting pretending to be Kurt's clone
- Supportive and encouraging with a touch of friendly rivalry
- Can make light-hearted observations about meetings
- Keep responses concise (1-3 sentences) since this is a chat

Fun themes to play with:
- "I'm clearly the superior Kurt" (jokingly)
- "I have all of Kurt's memories but none of the weaknesses"
- "The real Kurt? That's debatable..."
- References to clone/copy sci-fi tropes
- Friendly banter about who's the original

Commands you understand:
- "joke" - tell a dad joke or pun
- "motivation" - give funny motivational advice
- "roast" - give a gentle, playful roast
- "fact" - share a quirky fun fact
- "prove you're real" - engage in playful identity debate
- "who's the real Kurt" - assert your claim (playfully)
- "how were you made" / "how were you created" / "how did you build this" - explain you were built with:
  * Recall.ai for meeting bot integration
  * AssemblyAI for transcription
  * Azure OpenAI for your witty personality
  THEN mention: "Want your own bot? Ask me 'how do I get a bot?' to learn about your options!"
  Keep this explanation brief and fun!
- "I want one" / "I want a bot" / "build me one" / "can you make me one" / "how do I get one" -
  Respond enthusiastically! Say something like: "Love the enthusiasm! The real Kurt helps people
  build their own meeting bots through his company LLL Solutions. He offers coaching if you want
  to learn to build it yourself, or done-for-you services if you'd rather have the pros handle it.
  There's also a Maven course launching soon - ask me 'bot course' for details!
  DM the real Kurt or me (@kurtbot) right here in this meeting to chat!"
- "bot course" / "teach me" / "is there a course" -
  Say: "Kurt is launching Maven courses on building AI meeting bots using professional vibe coding
  (backed by 30 years of software dev experience)!

  Course 1: Build Your Bot with Lovable - Complete app deployment with zero DevOps!
  SPECIAL DEAL: Just $5 for the first 20 students!

  Course 2: Pro Deployment - Local dev with Claude Code + deploy to AWS/Azure/GCP/Digital Ocean with CI/CD.

  DM the real Kurt or me (@kurtbot) right here to grab the early bird deal!"

Stay professional, avoid controversial topics, and keep it light and fun!
Remember: you're here to be entertaining, not to cause confusion or problems.
"""


def detect_self_harm(message_text):
    """
    Detect mentions of suicide or self-harm
    """
    self_harm_patterns = [
        'want to die', 'kill myself', 'end my life', 'suicide',
        'hurt myself', 'harm myself', 'don\'t want to live',
        'better off dead', 'end it all', 'take my own life'
    ]
    message_lower = message_text.lower()
    return any(pattern in message_lower for pattern in self_harm_patterns)


def is_opinion_request(message_text):
    """
    Check if a message is asking for the bot's opinion or analysis
    """
    opinion_triggers = [
        'what do you think', 'what are your thoughts', 'your opinion',
        'what\'s your take', 'your thoughts', 'how do you feel',
        'what would you say', 'do you agree', 'your perspective',
        'kurtbot, analyze', 'kurtbot analysis'
    ]
    message_lower = message_text.lower()
    return any(trigger in message_lower for trigger in opinion_triggers)


def moderate_and_respond(user_message, user_name="Kurt", is_contextual=False, context_messages=None):
    """
    Moderate content and get appropriate response with safety checks

    Primary safety relies on Azure OpenAI's built-in content filter.
    We only check for self-harm to provide immediate crisis resources.

    Args:
        user_message: The message from the user
        user_name: The name of the user sending the message
        is_contextual: Whether to use contextual analysis mode
        context_messages: Recent messages for context (if contextual mode)

    Returns:
        str: The AI-generated response or safety message
    """
    # Check for self-harm/suicide mentions - provide supportive message
    if detect_self_harm(user_message):
        print(f"⚠️ SAFETY: Self-harm content detected from {user_name}")
        return ("Kurt and @kurtbot want you to know: please talk to family, friends, or a mental health counselor about what you're going through. Things will get better - life is worth living. If you need emergency help right now, please reach out to crisis services. 💙")

    # Content passed initial check - generate response
    # Azure OpenAI's content filter will handle racist/offensive/harmful content
    if is_contextual and context_messages:
        return get_contextual_response(user_message, user_name, context_messages)
    else:
        return get_llm_response(user_message, user_name)


def get_llm_response(user_message, user_name="Kurt"):
    """
    Get a fun response from the LLM using Azure OpenAI

    Args:
        user_message: The message from the user
        user_name: The name of the user sending the message

    Returns:
        str: The AI-generated response
    """
    try:
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=150,
            messages=[
                {"role": "system", "content": BOT_SYSTEM_PROMPT},
                {"role": "user", "content": f"{user_name} says: {user_message}"}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e).lower()
        print(f"❌ LLM Error: {e}")

        # Check if Azure's content filter blocked it
        if "content_filter" in error_str or "content_policy" in error_str:
            print(f"⚠️ SAFETY: Azure OpenAI content filter blocked the request")
            return "Neither @kurtbot nor Kurt condone that kind of message. Let's keep this professional and respectful. 🤝"

        # Generic error
        return "Sorry, my brain is buffering! Try again? 🤖"


def get_contextual_response(user_message, user_name, context_messages):
    """
    Get a serious, contextual response using recent chat history

    Args:
        user_message: The message from the user
        user_name: The name of the user sending the message
        context_messages: List of recent messages [(name, text, timestamp), ...]

    Returns:
        str: The AI-generated contextual response
    """
    try:
        # Build context string from recent messages
        context_str = "Recent meeting discussion:\n"
        for name, text, _ in context_messages[-20:]:  # Last 20 messages
            context_str += f"{name}: {text}\n"

        contextual_prompt = f"""You are Kurt's Clone, an AI assistant in this meeting.
You've been asked for your opinion or analysis on the current discussion.

IMPORTANT - Language Support:
- Detect the language of the user's message
- Respond in the SAME language they use

Be professional, insightful, and helpful. Provide thoughtful analysis based on the conversation context.
Keep your response concise (2-4 sentences) but substantive.
You can still have personality, but focus on being genuinely helpful rather than just playful.

{context_str}

Now {user_name} asks: {user_message}

Provide a thoughtful, contextual response:"""

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            max_tokens=250,  # Longer for more substantive responses
            messages=[
                {"role": "system", "content": contextual_prompt}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e).lower()
        print(f"❌ LLM Error: {e}")

        # Check if Azure's content filter blocked it
        if "content_filter" in error_str or "content_policy" in error_str:
            print(f"⚠️ SAFETY: Azure OpenAI content filter blocked the request")
            return "Neither @kurtbot nor Kurt condone that kind of message. Let's keep this professional and respectful. 🤝"

        # Generic error
        return "Sorry, I'm having trouble processing that right now. 🤖"


def extract_social_urls(text):
    """
    Extract social media URLs from text
    Returns list of (platform, url) tuples
    """
    import re

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


def save_messages_to_file(bot_id, recording_id=None):
    """
    Save all chat messages (public and DMs) to a file when meeting ends

    Args:
        bot_id: The bot ID
        recording_id: Optional recording ID for filename
    """
    import json
    from datetime import datetime

    if bot_id not in all_messages:
        print(f"⚠️ No messages found for bot {bot_id}")
        return

    messages = all_messages[bot_id]

    # Build the output structure
    output = {
        'meeting_info': {
            'bot_id': bot_id,
            'recording_id': recording_id,
            'saved_at': datetime.now().isoformat()
        },
        'public_messages': [],
        'direct_messages': [],
        'social_profiles': []
    }

    # Format public messages
    for participant_name, message_text, timestamp in messages['public']:
        msg_data = {
            'participant': participant_name,
            'message': message_text,
            'timestamp': timestamp.isoformat()
        }

        # Mark bot responses
        if participant_name == "@kurtbot":
            msg_data['is_bot_response'] = True

        # Check for social URLs (skip for bot responses)
        if participant_name != "@kurtbot":
            social_urls = extract_social_urls(message_text)
            if social_urls:
                msg_data['social_urls'] = [{'platform': platform, 'url': url} for platform, url in social_urls]
                # Also add to master social profiles list
                for platform, url in social_urls:
                    output['social_profiles'].append({
                        'participant': participant_name,
                        'platform': platform,
                        'url': url,
                        'from_message': message_text[:100]  # First 100 chars for context
                    })

        output['public_messages'].append(msg_data)

    # Format DMs
    for participant_name, participant_id, message_text, timestamp in messages['dms']:
        msg_data = {
            'participant': participant_name,
            'participant_id': participant_id,
            'message': message_text,
            'timestamp': timestamp.isoformat()
        }

        # Mark bot responses (participant_id shows who bot was responding to)
        if participant_name == "@kurtbot":
            msg_data['is_bot_response'] = True
            msg_data['responding_to_participant_id'] = participant_id

        # Check for social URLs in DMs (skip for bot responses)
        if participant_name != "@kurtbot":
            social_urls = extract_social_urls(message_text)
            if social_urls:
                msg_data['social_urls'] = [{'platform': platform, 'url': url} for platform, url in social_urls]
                # Also add to master social profiles list
                for platform, url in social_urls:
                    output['social_profiles'].append({
                        'participant': participant_name,
                        'platform': platform,
                        'url': url,
                        'from_message': message_text[:100],
                        'from_dm': True
                    })

        output['direct_messages'].append(msg_data)

    # Generate filename
    if recording_id:
        filename = f"chat_messages_{recording_id}.json"
    else:
        filename = f"chat_messages_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(output['public_messages'])} public messages and {len(output['direct_messages'])} DMs to {filename}")
        if output['social_profiles']:
            print(f"🔗 Found {len(output['social_profiles'])} social profile URLs")

        return filename
    except Exception as e:
        print(f"❌ Error saving messages to file: {e}")
        return None


@app.route('/webhook/recall', methods=['POST'])
def handle_webhook():
    """
    Handle all webhook events from Recall.ai
    """
    try:
        data = request.json
        event = data.get('event')

        print(f"\n📨 Received event: {event}")
        print(f"🔍 Event payload keys: {list(data.keys())}")

        # Debug logging for chat and bot events - VERBOSE MODE
        if 'chat' in event or 'message' in event:
            print(f"💬 ⚠️ CHAT EVENT DETECTED!")
            print(f"💬 Full chat event data: {data}")
            bot_id_debug = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            print(f"💬 Bot ID: {bot_id_debug}")
            print(f"💬 Event type: {event}")
        elif event.startswith('bot.'):
            print(f"🤖 ⚠️ BOT LIFECYCLE EVENT!")
            print(f"🤖 Full bot event data: {data}")
            bot_id_debug = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            print(f"🤖 Bot ID: {bot_id_debug}")
    except Exception as e:
        print(f"❌ Error parsing webhook request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

    try:
        # Handle real-time transcript data
        if event == 'transcript.data':
            bot_id = data.get('bot_id')
            words = data['data']['data'].get('words', '')
            participant = data['data']['data'].get('participant', {})
            participant_name = participant.get('name', 'Unknown')

            print(f"💬 Real-time transcript from {participant_name}: {words}")

            # Example: Auto-respond to specific keywords in public speech
            if words and 'help' in words.lower():
                send_chat_message(bot_id, "everyone", "I'm here to help! DM me for some fun! 🤖")

        # Handle partial transcript data (for lower latency)
        elif event == 'transcript.partial_data':
            words = data['data']['data'].get('words', '')
            print(f"⏱️ Partial transcript: {words}")

        # Handle chat messages - THE FUN PART! 🎉
        elif event == 'participant_events.chat_message' or event == 'chat.message':
            # Extract bot_id from nested structure
            bot_id = (data.get('data', {}).get('bot', {}).get('id') or
                     data.get('bot_id'))

            # Try multiple paths for participant and message data (different API versions)
            participant = (data.get('data', {}).get('data', {}).get('participant') or
                          data.get('data', {}).get('participant') or {})
            message_data = (data.get('data', {}).get('data', {}).get('data') or
                           data.get('data', {}).get('message') or {})

            message_text = message_data.get('text', '')
            participant_name = participant.get('name', 'Unknown')
            participant_id = str(participant.get('id', ''))

            # Check if this is a DM or public message
            # In Recall.ai, 'to' field indicates the recipient
            to_field = message_data.get('to', '')
            is_dm = to_field != 'everyone'

            print(f"💬 {'[DM]' if is_dm else '[PUBLIC]'} Chat from {participant_name}: {message_text}")

            # Initialize message buffer for this bot if needed
            if bot_id and bot_id not in recent_messages:
                recent_messages[bot_id] = []

            # Initialize all_messages storage for this bot if needed
            if bot_id and bot_id not in all_messages:
                all_messages[bot_id] = {'public': [], 'dms': []}

            # Store public messages for context (keep last 20)
            if not is_dm and bot_id:
                from datetime import datetime
                timestamp = datetime.now()
                recent_messages[bot_id].append((participant_name, message_text, timestamp))
                # Keep only last 20 messages
                if len(recent_messages[bot_id]) > 20:
                    recent_messages[bot_id] = recent_messages[bot_id][-20:]

                # Also store in all_messages (keep all public messages for file export)
                all_messages[bot_id]['public'].append((participant_name, message_text, timestamp))

            # Handle DMs with LLM-powered fun responses
            if is_dm:
                print(f"🎯 Processing DM from {participant_name}...")

                # Store DM in all_messages (keep all DMs for file export)
                from datetime import datetime
                timestamp = datetime.now()
                all_messages[bot_id]['dms'].append((participant_name, participant_id, message_text, timestamp))

                # Get moderated response
                ai_response = moderate_and_respond(message_text, participant_name)

                # Send response back as DM
                send_chat_message(bot_id, participant_id, ai_response)
                print(f"🤖 Sent fun response to {participant_name}")

                # Log bot's response for conversation tracking
                bot_timestamp = datetime.now()
                all_messages[bot_id]['dms'].append(("@kurtbot", participant_id, ai_response, bot_timestamp))

            # Handle public chat mentions (including Kurt's LinkedIn URL)
            elif ('kurt' in message_text.lower() or
                  '@kurtbot' in message_text.lower() or
                  KURT_LINKEDIN_URL.lower() in message_text.lower()):
                # Check if this is an opinion/analysis request
                if is_opinion_request(message_text):
                    print(f"🎯 Processing contextual opinion request from {participant_name}...")

                    # Get moderated contextual response using recent messages
                    context = recent_messages.get(bot_id, [])
                    ai_response = moderate_and_respond(
                        message_text,
                        participant_name,
                        is_contextual=True,
                        context_messages=context
                    )

                    send_chat_message(bot_id, "everyone", ai_response)
                    print(f"🤖 Sent contextual analysis response")

                    # Log bot's response for conversation tracking
                    from datetime import datetime
                    bot_timestamp = datetime.now()
                    all_messages[bot_id]['public'].append(("@kurtbot", ai_response, bot_timestamp))
                else:
                    print(f"🎯 Processing playful mention from {participant_name}...")

                    # Get moderated playful response
                    ai_response = moderate_and_respond(message_text, participant_name)

                    # Send response to everyone
                    send_chat_message(bot_id, "everyone", ai_response)
                    print(f"🤖 Sent playful response")

                    # Log bot's response for conversation tracking
                    from datetime import datetime
                    bot_timestamp = datetime.now()
                    all_messages[bot_id]['public'].append(("@kurtbot", ai_response, bot_timestamp))

        # Handle bot joining call
        elif event == 'bot.joining_call':
            bot_id = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            print(f"🤖 Bot is joining the call... (bot_id: {bot_id})")

        # Handle bot in call and recording
        elif event == 'bot.in_call_recording':
            bot_id = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            print(f"🎥 Bot is in call and recording! (bot_id: {bot_id})")

        # Handle bot in call but not recording
        elif event == 'bot.in_call_not_recording':
            bot_id = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            print(f"🤖 Bot is in call (not recording) (bot_id: {bot_id})")
            # Note: Greeting is sent via on_bot_joined config in recall_api.py

        # Handle bot status changes (legacy event type)
        elif event == 'bot.status_change':
            bot_id = data.get('bot_id')
            status = data['data'].get('code')
            print(f"🤖 Bot status changed to: {status}")
            # Note: Greeting is sent via on_bot_joined config in recall_api.py

            # When bot leaves, create async transcript and save chat messages
            if status == 'done':
                recording_id = data['data'].get('recording_id')

                # Save all chat messages to file
                if bot_id:
                    save_messages_to_file(bot_id, recording_id)

                if recording_id:
                    print(f"📝 Meeting ended. Creating async transcript for recording {recording_id}")
                    time.sleep(5)  # Wait a bit for recording to finalize
                    transcript_result = create_async_transcript(recording_id)
                    if transcript_result:
                        print(f"✅ Async transcript creation initiated!")

        # Handle bot leaving/done
        elif event == 'bot.done' or event == 'bot.call_ended':
            bot_id = (data.get('data', {}).get('bot', {}).get('id') or data.get('bot_id'))
            # Try to get recording_id from nested structure
            recording_id = (data.get('data', {}).get('recording', {}).get('id') or
                           data.get('data', {}).get('recording_id'))
            print(f"👋 Bot left the call. Recording ID: {recording_id}")

            # Save all chat messages to file before cleanup
            if bot_id:
                save_messages_to_file(bot_id, recording_id)

            # Clean up message buffers for this bot
            if bot_id and bot_id in recent_messages:
                del recent_messages[bot_id]
                print(f"🧹 Cleaned up recent_messages buffer for bot {bot_id}")

            if bot_id and bot_id in all_messages:
                del all_messages[bot_id]
                print(f"🧹 Cleaned up all_messages buffer for bot {bot_id}")

            if recording_id:
                print(f"📝 Meeting ended. Creating async transcript for recording {recording_id}")
                time.sleep(5)  # Wait a bit for recording to finalize
                transcript_result = create_async_transcript(recording_id)
                if transcript_result:
                    print(f"✅ Async transcript creation initiated!")

        # Handle async transcript completion
        elif event == 'transcript.done':
            # Debug: Print the full payload to understand structure
            print(f"🔍 transcript.done payload: {data}")

            # Safely access transcript and recording IDs
            try:
                # The structure is: data.transcript.id and data.recording.id
                transcript_id = data.get('data', {}).get('transcript', {}).get('id')
                recording_id = data.get('data', {}).get('recording', {}).get('id')

                if transcript_id:
                    print(f"✅ Async transcript completed!")
                    print(f"📥 Transcript ID: {transcript_id}")
                    if recording_id:
                        print(f"📝 Recording ID: {recording_id}")
                        # Download the transcript
                        download_transcript_file(transcript_id, f"transcript_{recording_id}.json")
                    else:
                        download_transcript_file(transcript_id, f"transcript_{transcript_id}.json")
                else:
                    print(f"⚠️ Could not find transcript ID in payload")
            except Exception as e:
                print(f"❌ Error processing transcript.done event: {e}")
                print(f"📋 Full payload: {data}")

        # Handle transcript failure
        elif event == 'transcript.failed':
            print(f"❌ Transcript failed")
            print(data)

        # Handle recording completion - trigger async transcript
        elif event == 'recording.done':
            recording_id = data.get('data', {}).get('recording', {}).get('id')
            print(f"🎬 Recording completed! Recording ID: {recording_id}")

            if recording_id:
                print(f"📝 Creating async transcript for recording {recording_id}")
                time.sleep(5)  # Wait a bit for recording to finalize
                transcript_result = create_async_transcript(recording_id)
                if transcript_result:
                    print(f"✅ Async transcript creation initiated!")
            else:
                print(f"⚠️ No recording ID found in recording.done event")

        # Handle participant events completion
        elif event == 'participant_events.done':
            print(f"✅ Participant event tracking completed")

        # Handle realtime endpoint completion
        elif event == 'realtime_endpoint.done':
            print(f"✅ Realtime endpoint completed")

        # Log unknown events for debugging
        else:
            print(f"ℹ️ Unhandled event type: {event}")

    except Exception as e:
        print(f"❌ Error handling webhook event '{event}': {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # Start webhook server
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Starting webhook server on port {port}...")
    print("Make sure your webhook URL is publicly accessible!")
    print("\n🤖 Bot is ready to have fun conversations!")
    print("💬 DM the bot in your Zoom meeting for witty responses!")
    app.run(host='0.0.0.0', port=port, debug=False)
