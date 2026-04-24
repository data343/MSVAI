import os
import argparse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Import functions from the new modules
from slack_api import (
    get_dm_conversations,
    get_channel_messages,
    get_all_team_messages,
    get_channel_id_by_name,
    list_channels_by_type,
    send_slack_message,
    get_conversation_context
)
from slack_formatter import (
    format_dms_for_output,
    format_public_channels_for_output,
    format_private_channels_for_output,
    format_messages_for_output,
    format_conversation_context_for_display
)

# --- Utility Function ---

def write_to_file(content, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Output successfully written to {filename}")
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Slack data fetcher.")
    parser.add_argument(
        "--action",
        choices=[
            "get_dms", 
            "get_team_messages",
            "get_specific_channel_messages",
            "list_public_channels",
            "list_private_channels",
            "send_message",
            "get_context"
        ],
        required=True,
        help="The action to perform."
    )
    parser.add_argument(
        "--channel-name",
        type=str,
        help="The name of the specific channel or DM user (required for 'get_specific_channel_messages', 'send_message', 'get_context' actions)."
    )
    parser.add_argument(
        "--message",
        type=str,
        help="The message text to send (required for 'send_message' action)."
    )
    parser.add_argument(
        "--thread-ts",
        type=str,
        help="Optional. Timestamp of a parent message to reply in its thread (for 'send_message' action)."
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Optional. Path to a .md file to save the output. Prints to terminal if not provided."
    )
    parser.add_argument(
        "--limit-per-channel",
        type=int,
        default=50, 
        help="Maximum number of messages to fetch per channel. For 'get_context', set to 0 or negative to fetch all messages (default for get_context is 20, for others 50)."
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=None, # Default to None, meaning fetch by limit only unless specified
        help="Optional. Number of past days of history to fetch for 'get_specific_channel_messages' and 'get_team_messages'. Overrides limit if both used for depth."
    )
    parser.add_argument(
        "--filter-user-id",
        type=str,
        default=None,
        help="Optional. Filter messages to include only those from this Slack User ID."
    )
    args = parser.parse_args()

    # Adjust limit for get_context if not explicitly set for it or if all messages are requested
    if args.action == "get_context":
        if args.limit_per_channel <= 0: # User wants all messages
            args.limit_per_channel = None 
        elif args.limit_per_channel == 50: # If still default from general arg, set to get_context default
             args.limit_per_channel = 20


    slack_token = os.environ.get("SLACK_USER_TOKEN")
    if not slack_token:
        print("Error: SLACK_USER_TOKEN environment variable not set.")
        return

    client = WebClient(token=slack_token)
    output_content = ""

    try:
        if args.action == "get_dms":
            dm_users = get_dm_conversations(client)
            output_content = format_dms_for_output(dm_users)
        elif args.action == "get_team_messages":
            team_messages = get_all_team_messages(
                client, 
                limit_per_channel=args.limit_per_channel,
                history_days=args.history_days,
                filter_user_id=args.filter_user_id # Pass filter_user_id
            )
            output_content = format_messages_for_output(team_messages)
        elif args.action == "get_specific_channel_messages":
            if not args.channel_name:
                print("Error: --channel-name is required for 'get_specific_channel_messages' action.")
                return
            channel_id = get_channel_id_by_name(client, args.channel_name)
            if channel_id:
                channel_messages = get_channel_messages(
                    client, 
                    channel_id, 
                    args.channel_name, 
                    limit_per_channel=args.limit_per_channel,
                    history_days=args.history_days,
                    filter_user_id=args.filter_user_id # Pass filter_user_id
                )
                output_content = format_messages_for_output(channel_messages)
            else:
                output_content = f"# Messages for {args.channel_name}\n\nChannel '{args.channel_name}' not found or access denied."
        elif args.action == "list_public_channels":
            public_channels = list_channels_by_type(client, "public_channel")
            output_content = format_public_channels_for_output(public_channels)
        elif args.action == "list_private_channels":
            private_channels = list_channels_by_type(client, "private_channel")
            output_content = format_private_channels_for_output(private_channels)
        elif args.action == "send_message":
            if not args.channel_name or not args.message:
                print("Error: --channel-name and --message are required for 'send_message' action.")
                return
            channel_id = get_channel_id_by_name(client, args.channel_name)
            if channel_id:
                message_ts = send_slack_message(client, channel_id, args.message, args.thread_ts)
                if message_ts:
                    output_content = f"Message sent successfully to {args.channel_name} (ID: {channel_id}). Timestamp: {message_ts}"
                else:
                    output_content = f"Failed to send message to {args.channel_name} (ID: {channel_id})."
            else:
                output_content = f"Channel or DM '{args.channel_name}' not found or access denied."
        elif args.action == "get_context":
            if not args.channel_name:
                print("Error: --channel-name is required for 'get_context' action.")
                return
            channel_id = get_channel_id_by_name(client, args.channel_name)
            if channel_id:
                conversation_history = get_conversation_context(client, channel_id, args.channel_name, message_limit=args.limit_per_channel)
                output_content = format_conversation_context_for_display(conversation_history, args.channel_name)
            else:
                output_content = f"# Context for {args.channel_name}\n\nChannel '{args.channel_name}' not found or access denied."


    except SlackApiError as e:
        print(f"An unhandled Slack API error occurred in main: {e.response['error']}")
        output_content = f"Error: {e.response['error']}"
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")
        output_content = f"Unexpected Error: {e}"


    if output_content:
        if args.output_file:
            write_to_file(output_content, args.output_file)
        else:
            print("\n--- Output ---")
            print(output_content)
            print("--- End of Output ---")

if __name__ == "__main__":
    main()
