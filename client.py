# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""SRE Agent Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from models import SreAgentAction, SreAgentObservation


class SreAgentEnv(
    EnvClient[SreAgentAction, SreAgentObservation, State]
):
    """
    Client for the SRE Agent Environment.

    This client maintains a persistent WebSocket connection to the environment server.
    """

    def _step_payload(self, action: SreAgentAction) -> Dict:
        """
        Convert SreAgentAction to JSON payload for step message.
        """
        return {
            "command": action.command,
        }

    def _parse_result(self, payload: Dict) -> StepResult[SreAgentObservation]:
        """
        Parse server response into StepResult[SreAgentObservation].
        """
        obs_data = payload.get("observation", {})
        observation = SreAgentObservation(
            task_id=obs_data.get("task_id", ""),
            task_description=obs_data.get("task_description", ""),
            terminal_output=obs_data.get("terminal_output", ""),
            current_step=obs_data.get("current_step", 0),
            max_steps=obs_data.get("max_steps", 20),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
