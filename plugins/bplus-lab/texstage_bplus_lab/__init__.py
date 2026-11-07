# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""B+ operation engine and prepared lessons and classroom submissions."""
from texstage.plugin_api.v1 import PluginV1


def create_plugin():
    from .authoring import prepare_lesson
    from .state import Lesson
    return PluginV1(authoring_hooks={"tree": prepare_lesson}, state_hooks={"tree": Lesson()})
