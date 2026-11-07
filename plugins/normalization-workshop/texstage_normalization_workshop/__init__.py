# SPDX-License-Identifier: Apache-2.0
"""Normalization analyzer and prepared classroom workshop."""
from texstage.plugin_api.v1 import PluginV1
from .authoring import prepare_lesson
from .state import Workshop


def create_plugin():
    return PluginV1(authoring_hooks={"workshop": prepare_lesson}, state_hooks={"workshop": Workshop()})
