"""Fetches and formats data from Slack API into intermediate data structures."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime as dt
import logging
from typing import Any, Optional

from slack_message_pipe.intermediate_data import (
    Attachment,
    Block,
    Channel,
    ChannelExportData,
    File,
    Message,
    Reaction,
    Thread,
    User,
)
from slack_message_pipe.locales import LocaleHelper
from slack_message_pipe.message_to_markdown import MessageToMarkdown
from slack_message_pipe.slack_service import SlackMessage, SlackService

logger = logging.getLogger(__name__)


class SlackDataFormatter:
    """Class for fetching and formatting data from Slack API into intermediate data structures."""

    def __init__(
        self,
        slack_service: SlackService,
        locale_helper: LocaleHelper,
        message_to_markdown: MessageToMarkdown,
    ):
        """
        Initialize the SlackDataFormatter with a SlackService, LocaleHelper, and MessageToMarkdown.

        Args:
            slack_service: The SlackService instance to interact with the Slack API.
            locale_helper: The LocaleHelper instance for locale-specific formatting.
            message_to_markdown: The MessageToMarkdown instance to convert messages to markdown.
        """
        self._slack_service = slack_service
        self._locale_helper = locale_helper
        self._message_to_markdown = message_to_markdown

    def fetch_and_format_channel_data(
        self,
        channel_id: str,
        oldest: Optional[dt.datetime] = None,
        latest: Optional[dt.datetime] = None,
        max_messages: Optional[int] = None,
    ) -> ChannelExportData:
        """
        Fetches messages and threads from a Slack channel and formats them into intermediate data structures.

        Args:
            channel_id: The ID of the Slack channel to fetch data from.
            oldest: The oldest message timestamp to fetch.
            latest: The latest message timestamp to fetch.
            max_messages: The maximum number of messages to fetch.

        Returns:
            A ChannelExportData object containing formatted channel data.
        """
        try:
            messages_data = self._slack_service.fetch_messages_from_channel(
                channel_id, max_messages, oldest, latest
            )
            threads_data = self._slack_service.fetch_threads_from_messages(
                channel_id, messages_data, max_messages, oldest, latest
            )

            # Format messages and threads into intermediate data structures
            messages = [self._format_message(msg) for msg in messages_data]
            threads = [self._format_thread(thread) for thread in threads_data.values()]

            # Get channel information
            channel_name = self._slack_service.channel_names().get(
                channel_id, f"channel_{channel_id}"
            )
            channel = Channel(id=channel_id, name=channel_name)

            return ChannelExportData(
                channel=channel, messages=messages, threads=threads
            )
        except Exception as e:
            logger.error(f"Error fetching and formatting channel data: {e}")
            raise

    def _format_message(self, msg: SlackMessage) -> Message:
        """
        Formats a single message from Slack API data into a Message data class.

        Args:
            msg: The Slack message data to format.

        Returns:
            A Message object with formatted data.
        """
        user: Optional[User] = None
        user_id = msg.get("user") or msg.get("bot_id")
        if user_id:
            user_name = self._slack_service.user_names().get(
                user_id, f"unknown_user_{user_id}"
            )
            user = User(id=user_id, name=user_name)

        ts = dt.datetime.fromtimestamp(
            float(msg["ts"]), tz=self._locale_helper.timezone
        )
        text = self._message_to_markdown.transform_text(msg["text"])
        reactions = [
            self._format_reaction(reaction) for reaction in msg.get("reactions", [])
        ]
        files = [self._format_file(file) for file in msg.get("files", [])]
        attachments = [
            self._format_attachment(attachment)
            for attachment in msg.get("attachments", [])
        ]
        blocks = [self._format_block(block) for block in msg.get("blocks", [])]

        return Message(
            user=user,
            ts=ts,
            text=text,
            reactions=reactions,
            files=files,
            attachments=attachments,
            blocks=blocks,
            thread_ts=msg.get("thread_ts"),
            is_bot="bot_id" in msg,
        )

    def _format_reaction(self, reaction: dict[str, Any]) -> Reaction:
        """
        Formats a reaction from Slack API data into a Reaction data class.

        Args:
            reaction: The reaction data from Slack API.

        Returns:
            A Reaction object with formatted data.
        """
        return Reaction(
            name=reaction["name"],
            count=reaction["count"],
            user_ids=reaction["users"],
        )

    def _format_file(self, file: dict[str, Any]) -> File:
        """
        Formats a file from Slack API data into a File data class.

        Args:
            file: The file data from Slack API.

        Returns:
            A File object with formatted data.
        """
        return File(
            id=file["id"],
            url=file["url_private"],
            name=file["name"],
            filetype=file["filetype"],
            title=file.get("title"),
            mimetype=file.get("mimetype"),
            size=file.get("size"),
            timestamp=dt.datetime.fromtimestamp(
                float(file["timestamp"]), tz=self._locale_helper.timezone
            )
            if "timestamp" in file
            else None,
        )

    def _format_attachment(self, attachment: dict[str, Any]) -> Attachment:
        """
        Formats an attachment from Slack API data into an Attachment data class.

        Args:
            attachment: The attachment data from Slack API.

        Returns:
            An Attachment object with formatted data.
        """
        return Attachment(
            fallback=attachment.get("fallback", ""),
            text=attachment.get("text", ""),
            pretext=attachment.get("pretext"),
            title=attachment.get("title"),
            title_link=attachment.get("title_link"),
            author_name=attachment.get("author_name"),
            fields=attachment.get("fields"),
            footer=attachment.get("footer"),
            image_url=attachment.get("image_url"),
            color=attachment.get("color"),
        )

    def _format_block(self, block: dict[str, any]) -> Block:
        """
        Formats a block from Slack API data into a Block data class.

        Args:
            block: The block data from Slack API.

        Returns:
            A Block object with formatted data.
        """
        return Block(
            type=block["type"],
            text=block.get("text", None),
            elements=block.get("elements"),
            accessory=block.get("accessory"),
        )

    def _format_thread(self, thread_data: list[SlackMessage]) -> Thread:
        """
        Formats a thread of messages from Slack API data into a Thread data class.

        Args:
            thread_data: The list of Slack messages that form a thread.

        Returns:
            A Thread object with formatted data.
        """
        parent_msg = self._format_message(thread_data[0])
        replies = [self._format_message(reply) for reply in thread_data[1:]]
        return Thread(parent=parent_msg, replies=replies)
