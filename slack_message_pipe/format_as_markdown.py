"""Formats a ChannelHistory object into human-readable Markdown with hierarchical threads."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime

from slack_message_pipe.intermediate_data import ChannelHistory, Message


def format_as_markdown(history: ChannelHistory) -> str:
    """Converts a ChannelHistory object into human-readable Markdown with
    hierarchical threads."""

    output = f"# {history.channel.name}\n\n"

    for message in history.top_level_messages:
        output += f"## {message.user.name if message.user else 'Unknown User'} ({message.ts_display})\n"
        output += f"{message.markdown}\n\n"  # Main message body

        # Attachments (Slack's legacy method)
        if message.attachments:
            for attachment in message.attachments:
                output += (
                    f"* **{attachment.title}** (fallback: {attachment.fallback})\n"
                )

        # Files
        if message.files:
            for file in message.files:
                output += f"* [{file.title or file.name}]({file.url})\n"

        # Reactions
        if message.reactions:
            reactions_line = "Reactions: "
            reactions_line += ", ".join(
                f"{r.name} ({r.count})" for r in message.reactions
            )
            output += reactions_line + "\n"

        output += "\n"
        output += format_replies(message.replies, level=3)

    return output


def format_replies(replies: list[Message], level: int) -> str:
    """Recursively formats replies at the specified heading level."""

    output = ""
    for reply in replies:
        output += f"{'#' * level} {reply.user.name if reply.user else 'Unknown User'} ({reply.ts_display})\n"
        output += f"{reply.markdown}\n\n"  # Reply body

        # For attachments, we use Slack's legacy method instead of parsing the blocks.
        # Attachments in blocks will not show up.
        if reply.attachments:
            for attachment in reply.attachments:
                output += (
                    f"* **{attachment.title}** (fallback: {attachment.fallback})\n"
                )

        if reply.files:
            for file in reply.files:
                output += f"* [{file.title or file.name}]({file.url})\n"

        if reply.reactions:
            reactions_line = "Reactions: "
            reactions_line += ", ".join(
                f"{r.name} ({r.count})" for r in reply.reactions
            )
            output += reactions_line + "\n"

        output += "\n"
        output += format_replies(reply.replies, level=level + 1)  # Further nesting

    return output
