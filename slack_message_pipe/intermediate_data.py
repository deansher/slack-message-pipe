"""Defines an intermediate language of python data structures between the Slack history import
and the formatted export."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime
from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class User:
    """Represents a Slack user with a unique identifier and display name."""

    id: str
    name: str


@dataclass
class Channel:
    """Represents a Slack channel with a unique identifier and name."""

    id: str
    name: str


@dataclass
class Reaction:
    """Represents a reaction to a Slack message, including the emoji used and the user IDs who reacted."""

    name: str
    count: int
    user_ids: list[str]


@dataclass
class File:
    """Represents a file shared in a Slack message, with metadata and optional preview."""

    id: str
    url: str
    name: str
    filetype: str
    title: Optional[str] = None
    preview: Optional[str] = None
    mimetype: Optional[str] = None
    size: Optional[int] = None
    timestamp: Optional[datetime.datetime] = None


@dataclass
class Attachment:
    """Represents an attachment to a Slack message, which may include text, fields, and other elements."""

    fallback: str
    markdown: str
    pretext: Optional[str] = None
    title: Optional[str] = None
    title_link: Optional[str] = None
    author_name: Optional[str] = None
    footer: Optional[str] = None
    image_url: Optional[str] = None
    color: Optional[str] = None


@dataclass
class Composition:
    """Represents a composition object in Slack's Block Kit."""

    type: str
    text: Optional[str] = None
    emoji: Optional[bool] = None


@dataclass
class Element:
    """Represents a block element within Slack's Block Kit."""

    type: str


@dataclass
class Block:
    """Represents a layout block within Slack's Block Kit."""

    type: str


@dataclass
class SectionBlock(Block):
    """Represents a section block."""

    text: Optional[Composition] = None
    fields: Optional[list[Composition]] = None
    accessory: Optional[Element] = None


@dataclass
class ActionsBlock(Block):
    """Represents an actions block."""

    elements: list[Element] = field(default_factory=list)


@dataclass
class ContextBlock(Block):
    """Represents a context block."""

    elements: list[Element] = field(default_factory=list)


@dataclass
class DividerBlock(Block):
    """Represents a divider block."""


@dataclass
class ImageBlock(Block):
    """Represents an image block."""

    image_url: str
    alt_text: str
    title: Optional[Composition] = None


# Define other specific block types as needed...


@dataclass
class Message:
    """Represents a Slack message, including its content, author, and any associated interactive elements."""

    user: Optional[User]
    ts: str  # Raw timestamp string from Slack
    thread_ts: Optional[
        str
    ]  # Raw thread timestamp string from Slack, if part of a thread
    ts_display: str  # Human-readable timestamp
    thread_ts_display: Optional[
        str
    ]  # Human-readable thread timestamp, if part of a thread
    markdown: str  # The main body text of the message, formatted with mrkdwn
    reactions: list[Reaction] = field(default_factory=list)  # Reactions to the message
    files: list[File] = field(default_factory=list)  # Files shared in the message
    attachments: list[Attachment] = field(
        default_factory=list
    )  # Legacy secondary attachments
    blocks: list[Block] = field(default_factory=list)  # Blocks of rich layout
    parent_user_id: Optional[str] = (
        None  # User ID of the parent message's author if this is a reply
    )
    is_bot: bool = False  # Indicates if the message was sent by a bot
    replies: list["Message"] = field(default_factory=list)  # Replies in a thread


@dataclass
class ChannelHistory:
    """Historical messages and threads for a Slack channel."""

    channel: Channel
    top_level_messages: list[Message]


@dataclass
class TextStyle:
    """Represents the style attributes of text in a rich text element."""

    bold: Optional[bool] = None
    italic: Optional[bool] = None
    strike: Optional[bool] = None
    code: Optional[bool] = None


@dataclass
class ButtonElement(Element):
    """Represents a button element within Slack's Block Kit."""

    text: str
    value: str
    action_id: str
    # You can add more fields specific to the button element as needed


@dataclass
class ImageElement(Element):
    """Represents an image element within Slack's Block Kit."""

    image_url: str
    alt_text: str
    # Additional fields for image elements can be added here


@dataclass
class SelectOption:
    """Represents an option within a select menu."""

    text: str
    value: str


# Refining StaticSelectElement to use SelectOption


@dataclass
class StaticSelectElement(Element):
    """Represents a static select menu element within Slack's Block Kit."""

    placeholder: str
    options: list[SelectOption]
    action_id: str


@dataclass
class RichTextElement:
    """Base class for rich text elements."""

    type: str


@dataclass
class RichTextStyle:
    """Represents the style attributes of text in a rich text element."""

    bold: Optional[bool] = None
    italic: Optional[bool] = None
    strike: Optional[bool] = None
    code: Optional[bool] = None
    highlight: Optional[bool] = None
    client_highlight: Optional[bool] = None
    unlink: Optional[bool] = None


@dataclass
class RichTextSectionElement(RichTextElement):
    """Represents a section element within a rich text block."""

    elements: list[RichTextElement] = field(default_factory=list)
    style: Optional[RichTextStyle] = None


@dataclass
class RichTextListElement(RichTextElement):
    """Represents a list element within a rich text block."""

    style: str  # "bullet" or "ordered"
    elements: list[RichTextSectionElement] = field(default_factory=list)
    indent: Optional[int] = None
    offset: Optional[int] = None
    border: Optional[int] = None


@dataclass
class RichTextPreformattedElement(RichTextElement):
    """Represents a preformatted text element within a rich text block."""

    text: str
    border: Optional[int] = None


@dataclass
class RichTextQuoteElement(RichTextElement):
    """Represents a quote element within a rich text block."""

    text: str
    border: Optional[int] = None


@dataclass
class RichTextTextElement(RichTextElement):
    """Represents a text element within a rich text block."""

    text: str
    style: Optional[RichTextStyle] = None


@dataclass
class RichTextChannelElement(RichTextElement):
    """Represents a channel mention in a rich text element."""

    channel_id: str
    style: Optional[RichTextStyle] = None


@dataclass
class RichTextUserElement(RichTextElement):
    """Represents a user mention in a rich text element."""

    user_id: str
    style: Optional[RichTextStyle] = None


@dataclass
class RichTextUserGroupElement(RichTextElement):
    """Represents a user group mention in a rich text element."""

    user_group_id: str
    style: Optional[RichTextStyle] = None


@dataclass
class RichTextEmojiElement(RichTextElement):
    """Represents an emoji in a rich text element."""

    emoji_name: str


@dataclass
class RichTextLinkElement(RichTextElement):
    """Represents a hyperlink in a rich text element."""

    url: str
    text: Optional[str] = None
    unsafe: Optional[bool] = None
    style: Optional[RichTextStyle] = None


# Define a Union type for all possible rich text elements
RichTextElementType = Union[
    RichTextSectionElement,
    RichTextListElement,
    RichTextPreformattedElement,
    RichTextQuoteElement,
    RichTextTextElement,
    RichTextChannelElement,
    RichTextUserElement,
    RichTextUserGroupElement,
    RichTextEmojiElement,
    RichTextLinkElement,
]


@dataclass
class RichTextBlock(Block):
    """Represents a rich text block."""

    elements: list[RichTextElement] = field(default_factory=list)
