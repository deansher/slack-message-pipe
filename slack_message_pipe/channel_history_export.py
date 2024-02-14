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
        """
        Fetches and formats data from Slack API into intermediate data structures.
        """
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

            # Reverse the order of top-level messages to be in chronological order
            top_level_slack_messages.reverse()

            top_level_messages = [
                self._format_message(sm) for sm in top_level_slack_messages
            ]
            parent_messages_by_ts = {msg.ts: msg for msg in top_level_messages}

            for thread_ts, thread_messages in threads_by_ts.items():
                parent_message = parent_messages_by_ts.get(thread_ts)
                if parent_message:
                    # Reverse the order of thread messages to be in chronological order
                    thread_messages.reverse()
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
            logger.error(
                "Error fetching and formatting channel data: %s", str(e), exc_info=True
            )
            raise

    def _format_message(self, msg: SlackMessage) -> Message:
        """Formats a message from Slack API data into a Message data class."""
        try:
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
        except Exception as e:
            logger.warning(f"Failed to format message: {pformat(msg)}. Error: {e}")
            # Return a placeholder message indicating an issue with formatting
            return Message(
                user=User(id="unknown", name="Unknown User"),
                ts="0",
                thread_ts=None,
                ts_display="N/A",
                thread_ts_display=None,
                markdown="*Message could not be formatted.*",
                reactions=[],
                files=[],
                attachments=[],
                blocks=[],
                is_bot=False,
            )

    def _format_slack_ts_for_display(self, ts: str) -> str:
        """Converts a Slack timestamp string to a human-readable format in GMT."""
        try:
            # Always display as UTC because the resulting data should be user-independent.
            dt_obj = dt.datetime.fromtimestamp(float(ts), tz=dt.timezone.utc)
            formatted_ts = dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z")
            return formatted_ts
        except Exception as e:
            logger.warning(
                f"Failed to convert Slack timestamp {ts} to display format. Error: {e}"
            )
            # Return a placeholder or the original timestamp in case of failure
            return "Invalid Timestamp"

    def _format_reaction(self, reaction: dict[str, Any]) -> Reaction:
        """Formats a reaction from Slack API data into a Reaction data class."""
        try:
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
        except Exception as e:
            logger.warning(f"Failed to format reaction from Slack API data. Error: {e}")
            # Return a default Reaction object in case of failure
            return Reaction(name="", count=0, user_ids=[])

    def _format_file(self, file: dict[str, Any]) -> File:
        """Formats a file from Slack API data into a File data class."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_file: Slack API data received:"
            )
            logger.debug(pformat(file))

            formatted_file = File(
                id=file["id"],
                url=file["url_private"],
                name=file["name"],
                filetype=file["filetype"],
                title=file.get("title", ""),
                mimetype=file.get("mimetype", ""),
                size=file.get("size", 0),
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
        except Exception as e:
            logger.warning(
                f"Failed to format file from Slack API data. Error: {e}. Returning default File object."
            )
            # Return a default File object in case of failure
            return File(
                id="",
                url="",
                name="",
                filetype="",
                title="",
                mimetype="",
                size=0,
                timestamp=None,
            )

    def _format_attachment(self, attachment: dict[str, Any]) -> Attachment:
        """Formats an attachment from Slack API data into an Attachment data class."""
        # TODO: See whether any of these fields have indicators as to whether they are markdown.
        try:
            # Convert title and footer using SlackTextConverter
            title = self._slack_text_converter.convert_slack_text(
                attachment.get("title", ""), is_markdown=True
            )
            footer = self._slack_text_converter.convert_slack_text(
                attachment.get("footer", ""), is_markdown=True
            )

            formatted_attachment = Attachment(
                fallback=attachment.get("fallback", ""),
                markdown=self._slack_text_converter.convert_slack_text(
                    attachment.get("text", ""), is_markdown=True
                ),
                pretext=attachment.get("pretext", ""),
                title=title,
                title_link=attachment.get("title_link", ""),
                author_name=attachment.get("author_name", ""),
                footer=footer,
                image_url=attachment.get("image_url", ""),
                color=attachment.get("color", ""),
            )

            return formatted_attachment
        except Exception as e:
            logger.warning(
                f"Failed to format attachment from Slack API data. Error: {e}."
            )
            return Attachment(
                fallback="",
                markdown="",
                pretext="",
                title="",
                title_link="",
                author_name="",
                footer="",
                image_url="",
                color="",
            )

    def _format_block(self, block: dict[str, Any]) -> Block:
        """Formats a block from Slack API data into a Block data class."""
        try:
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
                # Fallback to a generic Block with minimal information
                formatted_block = Block(type=block_type)

            logger.debug(
                f"{self.__class__.__name__}._format_block: Intermediate data produced:"
            )
            logger.debug(pformat(formatted_block))

            return formatted_block
        except Exception as e:
            logger.warning(
                f"Failed to format block from Slack API data. Error: {e}. Returning default Block object."
            )
            # Return a default Block object in case of failure
            return Block(type="unknown")

    def _format_section_block(self, block: dict[str, Any]) -> SectionBlock:
        """Formats a section block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_section_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            text = None
            if "text" in block:
                text = Composition(
                    type=block["text"]["type"], text=block["text"]["text"]
                )

            fields = None
            if "fields" in block:
                fields = [
                    Composition(type=f["type"], text=f["text"])
                    for f in block.get("fields", [])
                ]

            accessory = None
            if "accessory" in block:
                accessory = self._format_element(block["accessory"])

            section_block = SectionBlock(
                type="section", text=text, fields=fields, accessory=accessory
            )

            logger.debug(
                f"{self.__class__.__name__}._format_section_block: Intermediate data produced:"
            )
            logger.debug(pformat(section_block))

            return section_block
        except Exception as e:
            logger.warning(
                f"Failed to format section block from Slack API data. Error: {e}. Returning default SectionBlock object."
            )
            return SectionBlock(type="section", text=None, fields=None, accessory=None)

    def _format_divider_block(self, block: dict[str, Any]) -> DividerBlock:
        """Formats a divider block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_divider_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            divider_block = DividerBlock(type="divider")

            logger.debug(
                f"{self.__class__.__name__}._format_divider_block: Intermediate data produced:"
            )
            logger.debug(pformat(divider_block))

            return divider_block
        except Exception as e:
            logger.warning(
                f"Failed to format divider block from Slack API data. Error: {e}. Returning default DividerBlock object."
            )
            return DividerBlock(type="divider")

    def _format_image_block(self, block: dict[str, Any]) -> ImageBlock:
        """Formats an image block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_image_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            image_url = block["image_url"]
            alt_text = block["alt_text"]
            title = (
                Composition(type="plain_text", text=block["title"]["text"])
                if "title" in block
                else None
            )

            image_block = ImageBlock(
                type="image", image_url=image_url, alt_text=alt_text, title=title
            )

            logger.debug(
                f"{self.__class__.__name__}._format_image_block: Intermediate data produced:"
            )
            logger.debug(pformat(image_block))

            return image_block
        except Exception as e:
            logger.warning(
                f"Failed to format image block from Slack API data. Error: {e}. Returning default ImageBlock object."
            )
            return ImageBlock(type="image", image_url="", alt_text="")

    def _format_actions_block(self, block: dict[str, Any]) -> ActionsBlock:
        """Formats an actions block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_actions_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            elements = [self._format_element(el) for el in block.get("elements", [])]

            actions_block = ActionsBlock(type="actions", elements=elements)

            logger.debug(
                f"{self.__class__.__name__}._format_actions_block: Intermediate data produced:"
            )
            logger.debug(pformat(actions_block))

            return actions_block
        except Exception as e:
            logger.warning(
                f"Failed to format actions block from Slack API data. Error: {e}. Returning default ActionsBlock object."
            )
            return ActionsBlock(type="actions", elements=[])

    def _format_context_block(self, block: dict[str, Any]) -> ContextBlock:
        """Formats a context block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_context_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            elements = [self._format_element(el) for el in block.get("elements", [])]

            context_block = ContextBlock(type="context", elements=elements)

            logger.debug(
                f"{self.__class__.__name__}._format_context_block: Intermediate data produced:"
            )
            logger.debug(pformat(context_block))

            return context_block
        except Exception as e:
            logger.warning(
                f"Failed to format context block from Slack API data. Error: {e}. Returning default ContextBlock object."
            )
            return ContextBlock(type="context", elements=[])

    def _format_rich_text_block(self, block: dict[str, Any]) -> RichTextBlock:
        """Formats a rich text block from Slack API data."""
        try:
            logger.debug(
                f"{self.__class__.__name__}._format_rich_text_block: Slack API data received:"
            )
            logger.debug(pformat(block))

            elements = [
                self._format_rich_text_element(el) for el in block.get("elements", [])
            ]

            rich_text_block = RichTextBlock(type="rich_text", elements=elements)

            logger.debug(
                f"{self.__class__.__name__}._format_rich_text_block: Intermediate data produced:"
            )
            logger.debug(pformat(rich_text_block))

            return rich_text_block
        except Exception as e:
            logger.warning(
                f"Failed to format rich text block from Slack API data. Error: {e}. Returning default RichTextBlock object."
            )
            return RichTextBlock(type="rich_text", elements=[])

    def _format_element(self, element: dict[str, Any]) -> Element:
        """Formats an element from Slack API data into an appropriate Element subclass."""
        try:
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
        except Exception as e:
            logger.warning(
                f"Failed to format element from Slack API data. Error: {e}. Returning default Element object."
            )
            return Element(type="unknown")

    def _format_button_element(self, element: dict[str, Any]) -> ButtonElement:
        """Formats a button element from Slack API data."""
        try:
            text = element["text"]["text"]
            value = element.get("value", "")
            action_id = element.get("action_id", "")
            return ButtonElement(
                type="button", text=text, value=value, action_id=action_id
            )
        except Exception as e:
            logger.warning(
                f"Failed to format button element from Slack API data. Error: {e}. Returning default ButtonElement object."
            )
            return ButtonElement(type="button", text="Error", value="", action_id="")

    def _format_image_element(self, element: dict[str, Any]) -> ImageElement:
        """Formats an image element from Slack API data."""
        try:
            image_url = element["image_url"]
            alt_text = element["alt_text"]
            return ImageElement(type="image", image_url=image_url, alt_text=alt_text)
        except Exception as e:
            logger.warning(
                f"Failed to format image element from Slack API data. Error: {e}. Returning default ImageElement object."
            )
            return ImageElement(type="image", image_url="", alt_text="Error")

    def _format_static_select_element(
        self, element: dict[str, Any]
    ) -> StaticSelectElement:
        """Formats a static select element from Slack API data."""
        try:
            placeholder = element["placeholder"]["text"]
            options = [
                self._format_option(option) for option in element.get("options", [])
            ]
            action_id = element.get("action_id", "")
            return StaticSelectElement(
                type="static_select",
                placeholder=placeholder,
                options=options,
                action_id=action_id,
            )
        except Exception as e:
            logger.warning(
                f"Failed to format static select element from Slack API data. Error: {e}. Returning default StaticSelectElement object."
            )
            return StaticSelectElement(
                type="static_select", placeholder="Error", options=[], action_id=""
            )

    def _format_option(self, option: dict[str, Any]) -> SelectOption:
        """Formats a select option from Slack API data."""
        try:
            text = option["text"]["text"]
            value = option["value"]
            return SelectOption(text=text, value=value)
        except Exception as e:
            logger.warning(
                f"Failed to format select option from Slack API data. Error: {e}. Returning default SelectOption object."
            )
            return SelectOption(text="Error", value="")

    def _format_rich_text_element(self, element: dict[str, Any]) -> RichTextElement:
        """Formats a rich text element from Slack API data into a RichTextElement data class."""
        try:
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
                return RichTextElement(
                    type=element_type
                )  # Fallback for unsupported types
        except Exception as e:
            logger.warning(
                f"Failed to format rich text element from Slack API data. Error: {e}. Returning default RichTextElement object."
            )
            return RichTextElement(type="unknown")

    def _format_rich_text_section_element(
        self, element: dict[str, Any]
    ) -> RichTextSectionElement:
        """Formats a rich text section element from Slack API data."""
        try:
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
        except Exception as e:
            logger.warning(
                f"Failed to format rich text section element from Slack API data. Error: {e}. Returning default RichTextSectionElement object."
            )
            return RichTextSectionElement(
                type="rich_text_section", elements=[], style=None
            )

    def _format_rich_text_list_element(
        self, element: dict[str, Any]
    ) -> RichTextListElement:
        """Formats a rich text list element from Slack API data."""
        try:
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
        except Exception as e:
            logger.warning(
                f"Failed to format rich text list element from Slack API data. Error: {e}. Returning default RichTextListElement object."
            )
            return RichTextListElement(
                type="rich_text_list",
                style="bullet",
                elements=[],
                indent=0,
                offset=0,
                border=None,
            )

    def _format_rich_text_preformatted_element(
        self, element: dict[str, Any]
    ) -> RichTextPreformattedElement:
        """Formats a rich text preformatted element from Slack API data."""
        try:
            text = "".join(
                [el.get("text", "") for el in element.get("elements", [])]
            )  # Concatenate all text elements
            border = element.get("border")
            return RichTextPreformattedElement(
                type="rich_text_preformatted", text=text, border=border
            )
        except Exception as e:
            logger.warning(
                f"Failed to format rich text preformatted element from Slack API data. Error: {e}. Returning default RichTextPreformattedElement object."
            )
            return RichTextPreformattedElement(
                type="rich_text_preformatted", text="Error", border=None
            )

    def _format_rich_text_quote_element(
        self, element: dict[str, Any]
    ) -> RichTextQuoteElement:
        """Formats a rich text quote element from Slack API data."""
        try:
            text = "".join(
                [el.get("text", "") for el in element.get("elements", [])]
            )  # Concatenate all text elements
            border = element.get("border")
            return RichTextQuoteElement(
                type="rich_text_quote", text=text, border=border
            )
        except Exception as e:
            logger.warning(
                f"Failed to format rich text quote element from Slack API data. Error: {e}. Returning default RichTextQuoteElement object."
            )
            return RichTextQuoteElement(
                type="rich_text_quote", text="Error", border=None
            )

    def _parse_text_style(self, style: dict[str, Any]) -> RichTextStyle:
        """Parses text style information from a rich text element."""
        # Assuming this method is less prone to errors, but you can add error handling if needed.
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
        try:
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
        except Exception as e:
            logger.warning(
                f"Failed to format rich text text element from Slack API data. Error: {e}. Returning default RichTextTextElement object."
            )
            return RichTextTextElement(type="text", text="Error", style=None)

    def _format_rich_text_channel_element(
        self, element: dict[str, Any]
    ) -> RichTextChannelElement:
        """Formats a rich text channel element from Slack API data."""
        try:
            channel_id = element["channel_id"]
            style = (
                self._parse_text_style(element.get("style", {}))
                if "style" in element
                else None
            )
            return RichTextChannelElement(
                type="channel", channel_id=channel_id, style=style
            )
        except Exception as e:
            logger.warning(
                f"Failed to format rich text channel element from Slack API data. Error: {e}. Returning default RichTextChannelElement object."
            )
            return RichTextChannelElement(
                type="channel", channel_id="Error", style=None
            )

    def _format_rich_text_user_element(
        self, element: dict[str, Any]
    ) -> RichTextUserElement:
        """Formats a rich text user element from Slack API data."""
        try:
            user_id = element["user_id"]
            style = (
                self._parse_text_style(element.get("style", {}))
                if "style" in element
                else None
            )
            return RichTextUserElement(type="user", user_id=user_id, style=style)
        except Exception as e:
            logger.warning(
                f"Failed to format rich text user element from Slack API data. Error: {e}. Returning default RichTextUserElement object."
            )
            return RichTextUserElement(type="user", user_id="Error", style=None)

    def _format_rich_text_user_group_element(
        self, element: dict[str, Any]
    ) -> RichTextUserGroupElement:
        """Formats a rich text user group element from Slack API data."""
        try:
            user_group_id = element["user_group_id"]
            style = (
                self._parse_text_style(element.get("style", {}))
                if "style" in element
                else None
            )
            return RichTextUserGroupElement(
                type="user_group", user_group_id=user_group_id, style=style
            )
        except Exception as e:
            logger.warning(
                f"Failed to format rich text user group element from Slack API data. Error: {e}. Returning default RichTextUserGroupElement object."
            )
            return RichTextUserGroupElement(
                type="user_group", user_group_id="Error", style=None
            )

    def _format_rich_text_emoji_element(
        self, element: dict[str, Any]
    ) -> RichTextEmojiElement:
        """Formats a rich text emoji element from Slack API data."""
        try:
            emoji_name = element["name"]
            return RichTextEmojiElement(type="emoji", emoji_name=emoji_name)
        except Exception as e:
            logger.warning(
                f"Failed to format rich text emoji element from Slack API data. Error: {e}. Returning default RichTextEmojiElement object."
            )
            return RichTextEmojiElement(type="emoji", emoji_name="Error")

    def _format_rich_text_link_element(
        self, element: dict[str, Any]
    ) -> RichTextLinkElement:
        """Formats a rich text link element from Slack API data."""
        try:
            if isinstance(element.get("text"), dict):
                text = element.get("text", {}).get("text", element["url"])
            else:
                # If 'text' is not a dictionary, it might be directly the text string or absent.
                text = element.get("text", element["url"])
            url = element["url"]
            style = (
                self._parse_text_style(element.get("style", {}))
                if "style" in element
                else None
            )
            return RichTextLinkElement(type="link", text=text, url=url, style=style)
        except Exception as e:
            logger.warning(
                f"Failed to format rich text link element from Slack API data. Error: {e}. Returning default RichTextLinkElement object."
            )
            return RichTextLinkElement(
                type="link", text="Error", url="Error", style=None
            )
