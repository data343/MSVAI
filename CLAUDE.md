# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MSVAI is a weekly reporting automation system for managing team reports through Slack. The system tracks submission deadlines, logs report status (on-time, late, missing), stores reports to disk, and provides interactive CLI for responding to reports with AI-generated replies.

## Key Commands

### Setup and Installation
```bash
# First-time setup (automated)
./setup.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify setup
python verify_setup.py
```

### Development Workflow
```bash
# Activate virtual environment (required for all operations)
source venv/bin/activate

# Check weekly reports (main functionality)
python jobs/check_weekly_reports.py

# Check reports for specific date
python jobs/check_weekly_reports.py --date 2024-11-18

# Reply to specific people by name
python jobs/check_weekly_reports.py --reply-to-names "John Doe,Jane Smith"

# Reply to specific people by Slack User ID
python jobs/check_weekly_reports.py --reply-to-ids "U123456789,U987654321"

# Test AI reply generation (standalone)
python jobs/generate_report_reply.py
```

### Testing and Debugging
```bash
# Get help for main script
python jobs/check_weekly_reports.py --help

# Check required dependencies
python -c "import pytz, slack_sdk, langdetect, requests; print('All dependencies OK')"
```

## Architecture

### Core Components

**Main Script**: `jobs/check_weekly_reports.py` (477 lines)
- Fetches team member list from `.clinerules/companyoverview.md`
- Queries Slack API for DM history on reporting day (Monday)
- Determines report status: on_time, late, or missing based on deadline (default 13:00 Kyiv time)
- Provides interactive CLI for responding to reports
- Logs all activity to `jobs/report_log.csv`
- Stores individual reports to `reports/YYYY-MM-DD/Name.md`

**AI Reply Generator**: `jobs/generate_report_reply.py`
- Uses OpenRouter API with `meta-llama/llama-4-scout` model
- Detects report language (Ukrainian, Russian, English) using `langdetect`
- Applies CEO's communication style from `jobs/serhii_ceo_reply_style.md`
- Generates context-aware, brief replies

**Slack API Wrapper**: `connectors/slack-connect/slack_api.py`
- Handles DM conversations, channel messages, message sending
- Includes fuzzy matching for channel/user lookup using `thefuzz`
- Supports message threading and pagination
- Provides conversation context retrieval

**Google Sheets Integration**: `connectors/google-sheets-connect/`
- API wrapper for Google Sheets operations
- Used for data import/export tasks

### Data Flow

1. User runs `check_weekly_reports.py` with optional date/filters
2. Script parses `.clinerules/companyoverview.md` for team structure
3. Loads custom deadlines from `jobs/reporter_custom_deadlines.json` (if exists)
4. Loads replied log from `jobs/replied_log.json` to avoid duplicate replies
5. Queries Slack API for Monday DM messages in Europe/Kiev timezone
6. Determines status by comparing first message timestamp to deadline
7. Saves reports to `reports/YYYY-MM-DD/Reporter_Name.md`
8. Logs status to `jobs/report_log.csv`
9. Displays interactive prompt for replying (default, custom, AI)
10. Updates `jobs/replied_log.json` after successful reply

### Critical Configuration

**Timezone**: All operations use `Europe/Kiev` timezone (defined as `KYIV_TIMEZONE`)
- Reports checked for Monday of target week
- Default deadline: 13:00:00 Kyiv time
- Custom deadlines supported via `jobs/reporter_custom_deadlines.json`

**Team Structure**: `.clinerules/companyoverview.md`
- Contains "### Weekly Reporting Structure" section
- Format: `- **Name** (Title: Job Title) (Slack User ID: U123456789, IM ID: D123456789) (Reports to: Manager)`
- Must have both Slack User ID (starts with U) and IM ID (starts with D)

**Environment Variables**:
- `SLACK_USER_TOKEN` (required) - xoxp- token from Slack API
- `OPENROUTER_API_KEY` (optional) - for AI reply generation

### File Structure

```
MSVAI/
├── .clinerules/           # AI assistant rules and company data
│   ├── companyoverview.md # Team member database (critical)
│   ├── logbook.md
│   └── msvrules.md
├── connectors/            # External API integrations
│   ├── slack-connect/
│   │   ├── slack_api.py  # Core Slack operations
│   │   ├── slack_formatter.py
│   │   └── main.py
│   └── google-sheets-connect/
├── jobs/                  # Main application scripts
│   ├── check_weekly_reports.py  # Primary script (477 lines)
│   ├── generate_report_reply.py # AI reply generator
│   ├── report_log.csv           # Activity log (auto-created)
│   ├── replied_log.json         # Reply tracking (auto-created)
│   ├── reporter_custom_deadlines.json  # Optional config
│   └── serhii_ceo_reply_style.md       # AI style guide
├── memory-bank/           # Documentation and context
│   ├── activeContext.md
│   ├── logbook.md
│   ├── progress.md
│   ├── techContext.md
│   └── [11 other context files]
├── reports/               # Generated reports by date
│   └── YYYY-MM-DD/       # One directory per week
│       └── Reporter_Name.md
├── scripts/               # Utility scripts
│   ├── analyze_boss_messages.py
│   ├── get_monthly_messages.py
│   └── parse_pdf.py
├── datastore/             # Data storage
│   └── google-sheets-cache/
├── .env                   # Environment variables (not in git)
├── requirements.txt       # Python dependencies
├── setup.sh              # Automated setup script
└── verify_setup.py       # Setup verification
```

## Development Guidelines

### Working with Slack Integration

**Important**: The Slack token must have these OAuth scopes:
- `channels:history` - Read public channel messages
- `im:history` - Read direct messages
- `chat:write` - Send messages
- `users:read` - Read user information

**Testing Slack Features**: Always test in DMs first before modifying message-sending logic.

### Timezone Handling

**CRITICAL**: All datetime operations must use `KYIV_TIMEZONE = pytz.timezone("Europe/Kiev")`

```python
# Correct timezone handling
target_date_dt = datetime.now(KYIV_TIMEZONE)
deadline_dt = KYIV_TIMEZONE.localize(datetime.combine(date, time(13, 0, 0)))

# Incorrect (will cause timezone bugs)
deadline_dt = datetime.combine(date, time(13, 0, 0))  # No timezone info
```

**Recent Bug**: The CSV logging previously saved timestamps in system time instead of Kyiv time. Always specify `tz=KYIV_TIMEZONE` when converting timestamps.

### Adding New Team Members

Edit `.clinerules/companyoverview.md` under "### Weekly Reporting Structure":

```markdown
- **Full Name** (Title: Job Title) (Slack User ID: U123456789, IM ID: D123456789) (Reports to: Manager Name)
```

Get Slack User ID and IM ID:
1. User ID: Use Slack API `users.list` or check user profile
2. IM ID: Use Slack API `conversations.list` with `types=im` filtered by user

### Custom Deadlines

Create/edit `jobs/reporter_custom_deadlines.json`:

```json
{
  "U123456789": "09:00:00",
  "U987654321": "14:30:00"
}
```

Key is Slack User ID, value is time in HH:MM:SS format (Kyiv timezone).

### Known Technical Debt

See `refactor_todo.md` for detailed analysis. Key issues:

1. **Single Responsibility**: `check_weekly_reports.py` handles too many concerns (Slack API, file I/O, CLI, business logic)
2. **Testing**: No unit tests exist (high risk for changes)
3. **Function Naming**: Some functions have unclear names (`say()`, `check()`)
4. **Code Size**: Main file is 477 lines (getting unwieldy)

**Before Major Refactoring**: Add tests first to ensure existing functionality isn't broken.

### Reply Options During Interactive Mode

When prompted to reply to a report:
- `d` - Send default reply (random from predefined list)
- `c` - Send custom reply (type your own)
- `a` - AI-generated reply (requires OPENROUTER_API_KEY)
- `s` - Skip this person
- `exit` - Exit reply mode

AI reply sub-options:
- `y` - Send suggested reply
- `e` - Edit suggested reply
- `b` - Back to main menu

## Common Development Tasks

### Debugging Report Status Issues

The status determination logic (`determine_report_status` in check_weekly_reports.py:182):
```python
# A report is "on_time" if first_ts < deadline_ts
# Otherwise it's "late"
# If no messages, it's "missing"
```

Check these if status is incorrect:
1. Verify deadline_ts is in Kyiv timezone
2. Confirm first message timestamp is correctly extracted
3. Check custom deadlines JSON if user has custom time
4. Verify Slack User ID matches in companyoverview.md

### Adding New Connectors

Follow the pattern in `connectors/slack-connect/`:
1. Create API wrapper module (`*_api.py`)
2. Add main entry point (`main.py`)
3. Include formatter/helper if needed
4. Import in main scripts as needed

### Working with Memory Bank

The `memory-bank/` directory contains:
- `activeContext.md` - Current work context
- `progress.md` - Development progress log
- `techContext.md` - Technical decisions and architecture
- `logbook.md` - Development journal
- `systemPatterns.md` - Design patterns used

Update these when making significant architectural changes.

## Troubleshooting

### "SLACK_USER_TOKEN not set"
```bash
# Check .env file exists and has token
cat .env | grep SLACK_USER_TOKEN

# Set token manually
export SLACK_USER_TOKEN=xoxp-your-token-here
```

### "No reporters found"
Check `.clinerules/companyoverview.md`:
- Has "### Weekly Reporting Structure" section
- Each line matches regex: `- \*\*(.+?)\*\*.*?\(Slack User ID: (U[A-Z0-9]+), IM ID: (D[A-Z0-9]+)\)`

### Timezone Issues
All operations should use `Europe/Kiev` timezone. If seeing system timezone (Prague/other):
- Check `KYIV_TIMEZONE` is used in datetime operations
- Verify `tz=KYIV_TIMEZONE` parameter in `datetime.fromtimestamp()` calls

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Slack API Permission Errors
Verify token has required scopes at https://api.slack.com/apps → Your App → OAuth & Permissions
