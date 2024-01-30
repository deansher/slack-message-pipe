"""Defines an intermediate language of python data structures between the Slack history import
and the formatted export."""

# MIT License
#
# Copyright (c) 2024 Dean Thompson

import datetime
from dataclasses import dataclass, field
from typing import List, Optional


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
    """Represents an attachment to a Slack message, which may include text, fields, and other elements.
    Per Slack's API documentation, attachments are deprecated in favor of blocks."""

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
    """
    Represents a composition object in Slack's Block Kit, which defines text, options,
    or other interactive features within certain blocks and block elements. This can
    include simple text objects, confirm dialogs, option structures, and more.
    """

    type: str
    text: Optional[str] = None
    emoji: Optional[bool] = None


@dataclass
class Element:
    """
    Represents a block element within Slack's Block Kit, which can be an interactive
    component such as a button, menu, or text input. Elements are used within blocks
    to add interactivity and structure to the messages, modals, or other surfaces.
    """

    type: str
    text: Optional[Composition] = None
    value: Optional[str] = None
    action_id: Optional[str] = None


@dataclass
class Block:
    """
    Represents a layout block within Slack's Block Kit, which structures the content
    and presentation of messages and other surfaces. Blocks can be of various types
    like section, divider, image, actions, context, and more, and can contain text,
    fields, and interactive elements.
    """

    type: str
    text: Optional[Composition] = None
    fields: Optional[List[Composition]] = None
    accessory: Optional[Element] = None
    elements: Optional[List[Element]] = None


@dataclass
class Message:
    """Represents a Slack message, including its content, author, and any associated interactive elements."""

    user: Optional[User]
    ts: datetime.datetime
    text: str
    reactions: List[Reaction] = field(default_factory=list)
    files: List[File] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)
    thread_ts: Optional[str] = None
    parent_user_id: Optional[str] = None
    is_bot: bool = False


@dataclass
class Thread:
    """Represents a thread of messages in Slack, starting with a parent message and including replies."""

    parent: Message
    replies: List[Message] = field(default_factory=list)


@dataclass
class ChannelExportData:
    """Encapsulates all data for a Slack channel export, including messages and threads."""

    channel: Channel
    messages: List[Message]
    threads: List[Thread] = field(default_factory=list)
