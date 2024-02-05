"""Slack message transformers for slack-message-pipe."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

import re

from slack_message_pipe.locales import LocaleHelper
from slack_message_pipe.slack_service import SlackService


class SlackTextConverter:
    """A class for parsing and transforming Slack text into standard markdown."""

    def __init__(
        self,
        slack_service: SlackService,
        locale_helper: LocaleHelper,
    ) -> None:
        self._slack_service = slack_service
        self._locale_helper = locale_helper

    def convert_slack_text(self, text: str, is_markdown: bool) -> str:
        """Convert Slack-specific markdown into standard markdown if is_markdown, else return text unchanged.

        Args:
            text: The text string to be converted.
            is_markdown: Whether the text is markdown.

        Returns:
            The converted text.
        """
        result = text
        if not is_markdown:
            return result

        # Transform Slack-specific markdown with brackets
        result = re.sub(r"<(.*?)>", self._replace_markdown_in_text, result)

        # Transform other Slack-specific markdown elements
        # Bold
        result = re.sub(r"\*(.+?)\*", r"**\1**", result)
        # Italic
        result = re.sub(r"\b_(.+?)_\b", r"_\1_", result)
        # Code
        result = re.sub(r"`(.+?)`", r"`\1`", result)
        # Blockquotes
        result = re.sub(r"^>(.+)", r"> \1", result, flags=re.MULTILINE)
        # Newlines are already markdown compatible

        return result

    def _replace_markdown_in_text(self, match_obj: re.Match) -> str:
        """Returns replacement string for re.sub to resolve Slack-specific markdown."""
        match = match_obj.group(1)

        if match.startswith("@U") or match.startswith("@W"):
            return self._process_user_id(match[1:])

        elif match.startswith("#C"):
            return self._process_channel_id(match[1:])

        elif match.startswith("!subteam^"):
            return self._process_user_group_id(match)

        elif match.startswith("!"):
            return self._process_special_mention(match)

        else:
            return self._process_url(match)

    def _process_user_id(self, user_id: str) -> str:
        """Transforms a user ID into a markdown mention."""
        user_name = self._slack_service.user_names().get(user_id, f"user_{user_id}")
        return f"@{user_name}"

    def _process_channel_id(self, channel_id: str) -> str:
        """Transforms a channel ID into a markdown channel name."""
        channel_name = self._slack_service.channel_names().get(
            channel_id, f"channel_{channel_id}"
        )
        return f"#{channel_name}"

    def _process_user_group_id(self, usergroup_match: str) -> str:
        """Transforms a user group mention into a markdown user group name."""
        usergroup_id = usergroup_match.split("^")[1]
        usergroup_name = self._slack_service.usergroup_names().get(
            usergroup_id, f"usergroup_{usergroup_id}"
        )
        return f"@{usergroup_name}"

    def _process_special_mention(self, special_mention: str) -> str:
        """Transforms special mentions into plain text."""
        if special_mention == "!here":
            return "@here"
        elif special_mention == "!channel":
            return "@channel"
        elif special_mention == "!everyone":
            return "@everyone"
        elif special_mention.startswith("!date^"):
            date_id = special_mention.split("^")[1]
            # TODO: was self._locale_helper.get_datetime_formatted_str(date_id), but what should it be?
            return date_id
        else:
            return f"@{special_mention}"

    def _process_url(self, url_match: str) -> str:
        """Transforms a URL into a markdown link."""
        parts = url_match.split("|")
        if len(parts) == 2:
            url, text = parts
        else:
            url = text = parts[0]
        return f"[{text}]({url})"
