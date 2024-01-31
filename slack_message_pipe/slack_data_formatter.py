"""Fetches and formats data from Slack API into intermediate data structures."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime as dt
import logging
from typing import Any, Optional

import pytz

from slack_message_pipe.intermediate_data import (
    Attachment,
    Block,
    Channel,
    ChannelExportData,
    Composition,
    Element,
    File,
    Message,
    Reaction,
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
            top_level_slack_messages = self._slack_service.fetch_messages_from_channel(
                channel_id, max_messages, oldest, latest
            )
            threads_by_ts = self._slack_service.fetch_threads_by_ts(
                channel_id, top_level_slack_messages, max_messages, oldest, latest
            )

            # Format messages into intermediate data structures
            top_level_messages = [
                self._format_message(sm) for sm in top_level_slack_messages
            ]

            # Create a mapping for quick access to parent messages by ts
            parent_messages_by_ts = {msg.ts: msg for msg in top_level_messages}

            # Iterate over threads and nest them within their parent messages
            for thread_ts, thread_messages in threads_by_ts.items():
                parent_message = parent_messages_by_ts.get(thread_ts)
                if parent_message:
                    for reply_slack_message in thread_messages:
                        # Omit the parent message
                        if reply_slack_message["ts"] != thread_ts:
                            reply_message = self._format_message(reply_slack_message)
                            parent_message.replies.append(reply_message)

            # Get channel information
            channel_name = self._slack_service.channel_names().get(
                channel_id, f"channel_{channel_id}"
            )
            channel = Channel(id=channel_id, name=channel_name)

            return ChannelExportData(
                channel=channel, top_level_messages=top_level_messages
            )
        except Exception as e:
            logger.exception("Error fetching and formatting channel data", exc_info=e)
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

        ts = msg["ts"]
        thread_ts = msg.get("thread_ts")
        ts_display = self._format_slack_ts_for_display(ts)
        thread_ts_display = (
            self._format_slack_ts_for_display(thread_ts) if thread_ts else None
        )
        is_markdown = msg.get(
            "mrkdwn", True
        )  # Default to True if 'mrkdwn' field is missing
        text = self._message_to_markdown.transform_text(msg["text"], is_markdown)
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
            thread_ts=thread_ts,
            ts_display=ts_display,
            thread_ts_display=thread_ts_display,
            text=text,
            reactions=reactions,
            files=files,
            attachments=attachments,
            blocks=blocks,
            is_bot="bot_id" in msg,
        )

    def _format_slack_ts_for_display(self, ts: str) -> str:
        """Convert a Slack timestamp string to a human-readable format in GMT."""
        # Convert the Slack timestamp to a float, then to a datetime object in UTC
        dt_obj = dt.datetime.fromtimestamp(float(ts), tz=pytz.utc)
        # Format the datetime object as a string, including 'GMT' to indicate the timezone
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S GMT")

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
        # Determine if the attachment text should be treated as markdown
        is_markdown = "text" in attachment.get("mrkdwn_in", [])
        text = self._message_to_markdown.transform_text(
            attachment.get("text", ""), is_markdown
        )

        return Attachment(
            fallback=attachment.get("fallback", ""),
            text=text,
            pretext=attachment.get("pretext"),
            title=attachment.get("title"),
            title_link=attachment.get("title_link"),
            author_name=attachment.get("author_name"),
            footer=attachment.get("footer"),
            image_url=attachment.get("image_url"),
            color=attachment.get("color"),
        )

    def _format_block(self, block: dict[str, Any]) -> Block:
        block_type = block["type"]
        block_text = None
        block_fields = None
        block_accessory = None
        block_elements = None

        if "text" in block:
            block_text = Composition(
                type=block["text"]["type"], text=block["text"]["text"]
            )

        if "fields" in block:
            block_fields = [
                Composition(type=f["type"], text=f["text"]) for f in block["fields"]
            ]

        if "accessory" in block:
            block_accessory = self._format_element(block["accessory"])

        if "elements" in block:
            block_elements = [self._format_element(el) for el in block["elements"]]

        return Block(
            type=block_type,
            text=block_text,
            fields=block_fields,
            accessory=block_accessory,
            elements=block_elements,
        )

    def _format_element(self, element: dict[str, Any]) -> Element:
        element_type = element["type"]
        element_text = None

        if "text" in element:
            element_text = Composition(
                type=element["text"]["type"], text=element["text"]["text"]
            )

        # Handle other fields and types of elements as necessary

        return Element(
            type=element_type,
            text=element_text,
            # ... other fields ...
        )
