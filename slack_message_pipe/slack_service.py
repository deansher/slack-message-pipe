"""Logic for handling Slack API."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

import datetime
import logging
from pprint import pformat
from typing import Optional, TypedDict, cast

import slack_sdk
from babel.numbers import format_decimal

from slack_message_pipe import settings
from slack_message_pipe.locales import LocaleHelper

logger = logging.getLogger(__name__)


class SlackMessage(TypedDict, total=False):
    """Represents a message as returned by the Slack API."""

    type: str
    bot_id: str
    user: str
    username: Optional[str]
    text: str
    ts: str
    thread_ts: Optional[str]
    reactions: list[dict]
    files: list[dict]
    attachments: list[dict]
    blocks: list[dict]
    mrkdwn: bool
    # Include other fields as needed


class SlackService:
    """Service layer between main app and Slack API"""

    def __init__(
        self, slack_token: str, locale_helper: Optional[LocaleHelper] = None
    ) -> None:
        """
        Initialize SlackService with a Slack token and an optional locale helper.

        Args:
            slack_token: Slack token to use for all API calls.
            locale_helper: Locale helper instance for localization.
        """
        if slack_token is None:
            raise ValueError("slack_token can not be null")

        self._client = slack_sdk.WebClient(token=slack_token)
        if not locale_helper:
            locale_helper = LocaleHelper()
        self._locale = locale_helper.locale
        self._workspace_info = self._fetch_workspace_info()
        logger.info("Current Slack workspace: %s", self.team)
        self._user_names = self.fetch_user_names()

        if "user_id" in self._workspace_info:
            author_id = self._workspace_info["user_id"]
            self._author = self._user_names.get(author_id, f"unknown_user_{author_id}")
        else:
            author_id = None
            self._author = "unknown user"

        logger.info("Current Slack user: %s", self.author)
        self._channel_names = self._fetch_channel_names()
        self._usergroup_names = self._fetch_usergroup_names()

        self._author_info = self._fetch_user_info(author_id) if author_id else {}

    @property
    def author(self) -> str:
        """Return the author."""
        return self._author

    @property
    def team(self) -> str:
        """Return the team name."""
        return self._workspace_info.get("team", "")

    def author_info(self) -> dict:
        """Return author information."""
        return self._author_info

    def channel_names(self) -> dict[str, str]:
        """Return channel names."""
        return self._channel_names

    def user_names(self) -> dict[str, str]:
        """Return user names."""
        return self._user_names

    def usergroup_names(self) -> dict[str, str]:
        """Return usergroup names."""
        return self._usergroup_names

    def _fetch_workspace_info(self) -> dict:
        """Fetch and return information about the current workspace."""
        logger.info("Fetching workspace info from Slack...")
        response = self._client.auth_test()
        try:
            result = response.data
            assert isinstance(
                result, dict
            ), f"expected res.data to be dict, got {type(result)}"
            return result
        except AttributeError:
            raise RuntimeError(
                "Could not fetch workspace info from Slack; response was:"
                + pformat(response)
            )

    def fetch_user_names(self) -> dict[str, str]:
        """Fetch and return a dictionary mapping user IDs to user names."""
        user_names_raw = self._fetch_pages(
            "users_list", key="members", items_name="users"
        )
        user_names = self._reduce_to_dict(user_names_raw, "id", "real_name", "name")
        return {user: name for user, name in user_names.items()}

    def _fetch_user_info(self, user_id: str) -> dict:
        """Fetch and return information for a given user ID, including locale."""
        logger.info("Fetching user info for %s...", user_id)
        response = self._client.users_info(user=user_id, include_locale=True)
        return response["user"]

    def _fetch_channel_names(self) -> dict[str, str]:
        """Fetch and return a dictionary mapping channel IDs to channel names."""
        channel_names_raw = self._fetch_pages(
            "conversations_list",
            key="channels",
            args={"types": "public_channel,private_channel"},
            items_name="channels",
        )
        return {
            channel: name
            for channel, name in self._reduce_to_dict(
                channel_names_raw, "id", "name"
            ).items()
        }

    def _fetch_usergroup_names(self) -> dict[str, str]:
        """Fetch and return a dictionary mapping usergroup IDs to usergroup names."""
        logger.info("Fetching usergroups from Slack...")
        response = self._client.usergroups_list()
        usergroup_names = self._reduce_to_dict(response["usergroups"], "id", "handle")
        result = {usergroup: name for usergroup, name in usergroup_names.items()}
        logger.info(
            "Got a total of %s usergroups for this workspace",
            format_decimal(len(usergroup_names), locale=self._locale),
        )
        return result

    def fetch_messages_from_channel(
        self,
        channel_id: str,
        max_messages: Optional[int] = None,
        oldest: Optional[datetime.datetime] = None,
        latest: Optional[datetime.datetime] = None,
    ) -> list[SlackMessage]:
        """Fetch and return messages from a Slack channel."""
        oldest_ts = str(oldest.timestamp()) if oldest else None
        latest_ts = str(latest.timestamp()) if latest else None
        messages = self._fetch_pages(
            "conversations_history",
            key="messages",
            args={
                "channel": channel_id,
                "oldest": oldest_ts,
                "latest": latest_ts,
            },
            max_rows=max_messages,
            items_name="messages",
            collection_name="channel",
        )
        return messages  # type: ignore

    def fetch_threads_by_ts(
        self,
        channel_id: str,
        top_level_slack_messages: list[SlackMessage],
        max_thread_messages: Optional[int] = None,
        oldest: Optional[datetime.datetime] = None,
        latest: Optional[datetime.datetime] = None,
    ) -> dict[str, list[SlackMessage]]:
        """
        Fetch and return threads from messages for a channel.
        Returns a dict of thread_ts: messages, where the messages are in chronological order.
        """
        max_thread_messages = max_thread_messages or settings.MAX_MESSAGES_PER_THREAD
        threads = {}
        for msg in top_level_slack_messages:
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                thread_messages = self._fetch_messages_from_thread(
                    channel_id, thread_ts, max_thread_messages, oldest, latest
                )
                threads[thread_ts] = thread_messages

        return threads

    def _fetch_messages_from_thread(
        self,
        channel_id: str,
        thread_ts: str,
        max_messages: int,
        oldest: Optional[datetime.datetime] = None,
        latest: Optional[datetime.datetime] = None,
    ) -> list[SlackMessage]:
        """Fetch and return messages from a Slack thread."""
        oldest_ts = str(oldest.timestamp()) if oldest else None
        latest_ts = str(latest.timestamp()) if latest else None
        messages = self._fetch_pages(
            "conversations_replies",
            key="messages",
            args={
                "channel": channel_id,
                "ts": thread_ts,
                "oldest": oldest_ts,
                "latest": latest_ts,
            },
            max_rows=max_messages,
            items_name="threads",
            collection_name="channel",
        )
        return messages  # type: ignore

    def _fetch_pages(
        self,
        method: str,
        key: str,
        args: Optional[dict] = None,
        limit: Optional[int] = None,
        max_rows: Optional[int] = None,
        items_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        print_result: bool = True,
    ) -> list[dict]:
        """Helper function for retrieving all pages from an API endpoint."""
        page = 1
        output_str = (
            f"Fetching {items_name if items_name else method} "
            f"from {collection_name if collection_name else 'workspace'}..."
        )
        logger.info(output_str)
        args = args or {}
        limit = limit or settings.SLACK_PAGE_LIMIT
        base_args = {**args, "limit": limit}
        response = getattr(self._client, method)(**base_args)
        rows = response[key]

        while (
            (not max_rows or len(rows) < max_rows)
            and response.get("response_metadata")
            and response["response_metadata"].get("next_cursor")
        ):
            page += 1
            logger.info("%s - page %s", output_str, page)
            page_args = {
                **base_args,
                "cursor": response["response_metadata"].get("next_cursor"),
            }
            response = getattr(self._client, method)(**page_args)
            rows += response[key]

        if print_result:
            logger.info(
                "Received %s %s",
                format_decimal(len(rows), locale=self._locale),
                items_name if items_name else "objects",
            )
        return rows

    def fetch_bot_names_for_messages(
        self, messages: list[SlackMessage], threads: dict[str, list[SlackMessage]]
    ) -> dict[str, str]:
        """Fetches bot names from API for provided messages

        Will only fetch names for bots that never appeared with a username
        in any message (lazy approach since calls to bots_info are very slow)
        """
        # collect bot_ids without user name from messages
        bot_ids = []
        bot_names = {}
        for msg in messages:
            if "bot_id" in msg:
                bot_id = msg["bot_id"]
                username_from_message = msg.get("username")
                if username_from_message:
                    bot_names[bot_id] = username_from_message
                else:
                    bot_ids.append(bot_id)

        # collect bot_ids without user name from thread messages
        for thread_messages in threads.values():
            for msg in thread_messages:
                if "bot_id" in msg:
                    username_from_message = msg.get("username")
                    if username_from_message:
                        bot_names[bot_id] = username_from_message
                    else:
                        bot_ids.append(bot_id)

        # Find bot IDs that are not in bot_names
        bot_ids = list(set(bot_ids).difference(bot_names.keys()))

        # collect bot names from API if needed
        if len(bot_ids) > 0:
            logger.info("Fetching names for %d bots", len(bot_ids))
            for bot_id in bot_ids:
                response = self._client.bots_info(bot=bot_id)
                if response["ok"]:
                    bot_names[bot_id] = response["bot"]["name"]
        return bot_names

    @staticmethod
    def _reduce_to_dict(
        arr: list[dict],
        key_name: str,
        col_name_primary: str,
        col_name_secondary: Optional[str] = None,
    ) -> dict[str, str]:
        """returns dict with selected columns as key and value from list of dict

        Args:
            arr: list of dicts to reduce
            key_name: name of column to become key
            col_name_primary: colum will become value if it exists
            col_name_secondary: colum will become value if col_name_primary
                does not exist and this argument is provided

        dict items with no matching key_name, col_name_primary and
        col_name_secondary will not be included in the resulting new dict

        """
        result = {}
        for item in arr:
            if key_name in item:
                key = item[key_name]
                if col_name_primary in item:
                    result[key] = item[col_name_primary]
                elif col_name_secondary and col_name_secondary in item:
                    result[key] = item[col_name_secondary]
        return result
