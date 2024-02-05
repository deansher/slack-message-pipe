# MIT License
#
# Copyright (c) 2019 Erik Kalkoken

import json
import socket
from pathlib import Path
from typing import Any, Optional
from unittest import TestCase

SlackResponseData = dict[str, Any]


class SocketAccessError(Exception):
    pass


class NoSocketsTestCase(TestCase):
    """Enhancement of TestCase class that prevents any use of sockets

    Will throw the exception SocketAccessError when any code tries to
    access network sockets
    """

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


def chunks(lst, size):
    """Yield successive sized chunks from lst."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def slack_response_data(
    data: Optional[dict[str, Any]], ok: bool = True, error: Optional[str] = None
) -> SlackResponseData:
    if not ok:
        return {"ok": False, "error": error}
    else:
        return {"ok": True, **(data or {})}


class SlackResponseStub:
    def __init__(self, data: Optional[dict], ok: bool = True) -> None:
        self.data = slack_response_data(data, ok)


class SlackClientStub:
    def __init__(self, team: str, page_size: Optional[int] = None) -> None:
        self._team = str(team)
        self._page_size = page_size
        self._page_counts = {"conversations_list": 0}
        path = Path(__file__).parent / "slack_data.json"
        with path.open("r", encoding="utf-8") as f:
            self._slack_data = json.load(f)

    def _paging(self, data, key, cursor: Optional[int] = None) -> SlackResponseData:
        if not self._page_size:
            return slack_response_data({key: data})
        else:
            data_chunks = list(chunks(data, self._page_size))
            if cursor is None:
                cursor = 0

            response = {key: data_chunks[cursor]}
            if len(data_chunks) > cursor + 1:
                response["response_metadata"] = {"next_cursor": cursor + 1}

            return slack_response_data(response)

    def auth_test(self) -> SlackResponseStub:
        return SlackResponseStub(self._slack_data[self._team]["auth_test"])

    def bots_info(self, bot) -> SlackResponseData:
        return slack_response_data({}, ok=False)

    def conversations_replies(
        self,
        channel,
        ts,
        limit: Optional[int] = None,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        cursor: Optional[int] = None,
    ) -> SlackResponseData:
        if (
            channel in self._slack_data[self._team]["conversations_replies"]
            and ts in self._slack_data[self._team]["conversations_replies"][channel]
        ):
            messages = self._slack_data[self._team]["conversations_replies"][channel][
                ts
            ]
            return slack_response_data(self._messages_to_response(messages))
        else:
            return slack_response_data(None, ok=False, error="Thread not found")

    def conversations_history(
        self,
        channel,
        limit: Optional[int] = None,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        cursor: Optional[int] = None,
    ) -> SlackResponseData:
        if channel in self._slack_data[self._team]["conversations_history"]:
            messages = self._slack_data[self._team]["conversations_history"][channel]
            return self._paging(messages, "messages", cursor)
        else:
            return slack_response_data(None, ok=False, error="Channel not found")

    @staticmethod
    def _messages_to_response(messages: list) -> dict:
        return {"messages": messages, "has_more": False}

    def conversations_list(
        self, types, limit: Optional[int] = None, cursor: Optional[int] = None
    ) -> dict:
        return self._paging(
            self._slack_data[self._team]["conversations_list"]["channels"],
            "channels",
            cursor,
        )

    def users_info(
        self, user, include_locale: Optional[bool] = None
    ) -> SlackResponseData:
        users = {
            obj["id"]: obj
            for obj in self._slack_data[self._team]["users_list"]["members"]
        }
        if user in users:
            return slack_response_data({"user": users[user]})
        else:
            return slack_response_data(None, ok=False, error="User not found")

    def users_list(self, limit: Optional[int] = None) -> SlackResponseData:
        return slack_response_data(self._slack_data[self._team]["users_list"])

    def usergroups_list(self) -> SlackResponseData:
        return slack_response_data(self._slack_data[self._team]["usergroups_list"])
