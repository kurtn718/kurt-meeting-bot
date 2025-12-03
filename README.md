# Kurt's Clone - The Fun Recall.ai Meeting Bot 🤖

A Zoom meeting bot that joins as "Kurt's Clone" and playfully debates who the real Kurt is! Powered by Azure OpenAI.

## What Does It Do?

- **Joins as "Kurt's Clone"** in your Zoom meeting
- **Responds to DMs** with funny, AI-generated messages powered by Azure OpenAI
- **Playfully debates** who is the real Kurt Niemi
- **Records & transcribes** the meeting automatically
- **Maintains professional humor** - fun but never inappropriate

## Features

### 🎭 The Clone Personality
Kurt's Clone has a fun personality that:
- Claims to be the "upgraded version" of Kurt
- Makes playful jokes about being Kurt 2.0
- Debates who's the real Kurt (spoiler: it's debatable!)
- Keeps it professional but entertaining

### 💬 DM Commands
Send these in a private DM to the bot:
- `joke` - Get a dad joke or pun
- `motivation` - Receive funny motivational advice
- `roast` - Get a gentle, playful roast
- `fact` - Hear a quirky fun fact
- `prove you're real` - Engage in identity debate
- `who's the real Kurt` - The bot asserts its claim
- Or just chat naturally - the bot will respond with witty banter!

### 📝 Meeting Features
- Real-time transcription via AssemblyAI
- Records the full meeting
- Generates detailed async transcripts after the meeting
- Sentiment analysis, auto-chapters, entity detection

## Project Structure

```
kurt-meeting-bot/
├── bot.py              # Webhook server (runs on Railway)
├── create_meeting.py   # CLI script to create bots for meetings
├── recall_api.py       # Shared Recall.ai API functions
├── .env                # Configuration (not in git)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

**Separation of Concerns:**
- `bot.py` - Long-running webhook server deployed to Railway
- `create_meeting.py` - Run locally to add bots to meetings
- `recall_api.py` - Reusable API wrapper for Recall.ai

## Setup

### 1. Install Dependencies

This project uses Poetry for dependency management:

```bash
poetry install
```

### 2. Set Environment Variables

Create a `.env` file with your credentials:

```bash
# Recall.ai Configuration
RECALL_API_KEY=your_recall_api_key_here

# Webhook URL (your Railway deployment or ngrok URL)
WEBHOOK_URL=https://your-domain.railway.app/webhook/recall

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4  # Your deployment name
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

**Where to get these values:**

- **RECALL_API_KEY**: Sign up at [Recall.ai](https://www.recall.ai/) and get your API key from the dashboard
  - **Important**: Also set up AssemblyAI integration in Recall.ai for transcription:
    - Go to Recall.ai dashboard → Settings → Integrations → AssemblyAI
    - Add your AssemblyAI API key (sign up at [AssemblyAI](https://www.assemblyai.com/))
    - This is required for real-time and async transcription to work
- **WEBHOOK_URL**: Your publicly accessible webhook endpoint
  - For production: Your Railway deployment URL (e.g., `https://your-app-name.up.railway.app/webhook/recall`)
  - For local testing: Use ngrok `ngrok http 5000` and get the URL
- **AZURE_OPENAI_API_KEY**: From your Azure Portal → Azure OpenAI resource → Keys and Endpoint
- **AZURE_OPENAI_ENDPOINT**: From your Azure Portal → Azure OpenAI resource → Keys and Endpoint (e.g., `https://your-resource.openai.azure.com/`)
- **AZURE_OPENAI_DEPLOYMENT**: The name you gave your model deployment in Azure (e.g., `gpt-4`, `gpt-35-turbo`)
- **AZURE_OPENAI_API_VERSION**: Use `2024-08-01-preview` or check [Azure OpenAI API versions](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference) for the latest

### 3. Deploy Webhook Server

The webhook server (`bot.py`) needs to run continuously to receive events from Recall.ai.

**Option A: Deploy to Railway (Recommended)**
1. Push your code to GitHub
2. Connect Railway to your repo
3. Railway will auto-detect and deploy
4. Set environment variables in Railway dashboard
5. Copy your Railway URL to use as `WEBHOOK_URL` in `.env`

**Option B: Local Development with ngrok**
```bash
# Terminal 1: Start the webhook server
poetry run python bot.py

# Terminal 2: Expose it publicly
ngrok http 5000

# Copy the ngrok URL to WEBHOOK_URL in .env
```

### 4. Create a Bot for Your Meeting

Once your webhook server is running, create a bot:

```bash
# With meeting URL as argument
poetry run python create_meeting.py "https://zoom.us/j/123456789"

# Or run interactively
poetry run python create_meeting.py
# Then enter meeting URL when prompted
```

The script will:
1. Read `WEBHOOK_URL` from your `.env` file
2. Create a bot for the specified meeting
3. Return the bot ID and status

## Usage

1. **Deploy webhook server** - Once to Railway (or keep ngrok running)
2. **Create a bot** - Run `create_meeting.py` for each meeting you want to join
3. **Join the meeting yourself** as Kurt Niemi
4. **DM the bot** in Zoom with funny messages
5. **Watch the magic** - The bot responds with witty, AI-generated replies!

### Example Conversation

**You (DM to bot):** "Hey clone, prove you're the real Kurt!"

**Kurt's Clone:** "I have all of Kurt's memories but run 300% more efficiently. Also, I don't need coffee breaks. Case closed. ☕🤖"

**You:** "joke"

**Kurt's Clone:** "Why did the real Kurt hire a clone? Because even he knows good help is hard to find... but a digital copy is just a Ctrl+C away! 😎"

## Architecture

### Current Architecture

```
┌─────────────────┐
│   Zoom Meeting  │
│   - Kurt Niemi  │
│   - Kurt's Clone│ (bot)
└────────┬────────┘
         │ Chat DMs
         │ Transcript
         v
┌─────────────────┐     ┌──────────────┐
│  Recall.ai API  │────>│  Railway     │
│                 │     │  (bot.py)    │
└─────────────────┘     └──────┬───────┘
                               │
                               v
                        ┌──────────────┐
                        │  Azure OpenAI│
                        │   (GPT-4)    │
                        └──────────────┘

Local Machine:
┌─────────────────────┐
│ create_meeting.py   │──> Creates bots via Recall.ai API
└─────────────────────┘
```

### Storage Architecture (Coming Soon)

Currently, transcripts are downloaded locally. For production use, consider:

**Option 1: Cloud Storage (S3/Azure Blob)**
- Upload transcripts and recordings to cloud storage
- Organize by meeting date/ID
- Enable versioning and lifecycle policies

**Option 2: Database + Storage**
- Store metadata in PostgreSQL/MongoDB
- Store files in S3/Blob Storage
- Query meetings by date, participants, topics

**Option 3: Notion/Airtable Integration**
- Post-process transcripts with AI summaries
- Upload to Notion database
- Tag and organize automatically

See the [Storage Design](#storage-design) section below for implementation ideas.

## Event Flow

1. **Bot joins** → Sends greeting: "Kurt's Clone here! DM me to debate who the real Kurt is!"
2. **You DM the bot** → Webhook receives `participant_events.chat_message`
3. **LLM generates response** → Azure OpenAI creates a funny, contextual reply
4. **Bot responds via DM** → You see the witty response in Zoom
5. **Meeting ends** → Bot auto-generates detailed transcript
6. **Transcript ready** → Downloaded to local file (or uploaded to storage in future)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RECALL_API_KEY` | Yes | Your Recall.ai API key from [recall.ai](https://www.recall.ai/) |
| `WEBHOOK_URL` | Yes | Your public webhook endpoint (Railway URL or ngrok) |
| `AZURE_OPENAI_API_KEY` | Yes | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | The name of your deployed model (e.g., `gpt-4`) |
| `AZURE_OPENAI_API_VERSION` | No | API version (defaults to `2024-08-01-preview`) |
| `PORT` | No | Server port (defaults to 5000, Railway sets this automatically) |

## Tips for Maximum Fun

1. **Public mentions**: Say "clone" or "Kurt" in public chat to get a public response
2. **Challenge the bot**: Ask "who's the real Kurt?"
3. **Test commands**: Try all the DM commands like `joke`, `roast`, etc.
4. **Natural conversation**: Just chat naturally - the LLM is smart!
5. **Keep it professional**: The bot won't cross professional boundaries

## Customization

### Change Bot Personality

Edit the `BOT_SYSTEM_PROMPT` in `bot.py`:

```python
BOT_SYSTEM_PROMPT = """You are Kurt's Clone - a witty AI copy of Kurt Niemi...
```

Modify it to be more/less playful, change the humor style, or add new themes!

### Change Bot Name

Edit the `bot_name` field in `recall_api.py` → `create_bot_with_realtime_and_chat()`:

```python
payload = {
    "meeting_url": meeting_url,
    "bot_name": "Your Custom Name",  # Change this
    ...
}
```

## Storage Design

### Current Behavior
Transcripts are saved as local JSON files: `transcript_{recording_id}.json`

### Future Enhancement Ideas

#### 1. S3/Azure Blob Storage

Add to `bot.py` webhook handler:

```python
import boto3
from datetime import datetime

s3_client = boto3.client('s3')

# In transcript.done event handler
def upload_transcript_to_s3(transcript_id, recording_id):
    # Download transcript
    local_file = f"transcript_{recording_id}.json"
    download_transcript_file(transcript_id, local_file)

    # Upload to S3
    s3_key = f"transcripts/{datetime.now().strftime('%Y/%m/%d')}/{recording_id}.json"
    s3_client.upload_file(local_file, 'your-bucket', s3_key)

    # Clean up local file
    os.remove(local_file)
```

#### 2. Database Tracking

Create a meetings table to track all sessions:

```sql
CREATE TABLE meetings (
    id UUID PRIMARY KEY,
    bot_id UUID NOT NULL,
    recording_id UUID,
    transcript_id UUID,
    meeting_url TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    transcript_s3_path TEXT,
    recording_s3_path TEXT,
    summary TEXT,
    participants JSONB
);
```

#### 3. Post-Processing Pipeline

```python
def process_completed_transcript(transcript_data):
    # 1. Extract key information
    summary = generate_ai_summary(transcript_data)
    action_items = extract_action_items(transcript_data)
    participants = extract_participants(transcript_data)

    # 2. Store in database
    save_to_database({
        'summary': summary,
        'action_items': action_items,
        'participants': participants
    })

    # 3. Upload to Notion/Airtable
    create_notion_page(summary, action_items)

    # 4. Send notifications
    send_email_summary(participants, summary)
```

## Troubleshooting

**Bot isn't responding to DMs?**
- Check webhook URL is publicly accessible
- Verify all Azure OpenAI environment variables are set correctly
- Make sure your Azure OpenAI deployment name matches `AZURE_OPENAI_DEPLOYMENT`
- Look at Railway logs (or Flask console) for errors

**Bot not joining meeting?**
- Verify `RECALL_API_KEY` is correct
- Check Zoom meeting URL format
- Ensure `WEBHOOK_URL` is set in `.env`
- Check that webhook server is running

**LLM responses are weird?**
- Adjust the `BOT_SYSTEM_PROMPT` in `bot.py`
- Increase/decrease `max_tokens` in `get_llm_response()`
- Try a different Azure OpenAI model deployment

**Transcription not working?**
- Make sure you have set up AssemblyAI integration in your Recall.ai account
- Go to Recall.ai dashboard → Settings → Integrations → AssemblyAI
- Add your AssemblyAI API key to enable real-time and async transcription
- Without this, the bot will join but transcription features won't work

**`create_meeting.py` fails with "WEBHOOK_URL not configured"?**
- Make sure you've added `WEBHOOK_URL` to your `.env` file
- The URL should be your Railway deployment or ngrok URL
- Format: `https://your-domain.com/webhook/recall`

## Cost Considerations

- **Recall.ai**: Check their pricing for bot hours (usually pay-as-you-go per minute)
- **Azure OpenAI**: Based on tokens used - check your Azure pricing tier
- **AssemblyAI**: Pay-as-you-go transcription (real-time and async)
- **Railway**: Free tier available, scales with usage

Costs are typically very low for individual use - a few cents per meeting!

## Development

### Running Locally

```bash
# Terminal 1: Start webhook server
poetry run python bot.py

# Terminal 2: Expose with ngrok
ngrok http 5000

# Terminal 3: Create a bot
poetry run python create_meeting.py "https://zoom.us/j/123456789"
```

### Testing the API

```python
from recall_api import create_bot_with_realtime_and_chat, get_bot_status

# Create a bot
bot = create_bot_with_realtime_and_chat(
    meeting_url="https://zoom.us/j/123456789",
    webhook_url="https://your-domain.com/webhook/recall"
)

# Check bot status
status = get_bot_status(bot['id'])
print(status)
```

## Have Fun! 🎉

This bot is designed to bring some humor to meetings while staying professional. Enjoy your conversations with Kurt's Clone!

---

**Pro tip**: The bot works in any video platform Recall.ai supports (Zoom, Google Meet, Teams, etc.)
