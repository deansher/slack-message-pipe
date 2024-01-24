#!/usr/bin/env python
# -*- coding: utf-8 -*-

"FPDF for python"

__license__ = "LGPL 3.0"
__version__ = "1.7.2"

from slack_message_pipe.fpdf_mod.fpdf import (
    FPDF,
    FPDF_CACHE_DIR,
    FPDF_CACHE_MODE,
    FPDF_FONT_DIR,
    FPDF_VERSION,
    SYSTEM_TTFONTS,
    set_global,
)

try:
    from slack_message_pipe.fpdf_mod.html import HTMLMixin
except ImportError:
    import warnings

    warnings.warn("web2py gluon package not installed, required for html2pdf")

from slack_message_pipe.fpdf_mod.template import Template
