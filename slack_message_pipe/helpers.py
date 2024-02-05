"""Helpers for slack-message-pipe."""

# MIT License
#
# Copyright (c) 2019 Erik Kalkoken
# Copyright (c) 2024 Dean Thompson

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_array_from_json_file(filepath: Path, quiet=False) -> list:
    """reads a json file and returns its contents as array"""
    my_file = filepath.parent / (filepath.name + ".json")
    if not my_file.is_file():
        if quiet is False:
            logger.warning("file does not exist: %s", filepath)
        return []
    try:
        with my_file.open("r", encoding="utf-8") as file:
            return json.load(file)
    except IOError:
        if quiet is False:
            logger.warning("failed to read from %s: ", my_file, exc_info=True)
        return []


def write_array_to_json_file(arr, filepath: Path) -> None:
    """writes array to a json file"""
    my_file = filepath.parent / (filepath.name + ".json")
    logger.info("Writing file: %s", filepath)
    try:
        with my_file.open("w", encoding="utf-8") as file:
            json.dump(arr, file, sort_keys=True, indent=4, ensure_ascii=False)
    except IOError:
        logger.error("failed to write to %s", my_file, exc_info=True)
