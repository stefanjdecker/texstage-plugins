# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Engine-only plugin: its factory is never needed for browser evaluation."""
from texstage.plugin_api.v1 import PluginV1
def create_plugin():
    return PluginV1()
