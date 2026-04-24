import os
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta # Added timedelta
from thefuzz import fuzz # Import for fuzzy matching

# --- Slack API Functions ---

def get_dm_conversations(client):
    """
    Fetches a list of users with whom the authenticated user has Direct Messages.
    """
    users_info = []
    try:
        print("Fetching DM conversations...")
        result = client.conversations_list(types="im", limit=200)
        if not result.get("ok"):
            print(f"Error fetching conversations_list: {result.get('error')}")
            return users_info

        for channel in result.get("channels", []):
            user_id = channel.get("user")
            if user_id:
                try:
                    user_profile_result = client.users_info(user=user_id)
                    if user_profile_result.get("ok"):
                        user_obj = user_profile_result.get("user", {})
                        profile = user_obj.get("profile", {})
                        im_channel_id = channel.get("id") # Get the IM conversation ID
                        
                        user_details = {
                            "id": user_id,
                            "im_channel_id": im_channel_id, # Store the IM conversation ID
                            "name": user_obj.get("real_name") or user_obj.get("name", "Unknown User"),
                            "display_name": profile.get("display_name_normalized") or profile.get("display_name"),
                            "email": profile.get("email"),
                            "phone": profile.get("phone"),
                            "title": profile.get("title"),
                            "status_text": profile.get("status_text"),
                            "status_emoji": profile.get("status_emoji"),
                            "first_name": profile.get("first_name"),
                            "last_name": profile.get("last_name"),
                            "is_bot": user_obj.get("is_bot", False),
                            "is_app_user": user_obj.get("is_app_user", False),
                            "deleted": user_obj.get("deleted", False) # Check for deactivation
                        }
                        users_info.append(user_details)
                    else:
                        print(f"Error fetching user info for {user_id}: {user_profile_result.get('error')}")
                        users_info.append({"id": user_id, "im_channel_id": channel.get("id"), "name": f"Unknown User ({user_id})", "email": None, "phone": None, "title": None, "deleted": False}) # Basic info on error
                except SlackApiError as e_user:
                    print(f"Slack API error fetching user info for {user_id}: {e_user.response['error']}")
                    users_info.append({"id": user_id, "im_channel_id": channel.get("id"), "name": f"Unknown User ({user_id}) - API Error", "email": None, "phone": None, "title": None, "deleted": False})
        print(f"Found {len(users_info)} DM conversations.")
    except SlackApiError as e:
        print(f"Slack API error fetching DM conversations: {e.response['error']}")
    return users_info

def get_channel_messages(client, channel_id, channel_name="Channel", limit_per_channel=50, history_days=None, filter_user_id=None):
    """
    Fetches messages from a specific channel.
    If history_days is provided, it fetches messages from that many days ago until now.
    Otherwise, it fetches the last 'limit_per_channel' messages.
    If filter_user_id is provided, only messages from that user are returned.
    """
    messages_data = []
    print(f"Fetching messages from {channel_name} ({channel_id})...")
    if filter_user_id:
        print(f"Filtering for messages from user ID: {filter_user_id}")
    
    oldest_ts = None
    if history_days is not None:
        # Ensure timedelta is available
        from datetime import timedelta 
        oldest_ts = (datetime.now() - timedelta(days=history_days)).timestamp()
        print(f"Fetching history from the last {history_days} days (oldest: {datetime.fromtimestamp(oldest_ts).isoformat()}).")

    try:
        cursor = None
        fetched_count = 0
        
        while True:
            current_api_call_limit = 200 
            if limit_per_channel is not None and history_days is None: 
                remaining_to_fetch = limit_per_channel - fetched_count
                if remaining_to_fetch <= 0: break
                current_api_call_limit = min(current_api_call_limit, remaining_to_fetch)

            result = client.conversations_history(
                channel=channel_id, 
                limit=current_api_call_limit,
                oldest=str(oldest_ts) if oldest_ts else None,
                cursor=cursor
            )
            if not result.get("ok"):
                print(f"Error fetching history for channel {channel_id}: {result.get('error')}")
                break
            
            page_messages = result.get("messages", [])
            if not page_messages: 
                break

            for message in page_messages:
                user_id = message.get("user", "N/A")
                # Apply user filter if specified
                if filter_user_id and user_id != filter_user_id:
                    continue
                text = message.get("text", "")
                ts = message.get("ts", "0")
                # Convert timestamp to human-readable format
                try:
                    dt_object = datetime.fromtimestamp(float(ts))
                    readable_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    readable_time = "Invalid Timestamp"

                messages_data.append({
                    "user": user_id, 
                    "text": text,
                    "time": readable_time,
                    "channel_id": channel_id,
                    "channel_name": channel_name
                })
                fetched_count += 1
                if limit_per_channel is not None and history_days is None and fetched_count >= limit_per_channel:
                    break 
            
            if limit_per_channel is not None and history_days is None and fetched_count >= limit_per_channel:
                break 

            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor: 
                break
            # No need for the redundant break check here, already handled by the loop condition or inner break

        print(f"Processed {fetched_count} messages, kept {len(messages_data)} after filtering for {channel_name}.")
    except SlackApiError as e:
        print(f"Slack API error fetching messages for channel {channel_id} ({channel_name}): {e.response['error']}")
    return messages_data

def get_all_team_messages(client, limit_per_channel=50, history_days=None, filter_user_id=None):
    """
    Fetches messages from all public and private channels the user is a member of.
    """
    all_messages = []
    conversation_types = "public_channel,private_channel" # As per user clarification
    
    try:
        print(f"Fetching list of channels (types: {conversation_types})...")
        result = client.users_conversations(types=conversation_types, limit=200, exclude_archived=True)
        if not result.get("ok"):
            print(f"Error fetching users_conversations: {result.get('error')}")
            return all_messages

        channels = result.get("channels", [])
        print(f"Found {len(channels)} channels to process.")

        for channel in channels:
            channel_id = channel.get("id")
            channel_name = channel.get("name", f"Channel {channel_id}")
            if channel.get("is_member") or channel.get("is_im") is False: # Ensure user is member for non-DMs
                 messages_from_channel = get_channel_messages(
                     client, 
                     channel_id, 
                     channel_name, 
                     limit_per_channel=limit_per_channel,
                     history_days=history_days,
                     filter_user_id=filter_user_id # Pass filter_user_id
                 )
                 all_messages.extend(messages_from_channel)
            else:
                print(f"Skipping channel {channel_name} ({channel_id}) as user is not a member (or it's a DM being handled separately).")

    except SlackApiError as e:
        print(f"Slack API error fetching team messages: {e.response['error']}")
    
    print(f"Fetched a total of {len(all_messages)} messages from team channels.")
    return all_messages

def get_channel_id_by_name(client, channel_name_to_find):
    """
    Finds a channel ID given its name. Searches public channels, private channels, and DMs.
    If channel_name_to_find looks like an ID, it's returned directly.
    """
    # Check if the input looks like a direct Slack ID
    if isinstance(channel_name_to_find, str) and \
       len(channel_name_to_find) >= 9 and \
       channel_name_to_find[0] in ('C', 'G', 'D') and \
       channel_name_to_find[1:].isalnum(): # Basic check for typical ID format
        print(f"Input '{channel_name_to_find}' appears to be a direct Slack ID. Using it directly.")
        return channel_name_to_find

    print(f"Searching for channel/DM ID for '{channel_name_to_find}' (with fuzzy matching)...")
    best_match_channel_info = None
    highest_similarity = 0
    similarity_threshold = 80  # Minimum similarity score

    try:
        # 1. Search public and private channels
        print("Searching public/private channels...")
        channel_types = "public_channel,private_channel"
        cursor = None
        all_channels_fetched = []
        while True:
            result = client.users_conversations(
                types=channel_types, limit=200, exclude_archived=True, cursor=cursor
            )
            if not result.get("ok"):
                print(f"Error fetching users_conversations (public/private): {result.get('error')}")
                break 
            page_channels = result.get("channels", [])
            all_channels_fetched.extend(page_channels)
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        print(f"Fetched {len(all_channels_fetched)} public/private channels.")
        for channel in all_channels_fetched:
            name_to_check = channel.get("name")
            if name_to_check:
                similarity = fuzz.token_set_ratio(channel_name_to_find.lower(), name_to_check.lower())
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match_channel_info = {"id": channel.get("id"), "name": name_to_check, "type": "channel"}

        # 2. If no good match yet, search DMs by user name
        if not best_match_channel_info or highest_similarity < similarity_threshold:
            print(f"No strong match in public/private channels (highest sim: {highest_similarity}%). Searching DMs...")
            dm_users = get_dm_conversations(client) # This already fetches user details including names
            print(f"Fetched {len(dm_users)} DM contacts to search through.")
            for user in dm_users:
                # Check real_name, display_name, and slack 'name' field
                names_to_check = [
                    user.get("name"), # This is often real_name from get_dm_conversations
                    user.get("display_name")
                ]
                # The 'name' field from users.info (Slack's username) might also be relevant
                # but get_dm_conversations already prioritizes real_name.
                
                for name_val in names_to_check:
                    if name_val:
                        similarity = fuzz.token_set_ratio(channel_name_to_find.lower(), name_val.lower())
                        if similarity > highest_similarity:
                            highest_similarity = similarity
                            # For DMs, the 'channel_id' is the DM conversation ID, which is usually the user's ID prefixed with 'D'
                            # However, conversations_list(types="im") returns the actual DM channel ID.
                            # We need to find the DM channel ID associated with this user.
                            im_list_result = client.conversations_list(types="im", limit=500) # Potentially many DMs
                            dm_channel_id = None
                            if im_list_result.get("ok"):
                                for im_channel in im_list_result.get("channels", []):
                                    if im_channel.get("user") == user.get("id"):
                                        dm_channel_id = im_channel.get("id")
                                        break
                            if dm_channel_id:
                                best_match_channel_info = {"id": dm_channel_id, "name": name_val, "type": "dm"}
                            else:
                                print(f"Could not find DM channel ID for user {name_val} ({user.get('id')})")
        
        if best_match_channel_info and highest_similarity >= similarity_threshold:
            print(f"Found best match: '{best_match_channel_info['name']}' (ID: {best_match_channel_info['id']}, Type: {best_match_channel_info['type']}) with similarity {highest_similarity}%.")
            return best_match_channel_info["id"]
        elif best_match_channel_info:
            print(f"Closest match: '{best_match_channel_info['name']}' (Similarity: {highest_similarity}%) is below threshold {similarity_threshold}%.")
        else:
            print(f"No channel or DM found matching '{channel_name_to_find}'.")
        return None

    except SlackApiError as e:
        print(f"Slack API error during channel/DM ID lookup: {e.response['error']}")
        return None

def list_channels_by_type(client, channel_type):
    """
    Lists channels of a specific type (e.g., "public_channel", "private_channel")
    that the user is a member of.
    """
    print(f"Fetching list of {channel_type}s...")
    channels_info = []
    try:
        cursor = None
        while True:
            result = client.users_conversations(
                types=channel_type,
                limit=200,
                exclude_archived=True,
                cursor=cursor
            )
            if not result.get("ok"):
                print(f"Error fetching {channel_type} list: {result.get('error')}")
                break 
            
            for channel in result.get("channels", []):
                channels_info.append({
                    "id": channel.get("id"),
                    "name": channel.get("name", f"Unnamed {channel_type}")
                })
            
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        print(f"Found {len(channels_info)} {channel_type}s.")
    except SlackApiError as e:
        print(f"Slack API error fetching {channel_type} list: {e.response['error']}")
    return channels_info

def send_slack_message(client, channel_id, text, thread_ts=None):
    """
    Sends a message to a specified channel_id.
    Can reply in a thread if thread_ts is provided.
    """
    try:
        print(f"Sending message to channel {channel_id}..." + (f" in thread {thread_ts}" if thread_ts else ""))
        response = client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts,
            as_user=True # Explicitly send as the authenticated user
        )
        if response.get("ok"):
            print("Message sent successfully.")
            return response.get("ts") # Return the timestamp of the sent message
        else:
            print(f"Error sending message: {response.get('error')}")
            return None
    except SlackApiError as e:
        print(f"Slack API error sending message: {e.response['error']}")
        return None

def get_conversation_context(client, channel_id, channel_name="Channel", message_limit=20):
    """
    Fetches messages from a channel/DM, including threaded replies.
    If message_limit is None, fetches all messages (handles pagination).
    Otherwise, fetches the last 'message_limit' messages.
    """
    if message_limit is None:
        print(f"Fetching ALL conversation context for {channel_name} ({channel_id})...")
    else:
        print(f"Fetching conversation context for {channel_name} ({channel_id}), limit {message_limit} messages...")
    
    conversation_data = []
    user_cache = {} 

    def get_user_name(user_id_str): # Renamed param for clarity
        if not user_id_str or user_id_str == "N/A":
            return "Unknown User"
        if user_id_str in user_cache:
            return user_cache[user_id_str]
        try:
            user_info_result = client.users_info(user=user_id_str)
            if user_info_result.get("ok"):
                user_obj = user_info_result.get("user", {})
                name = user_obj.get("real_name") or user_obj.get("name", user_id_str)
                user_cache[user_id_str] = name
                return name
            else:
                print(f"Error fetching user info for {user_id_str}: {user_info_result.get('error')}")
                user_cache[user_id_str] = user_id_str 
                return user_id_str
        except SlackApiError as e_user_info: # Renamed exception var
            print(f"Slack API error fetching user info for {user_id_str}: {e_user_info.response['error']}")
            user_cache[user_id_str] = user_id_str 
            return user_id_str

    all_parent_messages = []
    try:
        cursor = None
        while True:
            history_result = client.conversations_history(
                channel=channel_id, 
                limit=200 if message_limit is None else message_limit, # Fetch in chunks if all, else fetch requested limit
                cursor=cursor
            )
            if not history_result.get("ok"):
                print(f"Error fetching history for {channel_id}: {history_result.get('error')}")
                return conversation_data # Return what we have so far, or empty

            page_messages = history_result.get("messages", [])
            all_parent_messages.extend(page_messages)
            
            if message_limit is not None and len(all_parent_messages) >= message_limit:
                all_parent_messages = all_parent_messages[:message_limit] # Trim if we fetched more than limit
                break 
            
            cursor = history_result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break # No more pages
        
        print(f"Fetched a total of {len(all_parent_messages)} parent messages.")

        # Process messages (older first for chronological display, but Slack API returns newest first)
        # If fetching all, we want oldest first. If fetching a limit, we want newest first from that limited set.
        # The API returns newest first. So if we fetch a limit, we just reverse that.
        # If we fetch all, we reverse the entire accumulated list.
        
        # The current logic fetches newest first, then reverses. This is good for display.
        # For fetching all, we'd accumulate then reverse the whole list.
        # The current `reversed(parent_messages)` will work correctly if `parent_messages` is the final list.
        
        # Let's adjust: if message_limit is None (fetch all), we reverse at the end.
        # If message_limit is set, we take the first 'limit' (newest) and then reverse those for display.
        # The current code already fetches newest first, and `reversed()` makes them oldest first for processing.

        for parent_msg in reversed(all_parent_messages): 
            ts = parent_msg.get("ts", "0")
            try:
                dt_object = datetime.fromtimestamp(float(ts))
                readable_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                readable_time = "Invalid Timestamp"

            user_id = parent_msg.get("user")
            user_name_str = get_user_name(user_id)

            msg_details = {
                "user_id": user_id,
                "user_name": user_name_str,
                "text": parent_msg.get("text", ""),
                "time": readable_time,
                "ts": ts, # Original timestamp for threading
                "channel_id": channel_id,
                "channel_name": channel_name,
                "reply_count": parent_msg.get("reply_count", 0),
                "thread_ts": parent_msg.get("thread_ts", ts), # thread_ts is ts for parent messages
                "replies": []
            }

            # Fetch threaded replies if they exist
            if msg_details["reply_count"] > 0 and parent_msg.get("ts"): # Ensure 'ts' exists for thread_ts
                print(f"Fetching replies for message {parent_msg.get('ts')}...")
                try:
                    replies_result = client.conversations_replies(
                        channel=channel_id,
                        ts=parent_msg.get("ts") # Use parent message's 'ts' as 'thread_ts' for replies API
                    )
                    if replies_result.get("ok"):
                        # The first message in replies_result.messages is the parent itself, skip it.
                        for reply_msg_data in replies_result.get("messages", [])[1:]:
                            reply_ts = reply_msg_data.get("ts", "0")
                            try:
                                reply_dt_object = datetime.fromtimestamp(float(reply_ts))
                                reply_readable_time = reply_dt_object.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                reply_readable_time = "Invalid Timestamp"
                            
                            reply_user_id = reply_msg_data.get("user")
                            reply_user_name_str = get_user_name(reply_user_id)

                            msg_details["replies"].append({
                                "user_id": reply_user_id,
                                "user_name": reply_user_name_str,
                                "text": reply_msg_data.get("text", ""),
                                "time": reply_readable_time,
                                "ts": reply_ts
                            })
                        print(f"Fetched {len(msg_details['replies'])} replies for message {parent_msg.get('ts')}.")
                    else:
                        print(f"Error fetching replies for message {parent_msg.get('ts')}: {replies_result.get('error')}")
                except SlackApiError as e_reply:
                    print(f"Slack API error fetching replies for message {parent_msg.get('ts')}: {e_reply.response['error']}")
            
            conversation_data.append(msg_details)
        
        print(f"Processed {len(conversation_data)} messages with their threads.")

    except SlackApiError as e:
        print(f"Slack API error fetching conversation context for {channel_id}: {e.response['error']}")
    
    return conversation_data
