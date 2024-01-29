# slack-message-pipe

**slack_message_pipe** is a command line tool for exporting the text contents of any Slack channel to a PDF or JSON file.
As of this writing, we only support PDF. JSON is next. Perhaps more later.

[![release](https://img.shields.io/pypi/v/slack-message-pipe?label=release)](https://pypi.org/project/slack-message-pipe/)
[![python](https://img.shields.io/pypi/pyversions/slack-message-pipe)](https://pypi.org/project/slack-message-pipe/)
[![license](https://img.shields.io/github/license/deansher/slack-message-pipe)](https://github.com/deansher/slack-message-pipe/blob/master/LICENSE)
[![Tests](https://github.com/deansher/slack-message-pipe/actions/workflows/main.yml/badge.svg)](https://github.com/deansher/slack-message-pipe/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/deansher/slack-message-pipe/branch/master/graph/badge.svg?token=omhTxW8ALq)](https://codecov.io/gh/deansher/slack-message-pipe)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This project began as a clone of [ErikKalkoken / slackchannel2pdf](https://github.com/ErikKalkoken/slackchannel2pdf). Our initial goal is to format a Slack channel's message history nicely as JSON for consumption by an LLM. We have to do quite a bit of cleanup of the JSON that comes back from Slack's API to make it simple, self contained, and easy to interpret. Erik already wrote that logic in his project. It's just that his output is PDF, while ours needs to be JSON.

Our approach is to insert an intermediate language of simple python data structures between the Slack history processing and the PDF generation. Then we will add an adapter to go from that intermediate language to JSON when desired.

We have no way to test on Windows, so we have dropped that support.

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

**slack-message-pipe** is an open source project and offered free of charge and under the MIT license. Please check attached licence file for details.

## Features

Here is a short summary of the key features of **slack-message-pipe**:

- Export of any public and private Slack channel to a PDF  or JSON file (text only)
- Automatic detection of timezone and locale based from Slack. Can also be set manually if needed.
- Exporting support for all Slack features incl. threads and layout blocks
- Ability to export only the portion of a channel for a specific time period
- Ability to configure page layout of PDF file (e.g. Portrait vs. Landscape)
- Many defaults and behaviors can be configured with configuration files

## Installation

### Python

You can install the tool from PyPI with `pip install`. This will require you to have Python reinstalled in your machine and it will work with any OS supported by Python. We recommend installing it into a virtual environment like venv.

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

To get a working token, you need to create a Slack app in your workspace with a user token. Here is one way on how to do that:

1. Create a new Slack app in your workspace (you can give it any name).
1. Under Oauth & Permissions / User Token Scopes add all the required scopes as documented above.
1. Install the app into your workspace

After successful installation the token for your app will then shown under Basic Information / App Credentials.

## Usage

In order to use **slack-message-pipe** you need:

1. have it installed on your system (see [Installation](#installation))
2. have a Slack token for the respective Slack workspace with the required permissions (see [Token](#token)).

Here are some examples on how to use **slack-message-pipe**:

To export the Slack channel "general" as PDF:

```bash
slack-message-pipe --token MY_TOKEN --format pdf general
```

To export the Slack channels "general", "random" and "test":

```bash
slack-message-pipe --token MY_TOKEN --format pdf general random test
```

To export all message from channel "general" starting from July 5th, 2019 at 11:00.

```bash
slack-message-pipe --token MY_TOKEN --format pdf --oldest "2019-JUL-05 11:00" general
```

> Tip: You can provide the Slack token either as command line argument `--token` or by setting the environment variable `SLACK_TOKEN`.

## Arguments

```text
usage: slack-message-pipe [-h] [--token TOKEN]
                        --format pdf
                        [--oldest OLDEST]
                        [--latest LATEST] [-d DESTINATION]
                        [--page-orientation {portrait,landscape}]
                        [--page-format {a3,a4,a5,letter,legal}]
                        [--timezone TIMEZONE] [--locale LOCALE] [--version]
                        [--max-messages MAX_MESSAGES] [--write-raw-data]
                        [--add-debug-info] [--quiet]
                        channel [channel ...]

Exports a Slack channel's message history to a file.

positional arguments:
  format channel [channel ...] output format (currently only pdf) followed by a
                        list of channels to export

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         Slack OAuth token (default: None)
  --oldest OLDEST       don't load messages older than a date (default: None)
  --latest LATEST       don't load messages newer then a date (default: None)
  -d DESTINATION, --destination DESTINATION
                        Specify a destination path to store the PDF file.
                        (TBD) (default: .)
  --page-orientation {portrait,landscape}
                        Orientation of PDF pages (default: portrait)
  --page-format {a3,a4,a5,letter,legal}
                        Format of PDF pages (default: a4)
  --timezone TIMEZONE   Manually set the timezone to be used e.g.
                        'Europe/Berlin' Use a timezone name as defined here: h
                        ttps://en.wikipedia.org/wiki/List_of_tz_database_time_
                        zones (default: None)
  --locale LOCALE       Manually set the locale to be used with a IETF
                        language tag, e.g. ' de-DE' for Germany. See this page
                        for a list of valid tags:
                        https://en.wikipedia.org/wiki/IETF_language_tag
                        (default: None)
  --version             show the program version and exit
  --max-messages MAX_MESSAGES
                        max number of messages to export (default: 10000)
  --write-raw-data      will also write all raw data returned from the API to
                        files, e.g. messages.json with all messages (default:
                        None)
  --add-debug-info      wether to add debug info to PDF (default: False)
  --quiet               When provided will not generate normal console output,
                        but still show errors (console logging not affected
                        and needs to be configured through log levels instead)
                        (default: False)
```

## Configuration

You can configure many defaults and behaviors via configuration files. Configuration files must have the name `slack_message_pipe.ini` and can be placed in two locations:

- home directory (home)
- current working directory (cwd)

You can also have a configuration file in both. Settings in cwd will overwrite the same settings in home. And calling this app with command line arguments will overwrite the corresponding configuration setting.

Please see the master configuration file for a list of all available configuration sections, options and the current defaults. The master configuration file is `slack_message_pipe/slack_message_pipe.ini` in this repo.

## Limitations

- Text only: **slack-message-pipe** will export only text from a channel, but not images or icons.
- No Emojis: the tools is currently not able to write emojis as icons will will use their text representation instead (e.g. `:laughing:` instead of :laughing:).
- DMs, Group DM: Currently not supported
- Limited blocks support:Some non-text features of layout blocks not yet supported
- Limited script support: This tool is rendering all PDF text with the [Google Noto Sans](https://www.google.com/get/noto/#sans-lgc) font and will therefore support all 500+ languages that are support by that font. It does however not support many Asian languages / scripts like Chinese, Japanese, Korean, Thai and others.
