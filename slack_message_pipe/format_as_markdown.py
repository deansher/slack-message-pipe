"""Formats a ChannelHistory object into human-readable Markdown with hierarchical threads."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

from dataclasses import dataclass
from typing import Optional

from slack_message_pipe.intermediate_data import Attachment, ChannelHistory, Message

# Throughout this file, whenever a function formats something that should be its own paragraph,
# it includes two trailing new lines.


@dataclass
class Config:
    """Configuration for formatting Markdown."""

    images: bool = True


def format_as_markdown(history: ChannelHistory, config: Config) -> str:
    """Converts a ChannelHistory object into human-readable Markdown with
    hierarchical threads."""

    output = f"# {history.channel.name}\n\n"

    for message in history.top_level_messages:
        # Heading level 2 for top-level messages
        output += format_message(message, 2, config=config)

    return output


def format_message(message: Message, heading_level: int, config: Config) -> str:
    """Formats a Message object into human-readable Markdown, including a header."""
    user_display = message.user.name if message.user else "Unknown User"
    header = f"{'#' * heading_level} {user_display} ({message.ts_display})"
    output = f"{header}\n\n{message.markdown}\n\n"

    # Attachments (Slack's legacy method)
    if message.attachments:
        for attachment in message.attachments:
            output += format_attachment(
                attachment, heading_level=heading_level + 1, config=config
            )

    # Files
    if message.files:
        for file in message.files:
            output += f"* [{file.title or file.name}]({file.url})\n\n"

    # Reactions
    if message.reactions:
        reactions_line = "Reactions: "
        reactions_line += ", ".join(f"{r.name} ({r.count})" for r in message.reactions)
        output += reactions_line + "\n\n"

    if message.replies:
        output += "\n"
        output += format_replies(
            message.replies, level=heading_level + 1, config=config
        )
    return output


def format_replies(replies: list[Message], level: int, config: Config) -> str:
    """Recursively formats replies at the specified heading level."""
    output = ""
    for reply in replies:
        output += format_message(reply, level, config=config)
        if reply.replies:
            output += "\n"
            output += format_replies(reply.replies, level=level + 1, config=config)

    return output


def format_attachment(
    attachment: Attachment, heading_level: int, config: Config
) -> str:
    """Formats an Attachment object into human-readable Markdown, treating it as a subsection.

    Args:
        attachment: The Attachment object to format.
        heading_level: The Markdown heading level for the attachment title (default is 4).
    """
    # Determine the heading prefix based on the specified level
    heading_prefix = "#" * heading_level

    output = f"{heading_prefix} Attachment\n\n"  # Use the dynamic heading level

    if attachment.pretext:
        output += f"{attachment.pretext}\n\n"
    if attachment.title:
        title_link = (
            f"[{attachment.title}]({attachment.title_link})"
            if attachment.title_link
            else attachment.title
        )
        output += f"* **{title_link}**\n\n"
    if attachment.author_name:
        output += f"* Author: {attachment.author_name}\n\n"
    if attachment.markdown:
        output += f"{attachment.markdown}\n\n"
    if attachment.footer:
        output += f"* Footer: {attachment.footer}\n\n"  # Use bullet for Footer
    if config.images and attachment.image_url:
        output += f"![image]({attachment.image_url})\n\n"

    return output
