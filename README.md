# slack-message-pipe

**slack_message_pipe** is a library for reading a Slack channel's message history as simple Python data structures. This has many benefits over Slack's API when formatting channel history for human or LLM consumption:

- We stitch data from multiple API calls into a single data structure. For example, our `Message` object contains user and channel names instead of IDs.
- We convert Slack's special markdown into standard markdown.
- We provide the output as simple, typed Python objects that you and your IDE can understand.

We intend to enhance this package also process the live message flow as activity proceeds in a set of Slack channels or threads.

[![release](https://img.shields.io/pypi/v/slack-message-pipe?label=release)](https://pypi.org/project/slack-message-pipe/)
[![python](https://img.shields.io/pypi/pyversions/slack-message-pipe)](https://pypi.org/project/slack-message-pipe/)
[![license](https://img.shields.io/github/license/deansher/slack-message-pipe)](https://github.com/deansher/slack-message-pipe/blob/master/LICENSE)
[![Tests](https://github.com/deansher/slack-message-pipe/actions/workflows/main.yml/badge.svg)](https://github.com/deansher/slack-message-pipe/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/deansher/slack-message-pipe/branch/master/graph/badge.svg?token=omhTxW8ALq)](https://codecov.io/gh/deansher/slack-message-pipe)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This project began as a clone of [ErikKalkoken / slackchannel2pdf](https://github.com/ErikKalkoken/slackchannel2pdf). We transformed that code to produce Python data structures instead of PDF files. We have no way to test on Windows, so we have dropped that support.

## Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Token](#token)
- [Usage](#usage)
- [Arguments](#arguments)
- [Configuration](#configuration)
- [Limitations](#limitations)

## Overview

**slack-message-pipe** is open source under the MIT license. See `./LICENSE`.
We use Flit for package management and distribution.

## Installation

### Python

This package is compatible with Python 3.10 and 3.11.

You can install the tool from PyPI with `pip install`:

```bash
pip install slack-message-pipe
```

You can then run the tool with the command `slack-message-pipe` as explained in detail under [Usage](#usage).

## Token

To run **slack-message-pipe**, you need to have a token for your Slack workspace with the following permissions:

- `channels:history`
- `channels:read`
- `groups:history`
- `groups:read`
- `users:read`
- `usergroups:read`

Here is one way to do that:

1. Create a new Slack app in your workspace (you can give it any name).
1. Under Oauth & Permissions / User Token Scopes add all the required scopes as documented above.
1. Install the app into your workspace

After successful installation the token for your app will then shown under Basic Information / App Credentials.

## Usage

Currently, the cli is just for testing. It exports the data as pretty printed python data structures.

You can provide the Slack token either as command line argument `--token` or by setting the environment variable `SLACK_TOKEN`.

```text
Logging to file: slack_message_pipe.log
usage: slack-message-pipe [-h] [--token TOKEN] [--formatter_timezone FORMATTER_TIMEZONE] [--formatter_locale FORMATTER_LOCALE] [--version]
                          [--max-messages MAX_MESSAGES] [--quiet]
                          {pprint,markdown} oldest latest channel_id [channel_id ...]

A tool for reading a Slack channel's message history and converting it to various formats.
The output is written to a file with the same name as the channel and the date range.

Example: slack-message-pipe markdown "2024-01-01 00:00" now C0423S252BH

For more information, see the README: https://github.com/dean-thompson/slack-message-pipe

positional arguments:
  {pprint,markdown}     Action to take on the data
  oldest                Oldest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone]
                        Defaults to this processe's timezone. (It is an error if no timezone is specified and the process's timezone is not known.)
  latest                Latest timestamp from which to load messages; format: YYYY-MM-DD HH:MM [timezone] or 'now'
                        Defaults to this process's timezone. (It is an error if no timezone is specified and the user's timezone is not known.)
                        If not provided, will process messages up to the current time.
  channel_id            One or several: ID of channel to export.

options:
  -h, --help            show this help message and exit
  --token TOKEN         Slack OAuth token. Can instead be provided in the environment variable SLACK_TOKEN.
  --formatter_timezone FORMATTER_TIMEZONE
                        Manually set the timezone to be used for formatting dates and times, such as 'Europe/Berlin'. Use a timezone name as defined here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zonesDefaults to the process timezone.
  --formatter_locale FORMATTER_LOCALE
                        Manually set the locale to be used for formatting, with a IETF language tag, e.g. 'de-DE' for Germany. See this page for a list of valid tags: https://en.wikipedia.org/wiki/IETF_language_tag . Defaults to the process locale.
  --version             Show the program version and exit
  --max-messages MAX_MESSAGES
                        Max number of messages to export
  --quiet               When provided will not generate normal console output, but still show errors
```

## Configuration

You can configure many defaults and behaviors via configuration files. Configuration files must have the name `slack_message_pipe.ini` and can be placed in two locations:

- home directory (home)
- current working directory (cwd)

You can also have a configuration file in both. Settings in cwd will overwrite the same settings in home. And calling this app with command line arguments will overwrite the corresponding configuration setting.

Please see the [master configuration file](https://github.com/deansher/slack-message-pipe/blob/master/slack_message_pipe/slack_message_pipe.ini) for a list of all available configuration sections, options, and the current defaults.

## Limitations

- Text only: **slack-message-pipe** will export only text from a channel, but not images or icons.
- No Emojis: the tools is currently not able to write emojis as icons will will use their text representation instead (e.g. `:laughing:` instead of :laughing:).
- DMs, Group DM: Currently not supported
- Limited blocks support:Some non-text features of layout blocks not yet supported
- Limited script support: This tool is rendering all PDF text with the [Google Noto Sans](https://www.google.com/get/noto/#sans-lgc) font and will therefore support all 500+ languages that are support by that font. It does however not support many Asian languages / scripts like Chinese, Japanese, Korean, Thai and others.
