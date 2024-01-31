"""Defines an intermediate language of python data structures between the Slack history import
and the formatted export."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Union


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
    user_ids: List[str]


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
    text: str
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
    fields: Optional[List[Composition]] = None
    accessory: Optional[Element] = None


@dataclass
class ActionsBlock(Block):
    """Represents an actions block."""

    elements: List[Element] = field(default_factory=list)


@dataclass
class ContextBlock(Block):
    """Represents a context block."""

    elements: List[Element] = field(default_factory=list)


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
    text: str  # The main body text of the message, can be formatted with mrkdwn
    reactions: List[Reaction] = field(default_factory=list)  # Reactions to the message
    files: List[File] = field(default_factory=list)  # Files shared in the message
    attachments: List[Attachment] = field(
        default_factory=list
    )  # Legacy secondary attachments
    blocks: List[Block] = field(default_factory=list)  # Blocks of rich layout
    parent_user_id: Optional[
        str
    ] = None  # User ID of the parent message's author if this is a reply
    is_bot: bool = False  # Indicates if the message was sent by a bot
    replies: List["Message"] = field(default_factory=list)  # Replies in a thread


@dataclass
class ChannelExportData:
    """Encapsulates all data for a Slack channel export, including messages and threads."""

    channel: Channel
    top_level_messages: List[Message]


# ... existing code ...


@dataclass
class TextStyle:
    """Represents the style attributes of text in a rich text element."""

    bold: Optional[bool] = None
    italic: Optional[bool] = None
    strike: Optional[bool] = None
    code: Optional[bool] = None


@dataclass
class RichTextElement:
    """Base class for rich text elements."""

    type: str


@dataclass
class RichTextSectionElement(RichTextElement):
    """Represents a section element within a rich text block."""

    text: str
    style: Optional[TextStyle] = None


@dataclass
class RichTextListElement(RichTextElement):
    """Represents a list element within a rich text block."""

    style: str  # "bullet" or "ordered"
    elements: List[RichTextSectionElement] = field(default_factory=list)


@dataclass
class RichTextPreformattedElement(RichTextElement):
    """Represents a preformatted text element within a rich text block."""

    text: str


@dataclass
class RichTextQuoteElement(RichTextElement):
    """Represents a quote element within a rich text block."""

    text: str


@dataclass
class RichTextChannelElement(RichTextElement):
    """Represents a channel mention in a rich text element."""

    channel_id: str


@dataclass
class RichTextUserElement(RichTextElement):
    """Represents a user mention in a rich text element."""

    user_id: str


@dataclass
class RichTextUserGroupElement(RichTextElement):
    """Represents a user group mention in a rich text element."""

    user_group_id: str


@dataclass
class RichTextEmojiElement(RichTextElement):
    """Represents an emoji in a rich text element."""

    emoji_name: str


@dataclass
class RichTextLinkElement(RichTextElement):
    """Represents a hyperlink in a rich text element."""

    url: str
    text: Optional[str] = None


# Define a Union type for all possible rich text elements
RichTextElementType = Union[
    RichTextSectionElement,
    RichTextListElement,
    RichTextPreformattedElement,
    RichTextQuoteElement,
    RichTextChannelElement,
    RichTextUserElement,
    RichTextUserGroupElement,
    RichTextEmojiElement,
    RichTextLinkElement,
]


@dataclass
class RichTextBlock(Block):
    """Represents a rich text block."""

    elements: List[RichTextElementType] = field(default_factory=list)
