"""Global settings incl. from configuration files for slack-message-pipe."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

# pylint: disable = no-member

import configparser
from ast import literal_eval
from pathlib import Path
from typing import Any, Optional, TypedDict, cast

_FILE_NAME_BASE = "slack_message_pipe"
_CONF_FILE_NAME = f"{_FILE_NAME_BASE}.ini"
_LOG_FILE_NAME = f"{_FILE_NAME_BASE}.log"

_DEFAULTS_PATH = Path(__file__).parent


def _configparser_convert_str(value: str) -> str:
    result = literal_eval(value)
    if not isinstance(result, str):
        raise configparser.ParsingError(f"Needs to be a string type: {value}")
    return result


def config_parser(
    defaults_path: Path,
    home_path: Optional[Path] = None,
    cwd_path: Optional[Path] = None,
) -> configparser.ConfigParser:
    """Load and parse config from file and return it."""
    parser = configparser.ConfigParser(converters={"str": _configparser_convert_str})
    config_file_paths = [defaults_path / _CONF_FILE_NAME]
    if home_path:
        config_file_paths.append(home_path / _CONF_FILE_NAME)
    if cwd_path:
        config_file_paths.append(cwd_path / _CONF_FILE_NAME)
    found = parser.read(config_file_paths)
    if not found:
        raise RuntimeError("Can not find a configuration file anywhere")
    return parser


_my_config = config_parser(
    defaults_path=_DEFAULTS_PATH, home_path=Path.home(), cwd_path=Path.cwd()
)

# locale
FALLBACK_LOCALE = _my_config.getstr("locale", "fallback_locale")  # type: ignore

# slack
MAX_MESSAGES_PER_CHANNEL = _my_config.getint("slack", "max_messages_per_channel")
MAX_MESSAGES_PER_THREAD = _my_config.getint("slack", "max_messages_per_thread")
SLACK_PAGE_LIMIT = _my_config.getint("slack", "slack_page_limit")


class FormatterInfo(TypedDict):
    """
    Represents the structure of formatter configurations for logging.

    Attributes:
        format (str): The string format to be used by the logging formatter.
    """

    format: str


# Define HandlerInfo using the functional syntax because of the reserved word 'class'
HandlerInfo = TypedDict(
    "HandlerInfo",
    {
        "level": str,
        "formatter": str,
        "class": str,
        "stream": Optional[str],
        "filename": Optional[str | Path],
        "mode": Optional[str],
    },
    total=False,
)

HandlerInfo.__doc__ = """
Represents the structure of handler configurations for logging.

This TypedDict is defined using the functional syntax to allow for the reserved word 'class' to be used as a key.

Attributes:
    level (str): The log level for the handler.
    formatter (str): The name of the formatter to be used by this handler.
    class (str): The class name of the handler to be instantiated.
    stream (Optional[str]): The stream to be used by the StreamHandler.
    filename (Optional[str | Path]): The filename to be used by the FileHandler.
    mode (Optional[str]): The file mode (e.g., 'a' for append) to be used by the FileHandler.
"""


class LoggerInfo(TypedDict):
    """
    Represents the structure of logger configurations for logging.

    Attributes:
        handlers (list[str]): A list of handler names that are associated with the logger.
        level (str): The log level for the logger.
        propagate (bool): Indicates whether the log messages should propagate to the parent logger.
    """

    handlers: list[str]
    level: str
    propagate: bool


class LoggingConfig(TypedDict):
    """
    Represents the overall structure of the logging configuration.

    Attributes:
        version (int): The configuration schema version, typically set to 1.
        disable_existing_loggers (bool): Whether to disable existing loggers upon initialization of the configuration.
        formatters (dict[str, FormatterInfo]): A mapping of formatter names to their configurations.
        handlers (dict[str, HandlerInfo]): A mapping of handler names to their configurations.
        loggers (dict[str, LoggerInfo]): A mapping of logger names to their configurations.
    """

    version: int
    disable_existing_loggers: bool
    formatters: dict[str, FormatterInfo]
    handlers: dict[str, HandlerInfo]
    loggers: dict[str, LoggerInfo]


def _setup_logging(config: configparser.ConfigParser) -> LoggingConfig:
    config_logging: LoggingConfig = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"format": "[%(levelname)s] %(message)s"},
            "file": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "level": config.getstr("logging", "console_log_level"),  # type: ignore
                "formatter": "console",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            }
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # add log file if configured
    log_file_enabled = config.getboolean("logging", "log_file_enabled", fallback=False)
    if log_file_enabled:
        file_log_path_full = config.getstr("logging", "log_file_path", fallback=None)  # type: ignore
        filename = (
            Path(file_log_path_full) / _LOG_FILE_NAME
            if file_log_path_full
            else _LOG_FILE_NAME
        )
        print("Logging to file:", filename, flush=True)
        config_logging["handlers"]["file"] = {
            "level": config.getstr("logging", "file_log_level"),  # type: ignore
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": str(filename),
            "mode": "a",
        }
        config_logging["loggers"][""]["handlers"].append("file")
    return config_logging


DEFAULT_LOGGING = cast(dict[str, Any], _setup_logging(_my_config))
