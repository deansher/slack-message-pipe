"""Command line interface."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

import argparse
import logging
import logging.config
import os
import sys
import zoneinfo
from pathlib import Path
from pprint import pformat

from babel import Locale, UnknownLocaleError
from dateutil import parser
from slack_sdk.errors import SlackApiError

from slack_message_pipe import __version__, settings

# Import the new SlackDataFormatter
from slack_message_pipe.channel_history_export import ChannelHistoryExporter
from slack_message_pipe.intermediate_data import ChannelHistory
from slack_message_pipe.locales import LocaleHelper
from slack_message_pipe.slack_service import SlackService
from slack_message_pipe.slack_text_converter import SlackTextConverter

logging.config.dictConfig(settings.DEFAULT_LOGGING)


def main():
    """Implements the arg parser and starts the data formatting with its input"""

    args = _parse_args(sys.argv[1:])
    slack_token = _parse_slack_token(args)
    my_tz = _parse_local_timezone(args)
    my_locale = _parse_locale(args)
    oldest = _parse_oldest(args)
    latest = _parse_latest(args)

    if not args.quiet:
        channel_postfix = "s" if args.channel_id and len(args.channel_id) > 1 else ""
        print(f"Formatting data for channel{channel_postfix} from Slack...")

    try:
        slack_service = SlackService(
            slack_token=slack_token, locale_helper=LocaleHelper(my_locale, my_tz)
        )
        message_to_markdown = SlackTextConverter(
            slack_service=slack_service,
            locale_helper=LocaleHelper(my_locale, my_tz),
        )
        formatter = ChannelHistoryExporter(
            slack_service=slack_service,
            locale_helper=LocaleHelper(my_locale, my_tz),
            slack_text_converter=message_to_markdown,
        )
    except SlackApiError as ex:
        print(f"ERROR: {ex}")
        sys.exit(1)

    for channel_id in args.channel_id:
        channel_history = formatter.fetch_and_format_channel_data(
            channel_id=channel_id,
            oldest=oldest,
            latest=latest,
            max_messages=args.max_messages,
        )
        pretty_print(
            channel_history,
            Path(args.output if args.output else f"{channel_history.channel.name}.txt"),
        )
        if not args.quiet:
            print(f"Wrote data for channel {channel_id} to {args.output}")


def _parse_args(args: list[str]) -> argparse.Namespace:
    """Defines the argument parser and returns parsed result from given argument"""
    my_arg_parser = argparse.ArgumentParser(
        description="Pulls a Slack channel's history and converts it to Python data structures.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # main arguments
    my_arg_parser.add_argument(
        "command",
        help="Action to take on the data",
        choices=["pprint"],
    )
    my_arg_parser.add_argument(
        "channel_id", help="One or several: ID of channel to export.", nargs="+"
    )
    my_arg_parser.add_argument("--token", help="Slack OAuth token")
    my_arg_parser.add_argument(
        "--oldest",
        help="Oldest timestamp from which to load messages; format: YYYY-MM-DD HH:MM",
    )
    my_arg_parser.add_argument(
        "--latest",
        help="Latest timestamp from which to load messages; format: YYYY-MM-DD HH:MM",
    )

    # Output file
    my_arg_parser.add_argument(
        "-o",
        "--output",
        help="Specify an output file path.",
        default="channel_data.txt",
    )

    # Timezone and locale
    my_arg_parser.add_argument(
        "--timezone",
        help=(
            "Manually set the timezone to be used e.g. 'Europe/Berlin'. "
            "Use a timezone name as defined here: "
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        ),
    )
    my_arg_parser.add_argument(
        "--locale",
        help=(
            "Manually set the locale to be used with a IETF language tag, "
            "e.g. 'de-DE' for Germany. "
            "See this page for a list of valid tags: "
            "https://en.wikipedia.org/wiki/IETF_language_tag"
        ),
    )

    # standards
    my_arg_parser.add_argument(
        "--version",
        help="Show the program version and exit",
        action="version",
        version=__version__,
    )

    # exporter config
    my_arg_parser.add_argument(
        "--max-messages",
        help="Max number of messages to export",
        type=int,
        default=settings.MAX_MESSAGES_PER_CHANNEL,
    )

    my_arg_parser.add_argument(
        "--quiet",
        action="store_const",
        const=True,
        default=False,
        help="When provided will not generate normal console output, but still show errors",
    )
    return my_arg_parser.parse_args(args)


def _parse_slack_token(args):
    """Try to take slack token from optional argument or environment variable."""
    if args.token is None:
        if "SLACK_TOKEN" in os.environ:
            slack_token = os.environ["SLACK_TOKEN"]
        else:
            print("ERROR: No slack token provided")
            sys.exit(1)
    else:
        slack_token = args.token
    return slack_token


def _parse_local_timezone(args):
    if args.timezone is not None:
        try:
            my_tz = zoneinfo.ZoneInfo(args.timezone)
        except ValueError:
            print("ERROR: Unknown timezone")
            sys.exit(1)
    else:
        my_tz = None
    return my_tz


def _parse_locale(args):
    if args.locale is not None:
        try:
            my_locale = Locale.parse(args.locale, sep="-")
        except UnknownLocaleError:
            print("ERROR: provided locale string is not valid")
            sys.exit(1)
    else:
        my_locale = None
    return my_locale


def _parse_oldest(args):
    if args.oldest is not None:
        try:
            oldest = parser.parse(args.oldest)
        except ValueError:
            print("ERROR: Invalid date input for --oldest")
            sys.exit(1)
    else:
        oldest = None
    return oldest


def _parse_latest(args):
    if args.latest is not None:
        try:
            latest = parser.parse(args.latest)
        except ValueError:
            print("ERROR: Invalid date input for --latest")
            sys.exit(1)
    else:
        latest = None
    return latest


def pretty_print(formatted_data: ChannelHistory, dest_path: Path):
    """Pretty-prints the Python intermediate data structures to a file."""
    with open(dest_path, "w", encoding="utf-16") as f:
        f.write(pformat(formatted_data))
        f.write("\n")


if __name__ == "__main__":
    main()
