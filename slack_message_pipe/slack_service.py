"""Logic for handling Slack API."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken

import logging
from typing import Optional

import slack_sdk
from babel.numbers import format_decimal

from slack_message_pipe import settings
from slack_message_pipe.helpers import transform_encoding
from slack_message_pipe.locales import LocaleHelper

logger = logging.getLogger(__name__)


class SlackService:
    """Service layer between main app and Slack API"""

    def __init__(
        self, slack_token: str, locale_helper: Optional[LocaleHelper] = None
    ) -> None:
        """
        Args:
        - slack_token: Slack token to use for all API calls
        - locale_helper: locale to use
        """
        if slack_token is None:
            raise ValueError("slack_token can not be null")

        # load information for current Slack workspace
        self._client = slack_sdk.WebClient(token=slack_token)
        if not locale_helper:
            locale_helper = LocaleHelper()
        self._locale = locale_helper.locale
        self._workspace_info = self._fetch_workspace_info()
        logger.info("Current Slack workspace: %s", self.team)
        self._user_names = self.fetch_user_names()

        # set author
        if "user_id" in self._workspace_info:
            author_id = self._workspace_info["user_id"]
            if author_id in self._user_names:
                self._author = self._user_names[author_id]
            else:
                self._author = f"unknown_user_{author_id}"
        else:
            author_id = None
            self._author = "unknown user"

        logger.info("Current Slack user: %s", self.author)
        self._channel_names = self._fetch_channel_names()
        self._usergroup_names = self._fetch_usergroup_names()

        if author_id is not None:
            self._author_info = self._fetch_user_info(author_id)
        else:
            self._author_info = {}

    @property
    def author(self) -> str:
        """Return author."""
        return self._author

    @property
    def team(self) -> str:
        """Return team."""
        return self._workspace_info.get("team", "")

    def author_info(self) -> dict:
        """Return author info."""
        return self._author_info

    def channel_names(self) -> dict:
        """Return channel names."""
        return self._channel_names

    def user_names(self) -> dict:
        """Return user names."""
        return self._user_names

    def usergroup_names(self) -> dict:
        """Return usergroup names."""
        return self._usergroup_names

    def _fetch_workspace_info(self) -> dict:
        """returns dict with info about current workspace"""

        logger.info("Fetching workspace info from Slack...")
        res = self._client.auth_test()
        return res.data  # type: ignore

    def fetch_user_names(self) -> dict:
        """returns dict of user names with user ID as key"""
        user_names_raw = self._fetch_pages(
            "users_list", key="members", items_name="users"
        )
        user_names = self._reduce_to_dict(user_names_raw, "id", "real_name", "name")
        for user in user_names:
            user_names[user] = transform_encoding(user_names[user])
        return user_names

    def _fetch_user_info(self, user_id: str) -> dict:
        """returns dict of user info for user ID incl. locale"""
        logger.info("Fetching user info for author...")
        response = self._client.users_info(user=user_id, include_locale=True)
        return response["user"]

    def _fetch_channel_names(self) -> dict:
        """returns dict of channel names with channel ID as key"""
        channel_names_raw = self._fetch_pages(
            "conversations_list",
            key="channels",
            args={"types": "public_channel,private_channel"},
            items_name="channels",
        )
        channel_names = self._reduce_to_dict(channel_names_raw, "id", "name")
        for channel in channel_names:
            channel_names[channel] = transform_encoding(channel_names[channel])
        return channel_names

    def _fetch_usergroup_names(self) -> dict:
        """returns dict of usergroup names with usergroup ID as key"""

        logger.info("Fetching usergroups from Slack...")
        response = self._client.usergroups_list()
        usergroup_names = self._reduce_to_dict(response["usergroups"], "id", "handle")
        if usergroup_names:
            for usergroup in usergroup_names:
                usergroup_names[usergroup] = transform_encoding(
                    usergroup_names[usergroup]
                )
            logger.info(
                "Got a total of %s usergroups for this workspace",
                format_decimal(len(usergroup_names), locale=self._locale),
            )
        else:
            logger.info("This workspace has no usergroups")
        return usergroup_names

    def fetch_messages_from_channel(
        self, channel_id, max_messages, oldest=None, latest=None
    ) -> list:
        """retrieve messages from a channel on Slack and return as list"""

        oldest_ts = str(oldest.timestamp()) if oldest is not None else 0
        latest_ts = str(latest.timestamp()) if latest is not None else 0
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
        return messages

    def fetch_threads_from_messages(
        self, channel_id, messages, max_messages, oldest=None, latest=None
    ) -> dict:
        """returns threads from all messages from for a channel as dict"""
        threads = {}
        thread_num = 0
        thread_messages_total = 0
        for msg in messages:
            if "thread_ts" in msg and msg["thread_ts"] == msg["ts"]:
                thread_ts = msg["thread_ts"]
                thread_num += 1
                thread_messages = self._fetch_messages_from_thread(
                    channel_id, thread_ts, max_messages, oldest, latest
                )
                threads[thread_ts] = thread_messages
                thread_messages_total += len(thread_messages)

        if thread_messages_total:
            logger.info(
                "Received %s messages from %d threads",
                format_decimal(thread_messages_total, locale=self._locale),
                thread_num,
            )
        else:
            logger.info("This channel has no threads")

        return threads

    def _fetch_messages_from_thread(
        self, channel_id, thread_ts, max_messages, oldest=None, latest=None
    ) -> list:
        """retrieve messages from a Slack thread and return as list"""
        oldest_ts = str(oldest.timestamp()) if oldest is not None else 0
        latest_ts = str(latest.timestamp()) if latest is not None else 0
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
            print_result=False,
        )
        return messages

    def _fetch_pages(
        self,
        method,
        key: str,
        args: Optional[dict] = None,
        limit: Optional[int] = None,
        max_rows: Optional[int] = None,
        items_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        print_result: bool = True,
    ) -> list:
        """helper for retrieving all pages from an API endpoint"""
        # fetch first page
        page = 1
        output_str = (
            f"Fetching {items_name if items_name else method} "
            f"from {collection_name if collection_name else 'workspace'}..."
        )
        logger.info(output_str)
        if not args:
            args = {}
        if not limit:
            limit = settings.SLACK_PAGE_LIMIT
        base_args = {**args, **{"limit": limit}}
        response = getattr(self._client, method)(**base_args)
        rows = response[key]

        # fetch additional page (if any)
        while (
            (not max_rows or len(rows) < max_rows)
            and response.get("response_metadata")
            and response["response_metadata"].get("next_cursor")
        ):
            page += 1
            logger.info("%s - page %s", output_str, page)
            page_args = {
                **base_args,
                **{
                    "cursor": response["response_metadata"].get("next_cursor"),
                },
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

    def fetch_bot_names_for_messages(self, messages: list, threads: dict) -> dict:
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
                if "username" in msg:
                    bot_names[bot_id] = transform_encoding(msg["username"])
                else:
                    bot_ids.append(bot_id)

        # collect bot_ids without user name from thread messages
        for thread_messages in threads.values():
            for msg in thread_messages:
                if "bot_id" in msg:
                    bot_id = msg["bot_id"]
                    if "username" in msg:
                        bot_names[bot_id] = transform_encoding(msg["username"])
                    else:
                        bot_ids.append(bot_id)

        # Find bot IDs that are not in bot_names
        bot_ids = set(bot_ids).difference(bot_names.keys())

        # collect bot names from API if needed
        if len(bot_ids) > 0:
            logger.info("Fetching names for %d bots", len(bot_ids))
            for bot_id in bot_ids:
                response = self._client.bots_info(bot=bot_id)
                if response["ok"]:
                    bot_names[bot_id] = transform_encoding(response["bot"]["name"])
        return bot_names

    @staticmethod
    def _reduce_to_dict(
        arr: list,
        key_name: str,
        col_name_primary: str,
        col_name_secondary: Optional[str] = None,
    ) -> dict:
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
        arr2 = {}
        for item in arr:
            if key_name in item:
                key = item[key_name]
                if col_name_primary in item:
                    arr2[key] = item[col_name_primary]
                elif col_name_secondary is not None and col_name_secondary in item:
                    arr2[key] = item[col_name_secondary]
        return arr2