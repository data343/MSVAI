# MSVAI Weekly Reports Setup Guide

This guide will help you set up the MSVAI weekly reports system on a new Mac device.

## Prerequisites

- macOS with Python 3.8 or higher
- Git installed
- Slack workspace access with appropriate permissions

## Quick Setup (Automated)

For fast setup, run the automated script after cloning:

```bash
# Clone repository
git clone <repository-url> MSVAI
cd MSVAI

# Run automated setup
./setup.sh

# Verify setup
python verify_setup.py
```

## Step-by-Step Setup (Manual)

### 1. Clone the Repository

```bash
# Replace <repository-url> with your actual repository URL
git clone <repository-url> MSVAI
cd MSVAI
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required dependencies
pip install pytz slack_sdk langdetect requests
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env  # If .env.example exists
# OR create .env manually
touch .env
```

Add the following variables to `.env`:

```env
# Required: Slack User Token (get from https://api.slack.com/apps)
SLACK_USER_TOKEN=xoxp-your-slack-user-token-here

# Optional: OpenRouter API Key for AI-powered replies
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

#### Getting Slack Token:
1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create or select your app
3. Go to "OAuth & Permissions"
4. Install app to workspace
5. Copy the "User OAuth Token" (starts with `xoxp-`)

#### Getting OpenRouter API Key (Optional):
1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up/login and go to API Keys
3. Create a new API key

### 4. Verify Required Files

Ensure these files exist in your repository:

**Main Scripts:**
- `jobs/check_weekly_reports.py` - Main application
- `jobs/generate_report_reply.py` - AI reply generator

**Configuration Files:**
- `.clinerules/companyoverview.md` - Team member data
- `jobs/serhii_ceo_reply_style.md` - AI style guide

**Auto-created Files (if missing):**
- `jobs/report_log.csv` - Created automatically on first run
- `jobs/replied_log.json` - Created automatically when needed
- `jobs/reporter_custom_deadlines.json` - Optional, create if custom deadlines needed

### 5. Create Missing Directories

```bash
# Create reports directory for storing weekly reports
mkdir -p reports
```

### 6. Test the Setup

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Test the main script
python jobs/check_weekly_reports.py --help

# Test with current date (will show help and available options)
python jobs/check_weekly_reports.py
```

## Usage

### Basic Usage

```bash
# Check today's reports
python jobs/check_weekly_reports.py

# Check specific date
python jobs/check_weekly_reports.py --date 2024-11-18

# Reply to specific people by name
python jobs/check_weekly_reports.py --reply-to-names "John Doe,Jane Smith"

# Reply to specific people by Slack User ID
python jobs/check_weekly_reports.py --reply-to-ids "U123456789,U987654321"
```

### Available Features

- **Report Checking**: Automatically checks if team members submitted weekly reports
- **Status Tracking**: Categorizes reports as on-time, late, or missing
- **Interactive Replies**: Respond to reports with default, custom, or AI-generated replies
- **Logging**: All activities logged to `jobs/report_log.csv`
- **Report Storage**: Individual reports saved to `reports/YYYY-MM-DD/`

### Reply Options

When prompted to reply to a report:
- `d` - Send default reply
- `c` - Send custom reply (type your own)
- `a` - AI-generated reply (requires OpenRouter API key)
- `s` - Skip this person
- `exit` - Exit reply mode

## Configuration

### Custom Deadlines

Create `jobs/reporter_custom_deadlines.json` for custom deadlines:

```json
{
  "U123456789": "09:00:00",
  "U987654321": "14:30:00"
}
```

### Team Member Updates

Update `.clinerules/companyoverview.md` when team members change. The format is:

```markdown
### Weekly Reporting Structure
- **Name** (Title: Job Title) (Slack User ID: U123456789, IM ID: D123456789) (Reports to: Manager)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure virtual environment is activated and dependencies installed
2. **Slack API errors**: Verify token permissions and validity
3. **No reports found**: Check if Slack User IDs in companyoverview.md are correct
4. **Permission denied**: Ensure app has necessary Slack permissions

### Required Slack Permissions

Your Slack app needs these OAuth scopes:
- `channels:history` - Read public channel messages
- `im:history` - Read direct messages
- `chat:write` - Send messages
- `users:read` - Read user information

## Development Notes

- Script uses Europe/Kiev timezone by default
- Reports are checked for Monday of the specified week
- All file paths are relative to project root
- Virtual environment should always be activated when running scripts

## File Structure

```
MSVAI/
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── jobs/
│   ├── check_weekly_reports.py   # Main script
│   ├── generate_report_reply.py  # AI reply generator
│   ├── report_log.csv           # Activity log
│   ├── replied_log.json         # Reply tracking
│   ├── reporter_custom_deadlines.json  # Custom deadlines
│   └── serhii_ceo_reply_style.md # AI style guide
├── .clinerules/
│   └── companyoverview.md       # Team data
├── reports/                     # Generated reports
├── venv/                        # Python virtual environment
└── requirements.txt             # Python dependencies
```