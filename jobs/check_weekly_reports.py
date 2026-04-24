import os
import csv
import argparse
from datetime import datetime, time, timedelta
import pytz # For timezone handling
import random # For choosing random default reply
import json # For loading custom deadlines and replied log
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from generate_report_reply import ReportResponder # Import the new class
import re # For parsing company overview
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
COMPANY_OVERVIEW_PATH = ".clinerules/companyoverview.md"
REPORT_LOG_PATH = "jobs/report_log.csv"
REPORT_STORAGE_DIR = "reports" # Base directory for storing reports
CUSTOM_DEADLINES_PATH = "jobs/reporter_custom_deadlines.json" # Path to custom deadlines
REPLIED_LOG_PATH = "jobs/replied_log.json" # Path to replied log
KYIV_TIMEZONE = pytz.timezone("Europe/Kiev")
REMINDER_MESSAGE = "когда отправишь викли отчет?"
DEFAULT_REPLIES = [
    "спасибо за отчет", "спасибо, принял", "дякую за звіт", "дякую, прийняв",
    "отчет получил, спасибо", "звіт отримав, дякую", "ок, спасибо", "добре, дякую",
    "принято, спасибо", "прийнято, дякую", "отлично, спасибо", "чудово, дякую",
    "все ок, спасибо", "many thanks"
]

# --- Helper Functions ---

def parse_company_overview(file_path):
    reporters = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            in_section = False
            for line in f:
                line = line.strip()
                if line.startswith("### Weekly Reporting Structure"):
                    in_section = True
                    continue
                if in_section:
                    if line.startswith("###"): break
                    if line.startswith("- **"):
                        match = re.match(r"- \*\*(.+?)\*\*.*?\(Slack User ID: (U[A-Z0-9]+), IM ID: (D[A-Z0-9]+)\)", line)
                        if match:
                            name, user_id, im_id = match.groups()
                            reporters.append({"name": name.strip(), "user_id": user_id, "im_id": im_id})
                        else:
                             print(f"Warning: Could not parse line: {line}")
    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
    except Exception as e:
        print(f"Error reading/parsing {file_path}: {e}")
    return reporters

def load_custom_deadlines(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Error parsing {file_path}. Using default deadlines.")
        return {}
    return {}

def load_replied_log(file_path, report_date_str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_log = json.load(f)
            return set(full_log.get(report_date_str, []))
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        print(f"Warning: Error parsing {file_path}. Starting fresh for today.")
        return set()

def update_replied_log(file_path, report_date_str, user_id):
    full_log = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass # Will create new or overwrite if invalid

    replied_today_list = list(full_log.get(report_date_str, []))
    if user_id not in replied_today_list:
        replied_today_list.append(user_id)
    full_log[report_date_str] = replied_today_list

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_log, f, indent=4)
    except IOError as e:
        print(f"Error writing to {file_path}: {e}")


def get_monday_date_details(target_date_dt):
    if target_date_dt.tzinfo is None:
        target_date_dt = KYIV_TIMEZONE.localize(target_date_dt)
    else:
        target_date_dt = target_date_dt.astimezone(KYIV_TIMEZONE)
    monday_dt = target_date_dt - timedelta(days=target_date_dt.weekday())
    start_of_monday_kyiv = KYIV_TIMEZONE.localize(datetime.combine(monday_dt.date(), time(0, 0, 0)))
    end_of_monday_kyiv = KYIV_TIMEZONE.localize(datetime.combine(monday_dt.date(), time(23, 59, 59)))
    report_date_str = monday_dt.strftime('%Y-%m-%d')
    print(f"Checking reports for Monday: {report_date_str}")
    print(f"Time window (Kyiv): {start_of_monday_kyiv.strftime('%H:%M:%S')} to {end_of_monday_kyiv.strftime('%H:%M:%S')}")
    return start_of_monday_kyiv, end_of_monday_kyiv, report_date_str

def fetch_reporter_messages(client, im_channel_id, reporter_user_id, start_ts, end_ts):
    reporter_messages = []
    try:
        cursor = None
        while True:
            response = client.conversations_history(
                channel=im_channel_id, oldest=str(start_ts), latest=str(end_ts),
                limit=200, cursor=cursor
            )
            if not response.get("ok"): break
            messages = response.get("messages", [])
            for msg in messages:
                if not msg.get("bot_id") and msg.get("user") == reporter_user_id:
                    reporter_messages.append(msg)
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor: break
    except SlackApiError as e:
        print(f"Slack API error for {im_channel_id}: {e.response['error']}")
    reporter_messages.sort(key=lambda x: float(x.get('ts', 0)))
    return reporter_messages

def log_report_status(log_file, report_date, reporter_name, user_id, status, first_submission_ts=None):
    file_exists = os.path.isfile(log_file)
    try:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Reporter Name', 'User ID', 'Status', 'First Message Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists: writer.writeheader()
            writer.writerow({
                'Date': report_date, 'Reporter Name': reporter_name, 'User ID': user_id,
                'Status': status,
                'First Message Timestamp': datetime.fromtimestamp(float(first_submission_ts), tz=KYIV_TIMEZONE).isoformat() if first_submission_ts else ''
            })
    except IOError as e:
        print(f"Error writing to log {log_file}: {e}")

def save_report_messages(storage_dir, report_date, reporter_name, messages):
    reporter_filename = f"{reporter_name.replace(' ', '_')}.md"
    report_dir = os.path.join(storage_dir, report_date)
    os.makedirs(report_dir, exist_ok=True)
    file_path = os.path.join(report_dir, reporter_filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Report: {reporter_name} - {report_date}\n\n")
            if not messages: f.write("No messages.\n")
            else:
                for msg in messages:
                    ts = float(msg.get('ts', 0))
                    r_time = datetime.fromtimestamp(ts, tz=KYIV_TIMEZONE).strftime('%H:%M:%S')
                    f.write(f"## [{r_time}]\n{msg.get('text', '[No text]')}\n\n")
    except IOError as e:
        print(f"Error saving report for {reporter_name}: {e}")

def send_slack_message(client, channel_id, text, thread_ts=None, reply_broadcast=False):
    try:
        payload = {"channel": channel_id, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
            if reply_broadcast:
                payload["reply_broadcast"] = True
        
        response = client.chat_postMessage(**payload)
        if response.get("ok"):
            print("Message sent successfully.")
            return True
        print(f"Error sending message to {channel_id}: {response.get('error')}")
    except SlackApiError as e:
        print(f"Slack API error sending message to {channel_id}: {e.response['error']}")
    return False

# --- Main Logic ---

def determine_report_status(messages, deadline_ts):
    if not messages:
        return "missing", None
    first_ts = float(messages[0].get('ts', 0))
    #print(f"First message timestamp: {first_ts}, Deadline timestamp: {deadline_ts}")
    status = "on_time" if first_ts < deadline_ts else "late"
    return status, first_ts

def say(client, reporters, message):
    for reporter in reporters:
        send_slack_message(client, reporter["im_id"], message)

def check():
    answer = input("Send reminder to missing reporters? (y/n): ").lower()
    if answer == "y":
        return "yes"
    elif answer == "n":
        return "no"
    else:
        print("Input not recognized. Exiting.")
        return None

def handle_missing_reports(client, missing_reporters):
    if not missing_reporters:
        return
    print("\n--- Handle Missing Reports ---")
    result = check()
    if result == "yes":
        say(client, missing_reporters, REMINDER_MESSAGE)
    # If "no" or None, just end the function

def handle_single_report_reply(client, reporter, status_type, all_messages, llm_responder, replied_user_ids, report_date_str, reply_to_names_list, reply_to_ids_list):
    # Skip if already replied and not specifically requested
    if reporter['user_id'] in replied_user_ids and \
       not (reporter['name'].lower() in reply_to_names_list or reporter['user_id'] in reply_to_ids_list):
        return False, False  # (reply_sent, exit_requested)

    print(f"\nMessages from {reporter['name']} ({status_type.replace('_', ' ')}):")
    current_messages = all_messages.get(reporter['user_id'], [])
    if not current_messages:
        print("[No messages found]")
        return False, False

    for msg in current_messages:
        ts = float(msg.get('ts', 0))
        print(f"- [{datetime.fromtimestamp(ts, tz=KYIV_TIMEZONE).strftime('%H:%M:%S')}] {msg.get('text', '[No text]')}")

    while True:  # Loop for current reporter's action
        prompt = f"Reply to {reporter['name']}? (d=default, a=AI suggest, c=custom, s=skip, exit=all): "
        action = input(prompt).lower()

        if action == 'd':
            reply_text = f"<@{reporter['user_id']}>, {random.choice(DEFAULT_REPLIES)}"
            if send_slack_message(client, reporter["im_id"], reply_text):
                update_replied_log(REPLIED_LOG_PATH, report_date_str, reporter['user_id'])
                return True, False
            break
        elif action == 'c':
            custom_reply = input("Enter custom reply: ")
            if custom_reply:
                if send_slack_message(client, reporter["im_id"], custom_reply):
                    update_replied_log(REPLIED_LOG_PATH, report_date_str, reporter['user_id'])
                    return True, False
            else:
                print("Empty reply, skipping.")
            break
        elif action == 'a':
            ai_sent = handle_ai_reply(client, reporter, current_messages, llm_responder, report_date_str)
            if ai_sent:
                return True, False  # If reply sent in AI, go to next responder
            # If not sent, re-prompt for this reporter
            continue
        elif action == 's':
            print("Skipping reply for this reporter.")
            break
        elif action == 'exit':
            print("Exiting all reply loops.")
            return False, True
        else:
            print("Invalid input.")

    return False, False

def handle_ai_reply(client, reporter, current_messages, llm_responder, report_date_str):
    if not llm_responder:
        print("LLM Responder not available.")
        return False
    report_text_for_llm = "\n\n".join([m.get('text', '[No text]') for m in current_messages])
    print("Generating LLM reply...")
    suggested_reply = llm_responder.generate_reply(report_text_for_llm)
    suggested_reply = f"<@{reporter['user_id']}>, {suggested_reply}"
    print(f"\n--- Suggested LLM Reply ---\n{suggested_reply}\n---------------------------\n")
    while True:
        sub_action = input("Send (y), edit (e), or back (b) to main menu: ").lower()
        if sub_action == 'y':
            if send_slack_message(client, reporter["im_id"], suggested_reply):
                update_replied_log(REPLIED_LOG_PATH, report_date_str, reporter['user_id'])
                print("Reply sent.")
                return True
            break
        elif sub_action == 'e':
            edited_reply = input(f"Edit suggestion (Enter to use as-is):\n{suggested_reply}\nYour edit: ")
            final_reply = edited_reply if edited_reply.strip() else suggested_reply
            if send_slack_message(client, reporter["im_id"], final_reply):
                update_replied_log(REPLIED_LOG_PATH, report_date_str, reporter['user_id'])
                print("Reply sent.")
                return True
            break
        elif sub_action == 'b':
            break
        else:
            print("Invalid input.")
    return False

def handle_report_replies(client, reporters, all_messages, llm_responder, replied_user_ids, report_date_str, reply_to_names_list, reply_to_ids_list):
    exit_all_loops = False
    for status_type, reporters_to_reply in reporters.items():
        if exit_all_loops:
            break
        print(f"\n--- Handle {status_type.replace('_', ' ').title()} Reports for Replies ---")
        for reporter in reporters_to_reply:
            if exit_all_loops:
                break
            reply_sent, exit_requested = handle_single_report_reply(
                client, reporter, status_type, all_messages, llm_responder,
                replied_user_ids, report_date_str, reply_to_names_list, reply_to_ids_list
            )
            if exit_requested:
                exit_all_loops = True
                break

    print("\nWeekly report check complete.")


# --- Main Logic ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="Check Slack weekly reports.")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--reply-to-names", type=str, help="Comma-separated names to reply to.")
    parser.add_argument("--reply-to-ids", type=str, help="Comma-separated Slack User IDs to reply to.")
    return parser.parse_args()

def initialize_slack_client():
    slack_token = os.environ.get("SLACK_USER_TOKEN")
    if not slack_token:
        print("Error: SLACK_USER_TOKEN not set.")
        return None
    return WebClient(token=slack_token)
def load_llm_responder(style_guide_path="jobs/serhii_ceo_reply_style.md"):
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Warning: OPENROUTER_API_KEY not set. 'a' option disabled.")
        return None
    try:
        if not os.path.isfile(style_guide_path):
            print(f"Warning: {style_guide_path} not found.")
            return None
        with open(style_guide_path, "r", encoding="utf-8") as f:
            style_guide_content = f.read()
        return ReportResponder(api_key=openrouter_api_key, style_guide_text=style_guide_content)
    except FileNotFoundError:
        print(f"Warning: {style_guide_path} not found.")
        return None
    except ValueError as ve:
        print(f"Error initializing LLM: {ve}")


def process_reporters(client, reporters, start_ts, end_ts, deadlines, report_date_str):
    results = {"on_time": [], "late": [], "missing": []}
    all_reporter_messages = {}

    for reporter in reporters:
        user_id = reporter["user_id"]
        deadline_time = deadlines.get(user_id, time(13, 0, 0))
        if isinstance(deadline_time, str):
            try:
                h, m = map(int, deadline_time.split(':'))
                deadline_time = time(h, m, 0)
            except ValueError:
                print(f"Invalid deadline format for user {user_id}. Using default time 13:00:00.")
                deadline_time = time(13, 0, 0)

        # Determine the deadline timestamp based on start_ts date
        start_date = datetime.fromtimestamp(start_ts, tz=KYIV_TIMEZONE).date()
        deadline_dt = KYIV_TIMEZONE.localize(datetime.combine(start_date, deadline_time))
        deadline_ts = deadline_dt.timestamp()

        messages = fetch_reporter_messages(client, reporter["im_id"], user_id, start_ts, end_ts)
        all_reporter_messages[user_id] = messages

        status, first_ts = determine_report_status(messages, deadline_ts)
        results[status].append(reporter)

        log_report_status(REPORT_LOG_PATH, report_date_str, reporter["name"], user_id, status, first_ts)
        if status != "missing":
            save_report_messages(REPORT_STORAGE_DIR, report_date_str, reporter["name"], messages)

    return results, all_reporter_messages

def print_report_summary(results, all_reporter_messages, report_date_str):
    """Prints a formatted summary of report statuses, including first message time for late reports."""
    print("\n--- Weekly Report Summary ---")
    print(f"Date Checked: {report_date_str}")

    print(f"\nOn Time ({len(results['on_time'])}):")
    for r in results["on_time"]:
        print(f"- {r['name']}")

    print(f"\nLate ({len(results['late'])}):")
    for r in results["late"]:
        user_id = r["user_id"]
        messages = all_reporter_messages.get(user_id, [])
        first_ts = None
        if messages:
            first_ts = float(messages[0].get('ts', 0))
            readable_time = datetime.fromtimestamp(first_ts, tz=KYIV_TIMEZONE).strftime('%H:%M:%S')
            print(f"- {r['name']} (First Submission: {readable_time})")
        else:
            # This case should ideally not happen if status is 'late', but included for robustness
            print(f"- {r['name']} (No messages found)") 

    print(f"\nMissing ({len(results['missing'])}):")
    for r in results["missing"]:
        print(f"- {r['name']}")
    print("----------------------------")


def main():
    args = parse_arguments()

    # Initialize these lists early, even if args are None
    reply_to_names_list = [name.strip().lower() for name in args.reply_to_names.split(',')] if args.reply_to_names else []
    reply_to_ids_list = [id.strip() for id in args.reply_to_ids.split(',')] if args.reply_to_ids else []

    client = initialize_slack_client()
    if not client:
        return

    target_date_dt = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now(KYIV_TIMEZONE)
    start_of_monday_kyiv, end_of_monday_kyiv, report_date_str = get_monday_date_details(target_date_dt)
    start_ts, end_ts = start_of_monday_kyiv.timestamp(), end_of_monday_kyiv.timestamp()

    reporters = parse_company_overview(COMPANY_OVERVIEW_PATH)
    if not reporters:
        print("Error: No reporters found.")
        return

    deadlines = load_custom_deadlines(CUSTOM_DEADLINES_PATH)
    replied_user_ids = load_replied_log(REPLIED_LOG_PATH, report_date_str)
    llm_responder = load_llm_responder()

    results, all_messages = process_reporters(client, reporters, start_ts, end_ts, deadlines, report_date_str)

    # Print the summary before interactive replies
    print_report_summary(results, all_messages, report_date_str)

    handle_missing_reports(client, results["missing"])
    
    # Filter reporters for interactive replies based on args and replied log
    interactive_reporters_categories = {}
    all_repliable_reporters = results["late"] + results["on_time"] # Order: Late first, then On Time

    if reply_to_names_list or reply_to_ids_list: # Use the created lists
        # Filter by provided names/ids, but still respect replied_user_ids unless explicitly listed
        filtered_reporters = []
        for r in all_repliable_reporters:
            is_explicitly_requested = r['name'].lower() in reply_to_names_list or r['user_id'] in reply_to_ids_list
            if r['user_id'] in replied_user_ids and not is_explicitly_requested:
                continue # Skip if already replied and not explicitly asked for
            if is_explicitly_requested:
                filtered_reporters.append(r)
        # Re-categorize filtered reporters into 'late'/'on_time' for the handler
        interactive_reporters_categories['late'] = [r for r in filtered_reporters if r in results['late']]
        interactive_reporters_categories['on_time'] = [r for r in filtered_reporters if r in results['on_time']]

    else: # Default: offer replies for Late, then On Time, skipping already replied
        interactive_reporters_categories['late'] = [r for r in results['late'] if r['user_id'] not in replied_user_ids]
        interactive_reporters_categories['on_time'] = [r for r in results['on_time'] if r['user_id'] not in replied_user_ids]

    # Remove empty categories
    interactive_reporters_categories = {k: v for k, v in interactive_reporters_categories.items() if v}

    handle_report_replies(client, interactive_reporters_categories, all_messages, llm_responder, replied_user_ids, report_date_str, reply_to_names_list, reply_to_ids_list) # Pass the created lists


if __name__ == "__main__":
    try:
        import pytz
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
        # langdetect is used by generate_report_reply, ensure it's available if that module is used.
    except ImportError:
        print("Error: Required libraries (pytz, slack_sdk) not found.")
        print("Please install them: pip install pytz slack_sdk langdetect")
        exit(1)
    main()