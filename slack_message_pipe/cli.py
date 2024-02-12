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

import dateutil.parser
from babel import Locale, UnknownLocaleError
from dateutil.tz import gettz
from slack_sdk.errors import SlackApiError
from tzlocal import get_localzone

from slack_message_pipe import __version__, settings

# Import the new SlackDataFormatter
from slack_message_pipe.channel_history_export import ChannelHistoryExporter
from slack_message_pipe.format_as_markdown import format_as_markdown
from slack_message_pipe.intermediate_data import ChannelHistory
from slack_message_pipe.locales import LocaleHelper
from slack_message_pipe.slack_service import SlackService
from slack_message_pipe.slack_text_converter import SlackTextConverter

logging.config.dictConfig(settings.DEFAULT_LOGGING)


def main():
    """Implements the arg parser and starts the data formatting with its input"""

    args = _parse_args(sys.argv[1:])
    slack_token = _parse_slack_token(args)
    formatter_timezone = _parse_formatter_timezone(args)
    formatter_locale = _parse_formatter_locale(args)
    oldest = _parse_datetime_argument(args.oldest)
    latest = _parse_datetime_argument(args.latest)

    if not args.quiet:
        channel_postfix = "s" if args.channel_id and len(args.channel_id) > 1 else ""
        print(f"Formatting data for channel{channel_postfix} from Slack...")

    try:
        slack_service = SlackService(
            slack_token=slack_token,
            locale_helper=LocaleHelper(formatter_locale, formatter_timezone),
        )
        message_to_markdown = SlackTextConverter(
            slack_service=slack_service,
            locale_helper=LocaleHelper(formatter_locale, formatter_timezone),
        )
        formatter = ChannelHistoryExporter(
            slack_service=slack_service,
            locale_helper=LocaleHelper(formatter_locale, formatter_timezone),
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
        if args.command == "pprint":
            pretty_print(
                channel_history,
                Path(
                    args.output
                    if args.output
                    else f"{channel_history.channel.name}.txt"
                ),
            )
        elif args.command == "markdown":
            markdown_output = format_as_markdown(channel_history)
            output_path = (
                args.output if args.output else f"{channel_history.channel.name}.md"
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_output)
        else:
            print(f"ERROR: Unknown command '{args.command}'")
            sys.exit(1)

        if not args.quiet:
            print(f"Wrote data for channel {channel_id} to {args.output}")


def _parse_args(args: list[str]) -> argparse.Namespace:
    """Defines the argument parser and returns parsed result from given argument"""
    my_arg_parser = argparse.ArgumentParser(
        description="Pulls a Slack channel's history and converts it to various formats.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # main arguments
    my_arg_parser.add_argument(
        "command",
        help="Action to take on the data",
        choices=["pprint", "markdown"],
    )
    my_arg_parser.add_argument(
        "channel_id", help="One or several: ID of channel to export.", nargs="+"
    )
    my_arg_parser.add_argument("--token", help="Slack OAuth token")
    my_arg_parser.add_argument(
        "--oldest",
        help=(
            "Oldest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone]\n"
            "Defaults to this processe's timezone. (It is an error if no timezone is specified and the process's timezone is not known.)\n"
            "If not provided, will start with the oldest message in the channel.\n"
        ),
    )
    my_arg_parser.add_argument(
        "--latest",
        help=(
            "Latest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone]\n"
            "Defaults to this process's timezone. (It is an error if no timezone is specified and the user's timezone is not known.)\n"
            "If not provided, will start with the latest message in the channel.\n"
        ),
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
        "--formatter_timezone",
        help=(
            "Manually set the timezone to be used for formatting dates and times, such as 'Europe/Berlin'. "
            "Use a timezone name as defined here: "
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
            "Defaults to the process timezone. "
        ),
    )
    my_arg_parser.add_argument(
        "--formatter_locale",
        help=(
            "Manually set the locale to be used for formatting, with a IETF language tag, "
            "e.g. 'de-DE' for Germany. "
            "See this page for a list of valid tags: "
            "https://en.wikipedia.org/wiki/IETF_language_tag . "
            "Defaults to the process locale. "
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


def _parse_formatter_timezone(args):
    if args.formatter_timezone is not None:
        try:
            tz = zoneinfo.ZoneInfo(args.formatter_timezone)
        except ValueError:
            print("ERROR: Unknown timezone")
            sys.exit(1)
    else:
        tz = None
    return tz


def _parse_formatter_locale(args):
    if args.formatter_locale is not None:
        try:
            locale = Locale.parse(args.formatter_locale, sep="-")
        except UnknownLocaleError:
            print("ERROR: provided locale string is not valid")
            sys.exit(1)
    else:
        locale = None
    return locale


def _parse_datetime_argument(cli_datetime_str, process_timezone=None):
    """
    Parses a date-time string from the CLI, taking into account optional timezone information.
    Attempts to discover the process's timezone if no none is specified in the string nor as `process_timezone`.

    Args:
        cli_datetime_str: The date-time string to parse, potentially including a timezone offset or name.
                          If None, returns None to indicate the use of the channel's oldest or latest message.
        process_timezone: The timezone to use if no timezone is specified in the string. (Defaults to the process's timezone.)

    Returns:
        A timezone-aware datetime object, or None if cli_datetime_str is None.

    Raises:
        ValueError: If the date-time string is invalid, the timezone is invalid, or no timezone is specified
                  and the process's timezone is not known.
    """
    if cli_datetime_str is None:
        return None

    if process_timezone is None:
        process_timezone = get_localzone()
        if process_timezone is None:
            raise ValueError(
                "No timezone specified and the process timezone is not known."
            )

    # Extract potential timezone information from the string
    timezone_str = None
    datetime_parts = cli_datetime_str.rsplit(" ", 1)
    if len(datetime_parts) == 2:
        possible_timezone_str = datetime_parts[1]
        if (
            possible_timezone_str == "Z"
            or "+" in possible_timezone_str
            or "-" in possible_timezone_str
            or gettz(possible_timezone_str)
        ):
            timezone_str = possible_timezone_str
            cli_datetime_str = datetime_parts[0]
        else:
            cli_datetime_str = " ".join(
                datetime_parts
            )  # No valid timezone found, treat as part of datetime

    # Parse the date-time without timezone information
    try:
        datetime_obj = dateutil.parser.parse(cli_datetime_str)
    except ValueError as e:
        raise ValueError(f"Invalid date-time format: {cli_datetime_str}") from e

    # Apply timezone information
    if timezone_str:
        if timezone_str == "Z":
            timezone_str = "UTC"
        timezone = gettz(timezone_str)
        if timezone:
            datetime_obj = datetime_obj.replace(tzinfo=timezone)
        else:
            raise ValueError(f"Invalid timezone: {timezone_str}")
    else:
        # Apply the process timezone if no timezone is specified in the input
        datetime_obj = datetime_obj.replace(tzinfo=process_timezone)

    return datetime_obj


def pretty_print(formatted_data: ChannelHistory, dest_path: Path):
    """Pretty-prints the Python intermediate data structures to a file."""
    with open(dest_path, "w", encoding="utf-16") as f:
        f.write(pformat(formatted_data))
        f.write("\n")


if __name__ == "__main__":
    main()
