
# Company Logbook (Memory Bank)

## Purpose
This logbook records key company actions, decisions, and events related to projects and operations tracked within this Memory Bank, to preserve institutional memory and ensure continuity.

## Entry Structure

### Date Header Format
`## YYYY-MM-DD`

### Entry Format
`### [Category] Action/Decision Title`
`**Who**: Key participants (names/roles)`
`**What**: Clear description of the action or decision`
`**Why**: Brief context or reasoning`
`**Next**: Follow-up actions with deadlines (if applicable)`

## Categories
- **[STRATEGIC]**
- **[OPS]**
- **[FINANCE]**
- **[PEOPLE]**
- **[LEGAL]**
- **[CLIENT]**
- **[PRODUCT]**
- **[TECH]**
- **[PROJECT_INIT]** - Project Initiation
- **[PROJECT_MILESTONE]** - Project Milestone
- **[PROJECT_UPDATE]** - Project Update
- **[PROJECT_COMPLETION]** - Project Completion

---

## 2025-05-07

### [PROJECT_INIT] AI Assistant Initialization for CEO

**Who**: Serhii Yaremenko (CEO), Cline (AI Assistant)
**What**: Initiated the project to set up Cline as an AI assistant for the CEO. This involves creating and populating the Memory Bank to provide Cline with comprehensive context on company tasks, projects, and ongoing operations.
**Why**: To enable Cline to effectively support the CEO in operating the business by having a structured understanding of company activities.
**Next**: Create the remaining core Memory Bank files: `productContext.md`, `activeContext.md`, `systemPatterns.md`, `techContext.md`, and `progress.md`.

### [TECH] Initial Slack Connector Script Implemented
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: Developed an initial Python script (`connectors/slack-connect/main.py`) to interact with the Slack API. The script can:
    - Fetch a list of users the authenticated user has DMs with.
    - Fetch messages from all public and private channels the authenticated user is a member of.
    - It uses a User OAuth token provided via the `SLACK_USER_TOKEN` environment variable.
    - Includes `requirements.txt` for dependencies (`slack_sdk`) and a `README.md` for setup/usage.
**Why**: To provide a foundational capability for Cline to access and retrieve information from Slack, as per user request and part of the broader goal of integrating key communication channels.
**Next**: Guide the user through testing the script. Evaluate if an MCP server is required for more robust Slack integration.

### [PROJECT_UPDATE] Slack Connector Enhanced for Specific Channel Fetching
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by feedback)
**What**: Updated the `connectors/slack-connect/main.py` script and its `README.md`.
    - Added a new action `get_specific_channel_messages` allowing users to fetch messages from a channel specified by `--channel-name`.
    - Implemented `get_channel_id_by_name` function with pagination to find channel IDs.
    - Updated `README.md` with the new action and arguments.
**Why**: To fulfill user request to fetch messages from a specific channel ("01-hq-operation") and make the script more versatile.
**Next**: Guide the user on testing the new functionality.

### [PROJECT_UPDATE] Slack Connector Enhanced for Channel Listing
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by feedback)
**What**: Further updated the `connectors/slack-connect/main.py` script and `README.md`.
    - Added new actions: `list_public_channels` and `list_private_channels`.
    - Implemented `list_channels_by_type` function using `users_conversations` API with pagination.
    - Added corresponding output formatting functions.
    - Updated `README.md` to include these new actions and examples.
**Why**: To fulfill user request to list DMs, public channels, and private channels separately.
**Next**: Execute these actions to provide the lists to the user and advise on Memory Bank storage.

### [TECH] Slack Communication Context Documented
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: 
    - Updated the Slack connector script's formatting functions to sort DM/channel lists by name.
    - Executed script actions (`get_dms`, `list_public_channels`, `list_private_channels`) to fetch Slack context.
    - Created and populated `memory-bank/slack_communication_context.md` with these sorted lists.
    - Deleted temporary files used for gathering the lists.
**Why**: To provide a persistent, organized record of key Slack communication channels and contacts within the Memory Bank, as requested by the user.
**Next**: Confirm task completion with the user.

### [PROJECT_UPDATE] Slack DM List Enhanced with Deactivation Status & Grouping
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by feedback)
**What**: 
    - Updated `connectors/slack-connect/main.py` to fetch more user profile details (including deactivation status) for DM contacts.
    - Modified the DM output format to group contacts by active/deactivated status, then sort each group by name, and display detailed profile information.
    - Updated `memory-bank/slack_communication_context.md` with this new enhanced DM list.
**Why**: To fulfill user request for more detailed DM information and clear indication of deactivated users.
**Next**: Confirm task completion with the user.

### [TECH] Local Git Repository Initialized & First Commit
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: 
    - Confirmed Git installation and user configuration.
    - Created a `.gitignor5e` file in the project root (`f:/MSVAI`) with standard Python, OS, and VS Code ignores, plus project-specific exclusions.
    - Initialized a local Git repository in `f:/MSVAI`.
    - Added all relevant project files (`.clinerules/`, `.gitignore`, `connectors/`, `memory-bank/`, `scripts/`) to staging.
    - Made the initial commit (SHA: 571d90c) with the message "Initial commit of project structure and memory bank".
    - A warning regarding an embedded repository `connectors/slack-user-mcp` was noted during the commit.
    - Previous "dubious ownership" issue was resolved by adding the directory to Git's safe directories list.
**Why**: To establish version control for the MSVAI project, allowing for tracking changes and managing project history locally.
**Next**: Confirm task completion with the user.

### [OPS] Operational Rhythm Documentation Initiated
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: 
    - Created `memory-bank/operational_rhythm.md`.
    - Documented the weekly team report process, including purpose, frequency, deadline, submission guidelines, and report requirements, based on user input.
    - Designated the `jobs/` folder as the location for future automation scripts related to operational rhythms.
**Why**: To formalize and document key company operational cadences, starting with the weekly team reporting structure, and to plan for future automation.
**Next**: Update `activeContext.md` and `progress.md`. Begin planning for the development of scripts in `jobs/` to automate report tracking.

### [PEOPLE] Weekly Reporting Roster Added to Company Overview
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: 
    - Identified active team members from `memory-bank/slack_communication_context.md`.
    - Filtered this list based on user input to determine who is required to submit weekly reports.
    - Added a new "Weekly Reporting Structure" section to `.clinerules/companyoverview.md`.
    - Populated this section with the list of reporting team members and their titles, with placeholders for direct manager details ([Manager TBD]).
**Why**: To establish a documented list of individuals responsible for weekly reporting, as a step towards building a tracking system.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`). Gather direct manager details to complete the roster.

### [TECH] Slack Connector and Company Overview Enhanced with IM IDs
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**:
    - Modified `connectors/slack-connect/slack_api.py` to include the IM channel ID in the fetched DM user details.
    - Modified `connectors/slack-connect/slack_formatter.py` to display the IM channel ID alongside the User ID in the formatted DM list.
    - Executed the `get_dms` action of the Slack connector script to refresh `memory-bank/slack_communication_context.md` with the IM Channel IDs.
    - Updated the "Weekly Reporting Structure" in `.clinerules/companyoverview.md` to include the Slack User ID and IM Channel ID for each reporting team member.
**Why**: To enrich the reporting roster with specific Slack identifiers for easier automation and communication tracking.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`).

### [TECH] Weekly Report Checker Script v1 Created
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**:
    - Created the initial version of `jobs/check_weekly_reports.py`.
    - The script reads the reporting roster from `.clinerules/companyoverview.md`.
    - It fetches DM messages from reporters sent on the target Monday.
    - It categorizes submissions as 'on_time', 'late', or 'missing' based on the 13:00 Kyiv deadline.
    - It logs the status to `jobs/report_log.csv`.
    - It saves submitted messages to `reports/[YYYY-MM-DD]/[Reporter_Name].md`.
    - It provides interactive prompts to send reminders or replies.
    - Added `pytz` dependency to `connectors/slack-connect/requirements.txt`.
**Why**: To provide a tool for checking weekly report submissions, tracking compliance, and facilitating responses.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`). Guide user on installing requirements and testing the script.

### [TECH] Weekly Report Checker Script Enhanced
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**:
    - Updated `jobs/check_weekly_reports.py` to enhance the interactive reply loop.
    - Added an 'exit' option to quit the reply loop safely.
    - Added an 'a' (ask Cline) option, which prompts the user to ask Cline in the chat interface for a suggested reply based on the displayed messages.
**Why**: To improve the usability of the script's interactive reply feature based on user feedback.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`).

### [PEOPLE] Weekly Reporting Roster Updated
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: Removed Tanya Katashinskaya, Tatsiana Mrosenfeld, and Veronika Bespavlova from the "Weekly Reporting Structure" section in `.clinerules/companyoverview.md`.
**Why**: To reflect changes in who is required to submit weekly reports.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`).

### [TECH] Weekly Report Checker Script Refined
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by feedback)
**What**:
    - Updated `jobs/check_weekly_reports.py` to refine message filtering in `fetch_reporter_messages`, ensuring only messages from the specific human reporter are processed (ignoring bots/integrations).
    - Updated `connectors/slack-connect/slack_api.py` to add `as_user=True` parameter to `chat.postMessage` calls, attempting to make messages appear more directly from the user in Slack previews.
**Why**: To address user feedback about seeing integration names in message previews and ensure the script focuses only on reporter messages.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`).

### [TECH] Weekly Report Checker Script Default Replies Updated
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: Updated `jobs/check_weekly_reports.py` to replace the single default reply with a list of 10 options. The script now randomly selects one of these options when the user chooses the default reply action ('d') and prepends the reporter's name.
**Why**: To add variety and personalization to the default acknowledgment messages.
**Next**: Update Memory Bank files (`activeContext.md`, `progress.md`).

### [TECH] Google Sheets Connector v1 Created
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**:
    - Created a new Python-based connector in `connectors/google-sheets-connect/`.
    - Includes `main.py` (CLI), `google_sheets_api.py` (API interaction logic), `requirements.txt`, and `README.md`.
    - The connector uses OAuth 2.0 for authentication (requiring `credentials.json` from Google Cloud Console and generating `token.json`).
    - It can fetch data from a specified sheet or all sheets within a Google Spreadsheet.
    - It can save the fetched data as Parquet files into `datastore/google-sheets-cache/`.
    - Updated `.gitignore` to exclude `credentials.json` and `token.json` for this connector.
**Why**: To enable Cline to access and retrieve data from Google Sheets, a key information source for the company.
**Next**: Guide user on setting up Google Cloud credentials, installing requirements, and testing the connector. Update `activeContext.md` and `progress.md`.

### [PROJECT_UPDATE] Key Documents Index Created
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, by request)
**What**: Created `memory-bank/key_documents.md` with a table structure (Link, Short Description, Long Description).
**Why**: To provide a centralized, structured list of frequently used company documents for easy reference.
**Next**: Guide user to populate the document. Update `activeContext.md` and `progress.md`.

---

## 2025-05-09

### [PRODUCT] Proactive AI Monitoring Use Cases Defined
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO, through discussion)
**What**: Defined and documented several new use cases for Cline to proactively monitor Amazon operations. These include:
    - Customer-facing issue detection (product page inaccuracies, negative reviews).
    - Amazon Seller Central monitoring (commission rates, ad spend).
    - Profitability & performance monitoring (via Sellerboard or similar).
    - Inventory & logistics anomaly detection (stranded inventory).
    - Fee change monitoring & alerting (FBA fees).
    A new document `memory-bank/ai_monitoring_use_cases.md` was created to detail these. `productContext.md` and `progress.md` were updated to reflect this.
**Why**: To expand Cline's capabilities towards proactive operational support and risk mitigation, enabling faster responses to critical business events.
**Next**: Prioritize these use cases and begin technical feasibility investigation for high-priority items.

### [TECH] Slack Connector Enhanced for Direct ID Handling
**Who**: Cline (AI Assistant)
**What**: Modified the `get_channel_id_by_name` function in `connectors/slack-connect/slack_api.py`. The function now checks if the input `channel_name_to_find` is a direct Slack ID (starts with C, G, or D and has typical ID format). If so, it uses the ID directly, bypassing the fuzzy name search.
**Why**: To resolve an issue where the Slack connector failed to send messages when an IM ID was provided directly, as it was attempting to fuzzy match the ID string against channel/user names. This improves reliability when sending messages via known IDs.
**Next**: Further testing of Slack connector functionalities.

---

## 2025-05-13

### [PROJECT_COMPLETION] LLM-Powered Reply Generation Feature for Weekly Reports
**Who**: Cline (AI Assistant), Serhii Yaremenko (CEO)
**What**: Completed the multi-phase task to enhance the `jobs/check_weekly_reports.py` script with LLM-generated replies matching the CEO's style.
    - **Phase 1 (Previously Completed):** Created `jobs/serhii_ceo_reply_style.md` with initial structure.
    - **Phase 2:**
        - Reviewed collected Slack messages from `private/serhii_ceo_collected_replies_batch1.md`.
        - Populated `jobs/serhii_ceo_reply_style.md` with representative examples of CEO's communication style.
        - Confirmed `jobs/generate_report_reply.py` already implements the `ReportResponder` class.
        - Added `langdetect` to `connectors/slack-connect/requirements.txt`.
    - **Phase 3:**
        - Confirmed `jobs/check_weekly_reports.py` correctly imports and uses the `ReportResponder` class and includes appropriate interactive options ('a' for LLM prep, 'y' for LLM & send, 'e' for LLM & edit) for generating and sending replies.
    - **Enhancement (2025-05-13):** Updated the interactive reply loop in `jobs/check_weekly_reports.py`. After using the 'a' (LLM prep) option and an LLM suggestion is displayed, a new focused prompt allows the user to send the suggestion by pressing Enter, or choose to edit, regenerate, use custom/default, skip, or exit.
    - **Enhancement (2025-05-14):** Further simplified threaded replies in `jobs/check_weekly_reports.py`. The script now always replies in a thread to the first report message (if one exists) and always broadcasts this threaded reply to the main DM conversation. Prompts asking for threading/broadcasting preferences were removed.
**Why**: To enable the `jobs/check_weekly_reports.py` script to suggest and send replies that more closely match the CEO's communication style, improving the efficiency of handling weekly reports, and to make the user interface more streamlined for sending prepared suggestions and managing threaded replies with a fixed, preferred behavior.
**Next**: Monitor the effectiveness of the LLM-generated replies. User may need to run `pip install -r connectors/slack-connect/requirements.txt` to install `langdetect`.
