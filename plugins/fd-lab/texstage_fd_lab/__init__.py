# SPDX-License-Identifier: Apache-2.0
"""Installed FD engine and classroom lessons; metadata discovery stays import-free."""
from texstage.plugin_api.v1 import PluginV1


def create_plugin():
    from .authoring import prepare_lesson
    from .state import Lesson
    return PluginV1(authoring_hooks={"exercise": prepare_lesson}, state_hooks={"exercise": Lesson()})
