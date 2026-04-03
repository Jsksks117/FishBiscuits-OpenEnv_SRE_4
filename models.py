# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the SRE Agent Environment.

The SRE Agent environment simulates a broken Linux server inside a Docker
container. The agent sends bash commands and receives terminal output.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class SreAgentAction(Action):
    """Agent sends a bash command to execute in the Ubuntu sandbox."""

    command: str = Field(
        ..., description="Bash command to execute in the Ubuntu sandbox container"
    )


class SreAgentObservation(Observation):
    """Environment returns terminal output and task context."""

    task_id: str = Field(default="", description="Current task identifier")
    task_description: str = Field(
        default="", description="Human-readable description of what needs to be fixed"
    )
    terminal_output: str = Field(
        default="", description="stdout/stderr from the last executed command"
    )
    current_step: int = Field(
        default=0, description="Current step number in this episode"
    )
    max_steps: int = Field(
        default=20, description="Maximum allowed steps for this episode"
    )
