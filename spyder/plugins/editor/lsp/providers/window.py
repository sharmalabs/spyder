# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Spyder Language Server Protocol Client window handler routines."""

import logging

from spyder.plugins.editor.lsp import LSPRequestTypes
from spyder.plugins.editor.lsp.decorators import handles

logger = logging.getLogger(__name__)


class WindowProvider:
    @handles(LSPRequestTypes.WINDOW_SHOW_MESSAGE)
    def process_show_message(self, response, *args):
        """Handle window/showMessage notifications from LSP server."""
        logger.debug("Received showMessage: %r" % response)
