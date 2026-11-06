# SPDX-License-Identifier: Apache-2.0
"""Installed engine and prepared lesson; discovery never calls the factory."""
from texstage.plugin_api.v1 import PluginV1


def create_plugin():
    from .authoring import prepare_lesson
    from .state import Lesson
    return PluginV1(authoring_hooks={"tree": prepare_lesson}, state_hooks={"tree": Lesson()})
