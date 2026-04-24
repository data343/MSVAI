# Slack Connector

This script connects to Slack to fetch information about DMs and channel messages.

## Setup

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variable:**
    You need to set the `SLACK_USER_TOKEN` environment variable to your Slack User OAuth token.
    
    *   **Windows (PowerShell):**
        ```powershell
        $env:SLACK_USER_TOKEN="your_slack_user_token_here" 
        ```
        (Note: This sets it for the current session. For persistent storage, you might use System Properties.)
    *   **Windows (Command Prompt):**
        ```cmd
        set SLACK_USER_TOKEN=your_slack_user_token_here
        ```
    *   **macOS/Linux:**
        ```bash
        export SLACK_USER_TOKEN="your_slack_user_token_here"
        ```
        (Add this line to your `.bashrc`, `.zshrc`, or shell configuration file for persistence.)

## Usage

The script `main.py` can be run to fetch information.

**Available Actions (specify with `--action`):**

*   `get_dms`: Get a list of users you have direct messages with.
*   `get_team_messages`: Get messages from all public and private channels you are a member of.
*   `get_specific_channel_messages`: Get messages from a specific channel by its name. Requires `--channel-name`.
*   `list_public_channels`: List all public channels in the workspace that you are part of.
*   `list_private_channels`: List all private channels you are a member of.
*   `send_message`: Sends a message to a specified channel or DM. Requires `--channel-name` and `--message`. Can optionally reply in a thread using `--thread-ts`.
*   `get_context`: Fetches recent messages (including threaded replies) from a specified channel or DM. Requires `--channel-name`.

**Arguments:**

*   `--channel-name <name>`: The name of the specific channel or DM user. Required for `get_specific_channel_messages`, `send_message`, and `get_context` actions.
*   `--message <text>`: The message text to send. Required for the `send_message` action.
*   `--thread-ts <timestamp>`: Optional. The timestamp of a parent message to reply within its thread. Used with the `send_message` action.
*   `--limit-per-channel <number>`: Maximum number of messages to fetch.
    *   For `get_team_messages` and `get_specific_channel_messages`: specifies messages per channel (default: 50).
    *   For `get_context`: specifies the number of parent messages to fetch (default: 20).
*   `--output-file <filename.md>`: Save output to a Markdown file instead of printing to terminal.

**Output Options:**

*   By default, output is printed to the terminal.
*   Use `--output-file <filename.md>` to save the output to a Markdown file.

**Examples:**

*   Get DMs and print to terminal:
    ```bash
    python main.py --action get_dms
    ```

*   Get team messages and save to `team_messages.md`:
    ```bash
    python main.py --action get_team_messages --output-file team_messages.md
    ```

*   Get the last 20 messages from channel "01-hq-operation" and print to terminal:
    ```bash
    python main.py --action get_specific_channel_messages --channel-name "01-hq-operation" --limit-per-channel 20
    ```

*   List all public channels:
    ```bash
    python main.py --action list_public_channels
    ```

*   List all private channels and save to `private_channels.md`:
    ```bash
    python main.py --action list_private_channels --output-file private_channels.md
    ```

*   Send a message "Hello there!" to the channel "general":
    ```bash
    python main.py --action send_message --channel-name "general" --message "Hello there!"
    ```

*   Reply "Got it, thanks!" in a thread (parent message timestamp "1234567890.123456") in the DM with "user.name":
    ```bash
    python main.py --action send_message --channel-name "user.name" --message "Got it, thanks!" --thread-ts "1234567890.123456"
    ```

*   Get the last 10 messages (including threads) from the channel "project-alpha" and print to terminal:
    ```bash
    python main.py --action get_context --channel-name "project-alpha" --limit-per-channel 10
    ```
