# --- Output Functions ---

def format_dms_for_output(dm_users):
    output_lines = ["# Direct Message Contacts (Detailed)\n"]
    if not dm_users:
        output_lines.append("No direct message contacts found.")
    else:
        active_users = [u for u in dm_users if not u.get('deleted')]
        deactivated_users = [u for u in dm_users if u.get('deleted')]

        # Sort each group by name, case-insensitive
        sorted_active_users = sorted(active_users, key=lambda x: (x.get('name') or '').lower())
        sorted_deactivated_users = sorted(deactivated_users, key=lambda x: (x.get('name') or '').lower())

        if sorted_active_users:
            output_lines.append("\n### Active Contacts\n")
            for user in sorted_active_users:
                user_name = user.get('name', 'N/A')
                user_id_str = user.get('id', 'N/A')
                im_channel_id_str = user.get('im_channel_id', 'N/A')
                output_lines.append(f"\n#### {user_name} (User ID: {user_id_str}, IM ID: {im_channel_id_str})")

                if user.get('is_bot'):
                    output_lines.append(f"  Type: Bot")
                if user.get('is_app_user'):
                    output_lines.append(f"  Type: App User")

                details_to_show = {
                    "Display Name": user.get('display_name'),
                    "Email": user.get('email'),
                    "Phone": user.get('phone'),
                    "Title": user.get('title'),
                    "Status": f"{user.get('status_emoji', '')} {user.get('status_text', '')}".strip()
                }
                has_details = False
                for key, value in details_to_show.items():
                    if value and value.strip() != "": 
                        output_lines.append(f"  {key}: {value}")
                        has_details = True
                if not has_details and not user.get('is_bot') and not user.get('is_app_user'):
                    output_lines.append("  (No additional profile details available or retrieved)")
        
        if sorted_deactivated_users:
            output_lines.append("\n### Deactivated Contacts\n")
            for user in sorted_deactivated_users:
                user_name = user.get('name', 'N/A')
                user_id_str = user.get('id', 'N/A')
                im_channel_id_str = user.get('im_channel_id', 'N/A')
                output_lines.append(f"\n#### {user_name} (User ID: {user_id_str}, IM ID: {im_channel_id_str}) - DEACTIVATED")
                # Optionally show minimal info for deactivated, e.g., type if bot/app
                if user.get('is_bot'):
                    output_lines.append(f"  Type: Bot")
                if user.get('is_app_user'):
                    output_lines.append(f"  Type: App User")
    return "\n".join(output_lines)

def format_public_channels_for_output(public_channels_list):
    output_lines = ["# Public Channels\n"]
    if not public_channels_list:
        output_lines.append("No public channels found or user is not a member of any.")
    else:
        # Sort by name, case-insensitive
        sorted_channels = sorted(public_channels_list, key=lambda x: x['name'].lower() if x['name'] else '')
        for channel in sorted_channels:
            output_lines.append(f"- {channel['name']} (ID: {channel['id']})")
    return "\n".join(output_lines)

def format_private_channels_for_output(private_channels_list):
    output_lines = ["# Private Channels\n"]
    if not private_channels_list:
        output_lines.append("No private channels found or user is not a member of any.")
    else:
        # Sort by name, case-insensitive
        sorted_channels = sorted(private_channels_list, key=lambda x: x['name'].lower() if x['name'] else '')
        for channel in sorted_channels:
            output_lines.append(f"- {channel['name']} (ID: {channel['id']})")
    return "\n".join(output_lines)

def format_messages_for_output(messages_data):
    output_lines = ["# Team Messages\n"]
    if not messages_data:
        output_lines.append("No messages found.")
        
    # Group messages by channel
    messages_by_channel = {}
    for msg in messages_data:
        channel_key = f"{msg['channel_name']} (ID: {msg['channel_id']})"
        if channel_key not in messages_by_channel:
            messages_by_channel[channel_key] = []
        messages_by_channel[channel_key].append(msg)
        
    for channel_key, msgs_in_channel in messages_by_channel.items():
        output_lines.append(f"\n## Messages from {channel_key}\n")
        for msg in sorted(msgs_in_channel, key=lambda x: x['time']): # Sort by time
            output_lines.append(f"**User {msg['user']} at {msg['time']}**: {msg['text']}")
    return "\n".join(output_lines)

def format_conversation_context_for_display(conversation_data, channel_name="Conversation"):
    output_lines = [f"# Conversation Context: {channel_name}\n"]
    if not conversation_data:
        output_lines.append("No messages found in this conversation.")
        return "\n".join(output_lines)

    for msg_details in conversation_data:
        user_display = msg_details.get('user_name', msg_details.get('user_id', 'Unknown User'))
        output_lines.append(f"\n## Message from {user_display} at {msg_details['time']}")
        output_lines.append(f"{msg_details['text']}")

        if msg_details['replies']:
            output_lines.append("  ### Thread Replies:")
            for reply in msg_details['replies']:
                reply_user_display = reply.get('user_name', reply.get('user_id', 'Unknown User'))
                output_lines.append(f"    - **{reply_user_display} at {reply['time']}**: {reply['text']}")
        elif msg_details['reply_count'] > 0:
            output_lines.append("  _(This message has replies, but they were not fetched or an error occurred.)_")
            
    return "\n".join(output_lines)
