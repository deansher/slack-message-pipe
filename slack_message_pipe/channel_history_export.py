"""Fetches and formats data from Slack API into intermediate data structures."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime as dt
import logging
import re
from pprint import pformat
from typing import Any, Optional

from slack_message_pipe.intermediate_data import (
    ActionsBlock,
    Attachment,
    Block,
    ButtonElement,
    Channel,
    ChannelHistory,
    Composition,
    ContextBlock,
    DividerBlock,
    Element,
    File,
    ImageBlock,
    ImageElement,
    Message,
    Reaction,
    RichTextBlock,
    RichTextChannelElement,
    RichTextElement,
    RichTextEmojiElement,
    RichTextLinkElement,
    RichTextListElement,
    RichTextPreformattedElement,
    RichTextQuoteElement,
    RichTextSectionElement,
    RichTextStyle,
    RichTextTextElement,
    RichTextUserElement,
    RichTextUserGroupElement,
    SectionBlock,
    SelectOption,
    StaticSelectElement,
    User,
)
from slack_message_pipe.locales import LocaleHelper
from slack_message_pipe.slack_service import SlackMessage, SlackService
from slack_message_pipe.slack_text_converter import SlackTextConverter

logger = logging.getLogger(__name__)


class ChannelHistoryExporter:
    """Class for fetching and formatting data from Slack API into intermediate data structures."""

    def __init__(
        self,
        slack_service: SlackService,
        locale_helper: LocaleHelper,
        slack_text_converter: SlackTextConverter,
    ):
        self._slack_service = slack_service
        self._locale_helper = locale_helper
        self._slack_text_converter = slack_text_converter

    def fetch_and_format_channel_data(
        self,
        channel_id: str,
        oldest: Optional[dt.datetime] = None,
        latest: Optional[dt.datetime] = None,
        max_messages: Optional[int] = None,
    ) -> ChannelHistory:
        logger.debug(
            f"{self.__class__.__name__}.fetch_and_format_channel_data: Processing channel {channel_id}"
        )
        try:
            top_level_slack_messages = self._slack_service.fetch_messages_from_channel(
                channel_id, max_messages, oldest, latest
            )
            threads_by_ts = self._slack_service.fetch_threads_by_ts(
                channel_id, top_level_slack_messages, max_messages, oldest, latest
            )

            top_level_messages = [
                self._format_message(sm) for sm in top_level_slack_messages
            ]
            parent_messages_by_ts = {msg.ts: msg for msg in top_level_messages}

            for thread_ts, thread_messages in threads_by_ts.items():
                parent_message = parent_messages_by_ts.get(thread_ts)
                if parent_message:
                    for reply_slack_message in thread_messages:
                        if reply_slack_message["ts"] != thread_ts:
                            reply_message = self._format_message(reply_slack_message)
                            parent_message.replies.append(reply_message)

            channel_name = self._slack_service.channel_names().get(
                channel_id, f"channel_{channel_id}"
            )
            channel = Channel(id=channel_id, name=channel_name)

            return ChannelHistory(
                channel=channel, top_level_messages=top_level_messages
            )
        except Exception as e:
            logger.exception("Error fetching and formatting channel data", exc_info=e)
            raise

    def _format_message(self, msg: SlackMessage) -> Message:
        logger.debug(
            f"{self.__class__.__name__}._format_message: Slack API data received:"
        )
        logger.debug(pformat(msg))

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
        is_markdown = msg.get("mrkdwn", True)
        markdown = self._slack_text_converter.convert_slack_text(
            msg["text"], is_markdown=is_markdown
        )
        reactions = [
            self._format_reaction(reaction) for reaction in msg.get("reactions", [])
        ]
        files = [self._format_file(file) for file in msg.get("files", [])]
        attachments = [
            self._format_attachment(attachment)
            for attachment in msg.get("attachments", [])
        ]
        blocks = [self._format_block(block) for block in msg.get("blocks", [])]

        formatted_message = Message(
            user=user,
            ts=ts,
            thread_ts=thread_ts,
            ts_display=ts_display,
            thread_ts_display=thread_ts_display,
            markdown=markdown,
            reactions=reactions,
            files=files,
            attachments=attachments,
            blocks=blocks,
            is_bot="bot_id" in msg,
        )

        logger.debug(
            f"{self.__class__.__name__}._format_message: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_message))

        return formatted_message

    def _format_slack_ts_for_display(self, ts: str) -> str:
        """Convert a Slack timestamp string to a human-readable format in GMT."""
        logger.debug(
            f"{self.__class__.__name__}._format_slack_ts_for_display: Slack API data received:"
        )
        logger.debug(pformat(ts))

        # Always display as UTC because the resulting data should be user-independent.
        dt_obj = dt.datetime.fromtimestamp(float(ts), tz=dt.timezone.utc)
        formatted_ts = dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z")

        logger.debug(
            f"{self.__class__.__name__}._format_slack_ts_for_display: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_ts))

        return formatted_ts

    def _format_reaction(self, reaction: dict[str, Any]) -> Reaction:
        """Formats a reaction from Slack API data into a Reaction data class."""
        logger.debug(
            f"{self.__class__.__name__}._format_reaction: Slack API data received:"
        )
        logger.debug(pformat(reaction))

        formatted_reaction = Reaction(
            name=reaction["name"],
            count=reaction["count"],
            user_ids=reaction["users"],
        )

        logger.debug(
            f"{self.__class__.__name__}._format_reaction: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_reaction))

        return formatted_reaction

    def _format_file(self, file: dict[str, Any]) -> File:
        """Formats a file from Slack API data into a File data class."""
        logger.debug(
            f"{self.__class__.__name__}._format_file: Slack API data received:"
        )
        logger.debug(pformat(file))

        formatted_file = File(
            id=file["id"],
            url=file["url_private"],
            name=file["name"],
            filetype=file["filetype"],
            title=file.get("title"),
            mimetype=file.get("mimetype"),
            size=file.get("size"),
            timestamp=(
                dt.datetime.fromtimestamp(
                    float(file["timestamp"]), tz=self._locale_helper.timezone
                )
                if "timestamp" in file
                else None
            ),
        )

        logger.debug(
            f"{self.__class__.__name__}._format_file: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_file))

        return formatted_file

    def _format_attachment(self, attachment: dict[str, Any]) -> Attachment:
        """Formats an attachment from Slack API data into an Attachment data class."""
        logger.debug(
            f"{self.__class__.__name__}._format_attachment: Slack API data received:"
        )
        logger.debug(pformat(attachment))

        is_markdown = "text" in attachment.get("mrkdwn_in", [])
        formatted_attachment = Attachment(
            fallback=attachment.get("fallback", ""),
            markdown=self._slack_text_converter.convert_slack_text(
                attachment.get("text", ""), is_markdown=is_markdown
            ),
            pretext=attachment.get("pretext"),
            title=attachment.get("title"),
            title_link=attachment.get("title_link"),
            author_name=attachment.get("author_name"),
            footer=attachment.get("footer"),
            image_url=attachment.get("image_url"),
            color=attachment.get("color"),
        )

        logger.debug(
            f"{self.__class__.__name__}._format_attachment: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_attachment))

        return formatted_attachment

    def _format_block(self, block: dict[str, Any]) -> Block:
        """Formats a block from Slack API data into a Block data class."""
        logger.debug(
            f"{self.__class__.__name__}._format_block: Slack API data received:"
        )
        logger.debug(pformat(block))

        block_type = block["type"]
        formatted_block: Block
        if block_type == "section":
            formatted_block = self._format_section_block(block)
        elif block_type == "divider":
            formatted_block = self._format_divider_block(block)
        elif block_type == "image":
            formatted_block = self._format_image_block(block)
        elif block_type == "actions":
            formatted_block = self._format_actions_block(block)
        elif block_type == "context":
            formatted_block = self._format_context_block(block)
        elif block_type == "rich_text":
            formatted_block = self._format_rich_text_block(block)
        else:
            logger.warning(f"Unsupported block type encountered: {block_type}")
            formatted_block = Block(type=block_type)  # Fallback to a generic Block

        logger.debug(
            f"{self.__class__.__name__}._format_block: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_block))

        return formatted_block

    def _format_section_block(self, block: dict[str, Any]) -> SectionBlock:
        """Formats a section block from Slack API data."""
        text = (
            Composition(type=block["text"]["type"], text=block["text"]["text"])
            if "text" in block
            else None
        )
        fields = (
            [
                Composition(type=f["type"], text=f["text"])
                for f in block.get("fields", [])
            ]
            if "fields" in block
            else None
        )
        accessory = (
            self._format_element(block["accessory"]) if "accessory" in block else None
        )
        return SectionBlock(
            type="section", text=text, fields=fields, accessory=accessory
        )

    def _format_divider_block(self, block: dict[str, Any]) -> DividerBlock:
        """Formats a divider block from Slack API data."""
        return DividerBlock(type="divider")

    def _format_image_block(self, block: dict[str, Any]) -> ImageBlock:
        """Formats an image block from Slack API data."""
        image_url = block["image_url"]
        alt_text = block["alt_text"]
        title = (
            Composition(type="plain_text", text=block["title"]["text"])
            if "title" in block
            else None
        )
        return ImageBlock(
            type="image", image_url=image_url, alt_text=alt_text, title=title
        )

    def _format_actions_block(self, block: dict[str, Any]) -> ActionsBlock:
        """Formats an actions block from Slack API data."""
        elements = [
            self._format_element(el) for el in block.get("elements", [])
        ]  # Assuming _format_element is implemented
        return ActionsBlock(type="actions", elements=elements)

    def _format_context_block(self, block: dict[str, Any]) -> ContextBlock:
        """Formats a context block from Slack API data."""
        elements = [
            self._format_element(el) for el in block.get("elements", [])
        ]  # Assuming _format_element is implemented
        return ContextBlock(type="context", elements=elements)

    def _format_rich_text_block(self, block: dict[str, Any]) -> RichTextBlock:
        """Formats a rich text block from Slack API data."""
        elements = [
            self._format_rich_text_element(el) for el in block.get("elements", [])
        ]  # Placeholder for rich text element formatting
        return RichTextBlock(type="rich_text", elements=elements)

    def _format_element(self, element: dict[str, Any]) -> Element:
        """Formats an element from Slack API data into an appropriate Element subclass."""
        logger.debug(
            f"{self.__class__.__name__}._format_element: Slack API data received:"
        )
        logger.debug(pformat(element))

        element_type = element["type"]
        formatted_element: Element
        if element_type == "button":
            formatted_element = self._format_button_element(element)
        elif element_type == "image":
            formatted_element = self._format_image_element(element)
        elif element_type == "static_select":
            formatted_element = self._format_static_select_element(element)
        # Add more elif branches for other element types as needed
        else:
            logger.warning(f"Unsupported element type encountered: {element_type}")
            formatted_element = Element(
                type=element_type
            )  # Placeholder for unsupported element types

        logger.debug(
            f"{self.__class__.__name__}._format_element: Intermediate data produced:"
        )
        logger.debug(pformat(formatted_element))

        return formatted_element

    def _format_button_element(self, element: dict[str, Any]) -> ButtonElement:
        """Formats a button element from Slack API data."""
        text = element["text"]["text"]
        value = element.get("value", "")
        action_id = element.get("action_id", "")
        return ButtonElement(type="button", text=text, value=value, action_id=action_id)

    def _format_image_element(self, element: dict[str, Any]) -> ImageElement:
        """Formats an image element from Slack API data."""
        image_url = element["image_url"]
        alt_text = element["alt_text"]
        return ImageElement(type="image", image_url=image_url, alt_text=alt_text)

    def _format_static_select_element(
        self, element: dict[str, Any]
    ) -> StaticSelectElement:
        """Formats a static select element from Slack API data."""
        placeholder = element["placeholder"]["text"]
        options = [self._format_option(option) for option in element.get("options", [])]
        action_id = element.get("action_id", "")
        return StaticSelectElement(
            type="static_select",
            placeholder=placeholder,
            options=options,
            action_id=action_id,
        )

    def _format_option(self, option: dict[str, Any]) -> SelectOption:
        """Formats a select option from Slack API data."""
        text = option["text"]["text"]
        value = option["value"]
        return SelectOption(text=text, value=value)

    def _format_rich_text_element(self, element: dict[str, Any]) -> RichTextElement:
        """Formats a rich text element from Slack API data into a RichTextElement data class."""
        logger.debug(
            f"{self.__class__.__name__}._format_rich_text_element: Slack API data received:"
        )
        logger.debug(pformat(element))

        element_type = element["type"]
        if element_type == "rich_text_section":
            return self._format_rich_text_section_element(element)
        elif element_type == "rich_text_list":
            return self._format_rich_text_list_element(element)
        elif element_type == "rich_text_preformatted":
            return self._format_rich_text_preformatted_element(element)
        elif element_type == "rich_text_quote":
            return self._format_rich_text_quote_element(element)
        elif element_type == "text":
            return self._format_rich_text_text_element(element)
        elif element_type == "channel":
            return self._format_rich_text_channel_element(element)
        elif element_type == "user":
            return self._format_rich_text_user_element(element)
        elif element_type == "user_group":
            return self._format_rich_text_user_group_element(element)
        elif element_type == "emoji":
            return self._format_rich_text_emoji_element(element)
        elif element_type == "link":
            return self._format_rich_text_link_element(element)
        else:
            logger.warning(
                f"Unsupported rich text element type encountered: {element_type}"
            )
            return RichTextElement(type=element_type)  # Fallback for unsupported types

    def _format_rich_text_section_element(
        self, element: dict[str, Any]
    ) -> RichTextSectionElement:
        """Formats a rich text section element from Slack API data."""
        elements = [
            self._format_rich_text_element(el) for el in element.get("elements", [])
        ]
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextSectionElement(
            type="rich_text_section", elements=elements, style=style
        )

    def _format_rich_text_list_element(
        self, element: dict[str, Any]
    ) -> RichTextListElement:
        """Formats a rich text list element from Slack API data."""
        elements = [
            self._format_rich_text_section_element(el)
            for el in element.get("elements", [])
        ]
        style = element.get("style", "bullet")  # Default to bullet if not specified
        indent = element.get("indent")
        offset = element.get("offset")
        border = element.get("border")
        return RichTextListElement(
            type="rich_text_list",
            style=style,
            elements=elements,
            indent=indent,
            offset=offset,
            border=border,
        )

    def _format_rich_text_preformatted_element(
        self, element: dict[str, Any]
    ) -> RichTextPreformattedElement:
        """Formats a rich text preformatted element from Slack API data."""
        text = "".join(
            [el.get("text", "") for el in element.get("elements", [])]
        )  # Concatenate all text elements
        border = element.get("border")
        return RichTextPreformattedElement(
            type="rich_text_preformatted", text=text, border=border
        )

    def _format_rich_text_quote_element(
        self, element: dict[str, Any]
    ) -> RichTextQuoteElement:
        """Formats a rich text quote element from Slack API data."""
        text = "".join(
            [el.get("text", "") for el in element.get("elements", [])]
        )  # Concatenate all text elements
        border = element.get("border")
        return RichTextQuoteElement(type="rich_text_quote", text=text, border=border)

    def _parse_text_style(self, style: dict[str, Any]) -> RichTextStyle:
        """Parses text style information from a rich text element."""
        return RichTextStyle(
            bold=style.get("bold", False),
            italic=style.get("italic", False),
            strike=style.get("strike", False),
            code=style.get("code", False),
            highlight=style.get("highlight", False),
            client_highlight=style.get("client_highlight", False),
            unlink=style.get("unlink", False),
        )

    def _format_rich_text_text_element(
        self, element: dict[str, Any]
    ) -> RichTextTextElement:
        """Formats a rich text text element from Slack API data."""
        logger.debug(
            f"{self.__class__.__name__}._format_rich_text_text_element: Slack API data received:"
        )
        logger.debug(pformat(element))

        text = element.get("text", "")
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextTextElement(type="text", text=text, style=style)

    def _format_rich_text_channel_element(
        self, element: dict[str, Any]
    ) -> RichTextChannelElement:
        """Formats a rich text channel element from Slack API data."""
        channel_id = element["channel_id"]
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextChannelElement(
            type="channel", channel_id=channel_id, style=style
        )

    def _format_rich_text_user_element(
        self, element: dict[str, Any]
    ) -> RichTextUserElement:
        """Formats a rich text user element from Slack API data."""
        user_id = element["user_id"]
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextUserElement(type="user", user_id=user_id, style=style)

    def _format_rich_text_user_group_element(
        self, element: dict[str, Any]
    ) -> RichTextUserGroupElement:
        """Formats a rich text user group element from Slack API data."""
        user_group_id = element["user_group_id"]
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextUserGroupElement(
            type="user_group", user_group_id=user_group_id, style=style
        )

    def _format_rich_text_emoji_element(
        self, element: dict[str, Any]
    ) -> RichTextEmojiElement:
        """Formats a rich text emoji element from Slack API data."""
        emoji_name = element["name"]
        return RichTextEmojiElement(type="emoji", emoji_name=emoji_name)

    def _format_rich_text_link_element(
        self, element: dict[str, Any]
    ) -> RichTextLinkElement:
        """Formats a rich text link element from Slack API data."""
        text = element["text"]["text"]
        url = element["url"]
        style = (
            self._parse_text_style(element.get("style", {}))
            if "style" in element
            else None
        )
        return RichTextLinkElement(type="link", text=text, url=url, style=style)
