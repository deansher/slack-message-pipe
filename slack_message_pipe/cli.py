"""Command line interface."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

import argparse
import datetime as dt
import logging
import logging.config
import os
import sys
import zoneinfo
from pathlib import Path
from pprint import pformat
from typing import Optional

import dateutil.parser
from babel import Locale, UnknownLocaleError
from dateutil.tz import gettz
from slack_sdk.errors import SlackApiError
from tzlocal import get_localzone

from slack_message_pipe import __version__, settings

# Import the new SlackDataFormatter
from slack_message_pipe.channel_history_export import ChannelHistoryExporter
from slack_message_pipe.format_as_markdown import Config, format_as_markdown
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

    output_file_extension = "md" if args.command == "markdown" else "txt"
    for channel_id in args.channel_id:
        channel_history = formatter.fetch_and_format_channel_data(
            channel_id=channel_id,
            oldest=oldest,
            latest=latest,
            max_messages=args.max_messages,
        )
        datetime_format = "%Y%m%d_%H%M"
        oldest_str = oldest.strftime(datetime_format)
        latest_str = latest.strftime(datetime_format)
        output_path = Path(
            f"{channel_history.channel.name}_{oldest_str}_to_{latest_str}.{output_file_extension}"
        )
        try:
            if args.command == "pprint":
                pretty_print(channel_history, output_path)
            elif args.command == "markdown":
                markdown_output = format_as_markdown(
                    channel_history, Config(images=args.images)
                )
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_output)
            else:
                print(f"ERROR: Unknown command '{args.command}'")
                sys.exit(1)
        except IOError as e:
            print(f"ERROR: Failed to write to {output_path}: {e}")
            continue

        if not args.quiet:
            print(f"Wrote data for channel {channel_id} to {output_path}")


def _parse_args(args: list[str]) -> argparse.Namespace:
    """
    Defines and parses command-line arguments.

    Args:
        args: A list of command-line arguments, excluding the program name.

    Returns:
        An argparse.Namespace object containing the parsed command-line arguments.
    """
    my_arg_parser = argparse.ArgumentParser(
        description=(
            "A tool for reading a Slack channel's message history and converting it to various formats.\n"
            "The output is written to a file with the same name as the channel and the date range.\n"
            "\n"
            'Example: slack-message-pipe markdown "2024-01-01 00:00" now C0423S252BH\n\n'
            "For more information, see the README: https://github.com/dean-thompson/slack-message-pipe"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # main arguments
    my_arg_parser.add_argument(
        "command",
        help="Action to take on the data",
        choices=["pprint", "markdown"],
    )
    my_arg_parser.add_argument(
        "oldest",
        help=(
            "Oldest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone]\n"
            "Defaults to this processe's timezone. (It is an error if no timezone is specified and the process's timezone is not known.)\n"
        ),
    )
    my_arg_parser.add_argument(
        "latest",
        help=(
            "Latest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone] or 'now'\n"
            "Defaults to this process's timezone. (It is an error if no timezone is specified and the user's timezone is not known.)\n"
            "If not provided, will process messages up to the current time.\n"
        ),
    )
    my_arg_parser.add_argument(
        "channel_id", help="One or several: ID of channel to export.", nargs="+"
    )
    my_arg_parser.add_argument(
        "--token",
        help="Slack OAuth token. Can instead be provided in the environment variable SLACK_TOKEN.",
    )

    my_arg_parser.add_argument(
        "--images", action="store_true", help="Include images in the markdown output"
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


def _parse_slack_token(args: argparse.Namespace) -> str:
    """
    Retrieves the Slack token from command-line arguments or environment variables.

    Args:
        args: Parsed command-line arguments.

    Returns:
        The Slack token as a string.

    Raises:
        SystemExit: If no Slack token is provided either as an argument or in the environment.
    """
    if args.token is None:
        if "SLACK_TOKEN" in os.environ:
            slack_token = os.environ["SLACK_TOKEN"]
        else:
            print("ERROR: No slack token provided")
            sys.exit(1)
    else:
        slack_token = args.token
    return slack_token


def _parse_formatter_timezone(args: argparse.Namespace) -> Optional[zoneinfo.ZoneInfo]:
    """
    Parses and returns the formatter timezone specified in the command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        A zoneinfo.ZoneInfo object representing the specified timezone, or None if not specified.

    Raises:
        SystemExit: If an unknown or invalid timezone is specified.
    """
    if args.formatter_timezone is not None:
        try:
            tz = zoneinfo.ZoneInfo(args.formatter_timezone)
        except ValueError:
            print("ERROR: Unknown timezone")
            sys.exit(1)
    else:
        tz = None
    return tz


def _parse_formatter_locale(args: argparse.Namespace) -> Optional[Locale]:
    """
    Parses and returns the formatter locale specified in the command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        A babel.Locale object representing the specified locale, or None if not specified.

    Raises:
        SystemExit: If an unknown or invalid locale is specified.
    """
    if args.formatter_locale is not None:
        try:
            locale = Locale.parse(args.formatter_locale, sep="-")
        except UnknownLocaleError:
            print("ERROR: provided locale string is not valid")
            sys.exit(1)
    else:
        locale = None
    return locale


def _parse_datetime_argument(
    cli_datetime_str: Optional[str], process_timezone: Optional[dt.tzinfo] = None
) -> dt.datetime:
    """
    Parses a date-time string from the CLI, considering optional timezone information and special values.

    This function supports a special value "now" to represent the current datetime. If the input string is "now",
    the function returns the current datetime with the timezone set to the process's timezone or the sp ecified
    timezone. For other inputs, it attempts to parse the string into a datetime object, applying the specified
    or process's timezone if no timezone information is included in the string.

    Args:
        cli_datetime_str: The date-time string to parse, potentially including a timezone offset or name, or the
                          special value "now". Returns the current time if this argument is None.
        process_timezone: The timezone to use if no timezone is specified in the string or for the "now" value.
                          Defaults to the process's timezone.

    Returns:
        A timezone-aware datetime object representing the specified datetime, the current datetime if "now" is
        specified, or None if cli_datetime_str is None.

    Raises:
        ValueError: If the date-time string is invalid, the specified timezone is invalid, no timezone is specified
                    and the process's timezone is not known, or if the process's timezone cannot be determined for
                    the "now" value.
    """
    if cli_datetime_str is None or cli_datetime_str.lower() == "now":
        return dt.datetime.now(tz=process_timezone)

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


def pretty_print(formatted_data: ChannelHistory, dest_path: Path) -> None:
    """
    Pretty-prints the Python intermediate data structures to a file.

    Args:
        formatted_data: The data structure containing the channel history to be printed.
        dest_path: The file path where the pretty-printed data will be written.

    Raises:
        IOError: If an error occurs during file writing.
    """
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(pformat(formatted_data))
        f.write("\n")


if __name__ == "__main__":
    main()
