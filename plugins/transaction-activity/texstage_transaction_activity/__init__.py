# SPDX-License-Identifier: Apache-2.0
"""Installed factory; discovery reads metadata without importing this module."""
def create_plugin():
    from texstage.plugin_api.v1 import PluginV1
    from .authoring import prepare_lesson
    from .state import Lesson
    return PluginV1(authoring_hooks={'schedule':prepare_lesson},state_hooks={'schedule':Lesson()})
