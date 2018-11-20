# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

import os
from textwrap import dedent

import pytest
from qtpy.QtCore import QObject, Signal, Slot

from spyder.config.main import CONF
from spyder.plugins.editor.lsp.client import LSPClient
from spyder.plugins.editor.lsp import (
    SERVER_CAPABILITES, LSPRequestTypes, LSPEventTypes)


class LSPEditor(QObject):
    sig_response_signal = Signal(str, dict)
    sig_lsp_notification = Signal(dict, str)

    @Slot(str, dict)
    def handle_response(self, method, params):
        self.sig_response_signal.emit(method, params)


@pytest.fixture
def lsp_client(qtbot):
    config = CONF.get('lsp-server', 'python')
    lsp_editor = LSPEditor()
    lsp = LSPClient(None, config['args'], config, config['external'],
                    plugin_configurations=config.get('configurations', {}),
                    language='python')
    lsp.register_plugin_type(
        LSPEventTypes.DOCUMENT, lsp_editor.sig_lsp_notification)
    # qtbot.addWidget(lsp)
    yield lsp, lsp_editor
    if os.name != 'nt':
        lsp.stop()


@pytest.mark.slow
@pytest.mark.skipif(os.name == 'nt', reason="Fails on Windows")
def test_initialization(qtbot, lsp_client):
    lsp, lsp_editor = lsp_client
    with qtbot.waitSignal(lsp_editor.sig_lsp_notification, timeout=10000) as blocker:
        lsp.start()
    options, _ = blocker.args
    assert all([option in SERVER_CAPABILITES for option in options.keys()])


@pytest.mark.slow
@pytest.mark.skipif(os.name == 'nt', reason="Fails on Windows")
def test_get_signature(qtbot, lsp_client):
    lsp, lsp_editor = lsp_client
    with qtbot.waitSignal(lsp_editor.sig_lsp_notification, timeout=10000):
        lsp.start()
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import os\nos.walk(\n",
        'codeeditor': lsp_editor,
        'requires_response': False
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    signature_params = {
        'file': 'test.py',
        'line': 1,
        'column': 10,
        'requires_response': True,
        'response_codeeditor': lsp_editor
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(
            LSPRequestTypes.DOCUMENT_SIGNATURE, signature_params)
    _, response = blocker.args
    assert response['params']['signatures']['label'].startswith('walk')


@pytest.mark.slow
@pytest.mark.skipif(os.name == 'nt', reason="Fails on Windows")
def test_get_completions(qtbot, lsp_client):
    lsp, lsp_editor = lsp_client
    with qtbot.waitSignal(lsp_editor.sig_lsp_notification, timeout=10000):
        lsp.start()
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import o",
        'codeeditor': lsp_editor,
        'requires_response': False
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    completion_params = {
        'file': 'test.py',
        'line': 0,
        'column': 8,
        'requires_response': True,
        'response_codeeditor': lsp_editor
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(
            LSPRequestTypes.DOCUMENT_COMPLETION, completion_params)
    _, response = blocker.args
    completions = response['params']
    assert 'os' in [x['label'] for x in completions]


@pytest.mark.slow
@pytest.mark.skipif(os.name == 'nt', reason="Fails on Windows")
def test_go_to_definition(qtbot, lsp_client):
    lsp, lsp_editor = lsp_client
    with qtbot.waitSignal(lsp_editor.sig_lsp_notification, timeout=10000):
        lsp.start()
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': "import os\nos.walk\n",
        'codeeditor': lsp_editor,
        'requires_response': False
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    go_to_definition_params = {
        'file': 'test.py',
        'line': 0,
        'column': 19,
        'requires_response': True,
        'response_codeeditor': lsp_editor
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(
            LSPRequestTypes.DOCUMENT_DEFINITION, go_to_definition_params)
    _, response = blocker.args
    definition = response['params']
    assert 'os.py' in definition['file']


@pytest.mark.slow
@pytest.mark.skipif(os.name == 'nt', reason="Fails on Windows")
def test_local_signature(qtbot, lsp_client):
    lsp, lsp_editor = lsp_client
    with qtbot.waitSignal(lsp_editor.sig_lsp_notification, timeout=10000):
        lsp.start()
    text = dedent('''
    def test(a, b):
        """Test docstring"""
        pass
    test''')
    open_params = {
        'file': 'test.py',
        'language': 'python',
        'version': 1,
        'text': text,
        'codeeditor': lsp_editor,
        'requires_response': False
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(LSPRequestTypes.DOCUMENT_DID_OPEN, open_params)

    signature_params = {
        'file': 'test.py',
        'line': 4,
        'column': 0,
        'requires_response': True,
        'response_codeeditor': lsp_editor
    }

    with qtbot.waitSignal(lsp_editor.sig_response_signal, timeout=10000) as blocker:
        lsp.perform_request(
            LSPRequestTypes.DOCUMENT_HOVER, signature_params)
    _, response = blocker.args
    definition = response['params']
    assert 'Test docstring' in definition
