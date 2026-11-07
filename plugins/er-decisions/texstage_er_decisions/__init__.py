# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""ER registration engine and prepared-authoring provider."""
from texstage.plugin_api.v1 import PluginV1


def create_plugin():
    from .authoring import prepare_lesson
    from .state import Lesson
    return PluginV1(authoring_hooks={"lesson": prepare_lesson}, state_hooks={"lesson": Lesson()})
