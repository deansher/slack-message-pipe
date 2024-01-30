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
    """Represents an attachment to a Slack message, which may include text, fields, and other elements."""

    fallback: str
    text: str
    pretext: Optional[str] = None
    title: Optional[str] = None
    title_link: Optional[str] = None
    author_name: Optional[str] = None
    fields: Optional[List[str]] = None
    footer: Optional[str] = None
    image_url: Optional[str] = None
    color: Optional[str] = None


@dataclass
class Block:
    """Represents a layout block within a Slack message, which structures the content and presentation."""

    type: str
    text: Optional[str] = None
    elements: Optional[List[str]] = None
    accessory: Optional[dict] = None


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
