import json
from typing import Callable, Dict, Optional, Union, List
import yaml
import numpy as np
from autogen.agentchat import ConversableAgent
from intercode.envs import (
    BashEnv, SqlEnv, ACTION_EXEC
)
from autogen import Agent


class InterCodeAgent(ConversableAgent):

    def __init__(
        self,
        name: str,
        env,
        action_parser,
        max_rounds: int = 10,
        is_termination_msg=lambda x: "terminate" in x.get("content").lower(),
        max_consecutive_auto_reply: Optional[int] = None,
        human_input_mode: Optional[str] = "NEVER",
        function_map: Optional[Dict[str, Callable]] = None,
        code_execution_config: Optional[Union[Dict, bool]] = None,
        llm_config: Optional[Union[Dict, bool]] = False,
        **kwargs,
    ):
        super().__init__(
            name,
            is_termination_msg,
            max_consecutive_auto_reply,
            human_input_mode,
            function_map,
            code_execution_config,
            llm_config,
            **kwargs,
        )

        self.env = env
        self.action_parser = action_parser
        self.max_rounds = max_rounds
        self.num_rounds = 0

        self.turn_history = {
            "thoughts": [],
            "actions": [],
            "observations": [],
            "rewards": [],
            "valid_action": [],
            "states": []
        }
        self.done = 0
        self.reward = 0
        self.register_reply(Agent, InterCodeAgent.generate_env_reply)



    def generate_env_reply(self, messages=None, sender=None, config=None):
        message = messages[-1].get("content", "")

        a = message.strip().split(f"Action: ") 
        thought, action = a[0], a[1]
        action_parsed, is_code = self.action_parser(action)
        # print(action_parsed, is_code)
        if not is_code:
            reward = 0
            observation = f"Error executing query: Your last `execute` action did not contain SQL code"
            done = 0
            info = None
            if "SHOW DATABASES" in action_parsed:
                observation = f"Error executing query: SHOW DATABASES is not allowed in this environment."
        else:
            observation, reward, done, info = self.env.step(action_parsed)
            reward = max(reward, 0)
            valid_action = info[ACTION_EXEC]
                    
        # Limit observation size due to context window thresholds for API call
        if isinstance(observation, str) and len(observation) > 350:
            observation = observation[:350]
        elif isinstance(observation, list) and len(observation) > 25:
            observation = observation[:25]
    
        self.done = done
        self.reward = reward
        self.turn_history["thoughts"].append(thought)
        self.turn_history["actions"].append(action)
        self.turn_history["observations"].append(str(observation)) # To avoid serialization issues
        self.turn_history["rewards"].append(reward)
        try: 
            self.turn_history["valid_action"].append(valid_action)
        except:
            pass
        
        self.num_rounds += 1
        if done or self.num_rounds >= self.max_rounds:
            return True, "TERMINATE"
        return True, f"Observation: {observation}"
        
        
    def reset(self, idx):
        super().reset()
        self.env.reset(idx)
        self.turn_history = {
            "thoughts": [],
            "actions": [],
            "observations": [],
            "rewards": [],
            "valid_action": [],
            "states": []
        }
        self.done = 0
        self.num_rounds = 0
        self.reward = 0
