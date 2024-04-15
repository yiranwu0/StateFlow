import argparse, config, json, openai, os
from intercode.envs import (
    BashEnv, SqlEnv, ACTION_EXEC
)
from tqdm import tqdm
from typing import Dict, List
from experiments.utils import ACTION_PARSER_MAP_REACT

import time
from .analysis import get_summary

from autogen import GroupChat, GroupChatManager, UserProxyAgent, gather_usage_summary
from .flow_bash import all_agents, state_transition
from .intercode_agent import InterCodeAgent

SETTING_MAP = {
    "sql": "MySQL Database",
    "bash": "Bourne Shell"
}

def preprocess_sql(record: Dict) -> List:
    db = record["db"]
    return [f"use {db}"]

parser = argparse.ArgumentParser(description='ReAct evaluation for Intercode environment')
parser.add_argument('--data_path', type=str, help='path to dataset to evaluate on')
parser.add_argument('--env', choices=['sql', 'bash'], help='Intercode environment to run eval on')
parser.add_argument('--image_name', type=str, help='name of docker image to build environment with')
parser.add_argument('--log_dir', type=str, help='folder to save experiment run log file to')
parser.add_argument('--max_turns', type=int, help='max number of interaction turns')
parser.add_argument('--verbose', action='store_true', help="print out logs")

parser.add_argument('--cache_seed', type=int, default=42, help='random seed for LLMs')
parser.add_argument('--model', type=str, default='gpt-35-turbo-1106', help='LLM model')
parser.add_argument('--key_option', type=str, default='azure', help='LLM key option')
parser.add_argument('--temperature', type=float, default=0, help='LLM temperature')
args = parser.parse_args()


class ExperimentWrapper():
    def __init__(self, args):
        self.args = args

        # Set environment (No logging for env)
        self.env = None
        added_str = ""
        if "gpt-4" in args.model:
            added_str = "gpt4_"
        if args.env == 'sql':
            self.env = SqlEnv(image_name=args.image_name,
                data_path=args.data_path, preprocess=preprocess_sql)
            if 'wiki' in args.data_path:
                added_str += 'wiki'
            if 'bird' in args.data_path:
                added_str += 'bird'
        elif args.env == 'bash':
            self.env = BashEnv(image_name=args.image_name,
                data_path=args.data_path)
            added_str = args.data_path.split("nl2bash_")[1].split(".json")[0]
        else:
            raise ValueError(f'Environment {args.env} not recognized')

        if added_str != "":
            added_str = f"_{added_str}"
        # Define log file name and path
        if not os.path.exists(args.log_dir):
            os.makedirs(args.log_dir, exist_ok=True)
        log_file_name = f"{args.env}{added_str}_top_agent_{args.max_turns}_s_{args.cache_seed}_turns.json"
        self.log_path = os.path.join(args.log_dir, log_file_name)
        summary_file_name = f"{args.env}{added_str}_top_agent_{args.max_turns}_turns_s_{args.cache_seed}_summary.json"
        self.summary_path = os.path.join(args.log_dir, summary_file_name)

        self.log_data = {}
        
        # Initialize parser
        self.action_parser = ACTION_PARSER_MAP_REACT[args.env]
        

    def run_expr(self):
        try:
            count = 0
            for idx in tqdm(range(len(self.env.data_loader)), disable=self.args.verbose):
                count += 1
                # if count < 49:
                #     continue
                self.env.reset(idx)
                record = self.env.data_loader.get(idx)

                # init memory
                start_time = time.time()

                intercode_agent = InterCodeAgent(
                    name="intercode",
                    env=self.env,
                    action_parser=self.action_parser,
                    max_rounds=self.args.max_turns,
                )
                init_agent = UserProxyAgent(
                    name="init",
                    code_execution_config = False
                )
                bashflow_chat = GroupChat(
                    agents=[*all_agents, intercode_agent, init_agent],
                    messages=[],
                    speaker_selection_method=state_transition,
                    max_round=100,
                )
                manager = GroupChatManager(groupchat=bashflow_chat, llm_config=None)
                init_agent.initiate_chat(manager, message=f"Question: {self.env.query}")


                total_usage_summary, _ = gather_usage_summary(all_agents)
                turn_history = intercode_agent.turn_history
                done = intercode_agent.done
                reward = intercode_agent.reward
                turn_count = intercode_agent.num_rounds
                model_key = list(total_usage_summary.keys())[1]

                token_1k_35_1106 = (0.001, 0.002)
                if args.model == "gpt-35-turbo-1106":
                    total_usage_summary['total_cost'] = (token_1k_35_1106[0] * total_usage_summary[model_key]["prompt_tokens"] +
                                                        token_1k_35_1106[1] * total_usage_summary[model_key]["completion_tokens"]) / 1000

                for agent in all_agents:
                    agent.reset()

                # ----------------------------------------------------------------------------
                # ----------------------------------------------------------------------------


                # Calculate reward if agent did not finish
                if not done:
                    observation, reward, done, info = self.env.step("submit")
                    turn_history["thoughts"].append("EXCEEDED MAX TURNS: submit")
                    turn_history["actions"].append("submit")
                    turn_history["observations"].append(str(observation)) # To avoid serialization issues
                    turn_history["rewards"].append(reward)
                    turn_history["valid_action"].append(True)
                    turn_history["states"].append("force_submit")
                
                # Logging
                log_episode = {
                    "environment": self.env.name,
                    "dataset": self.args.data_path,
                    "task_id": idx,
                    "query": self.env.query,
                    "turn_history": turn_history,
                    "summary": {
                        "max_reward": reward,
                        "turns_taken": turn_count,
                        "turns_max": self.args.max_turns,
                        "cost": total_usage_summary['total_cost'],
                        "prompt_tokens": total_usage_summary[model_key]["prompt_tokens"],
                        "completion_tokens": total_usage_summary[model_key]["completion_tokens"],
                        "total_tokens": total_usage_summary[model_key]["total_tokens"],
                        "time": round(time.time() - start_time, 2),
                    },
                    "dialogue": bashflow_chat.messages
                }
                if "hardness" in record:
                    log_episode["hardness"] = record["hardness"]
                self.log_data[idx] = log_episode

                if self.args.verbose:
                    print(f"Query {idx} Finished\n-Reward: {reward}\n-Turns: {turn_count}")


        except KeyboardInterrupt:
            print("Keyboard interrupt detected")
        finally:
            with open(self.log_path, "w") as fp:
                json.dump(self.log_data, fp, indent=2)
            self.env.close()
            summary = get_summary(
                    self.log_data, 
                    model=self.args.model, 
                    cache_seed=self.args.cache_seed, 
                    temperature=self.args.temperature)
            with open(self.summary_path, "w") as fp:
                json.dump(summary, fp, indent=2)

if __name__ == '__main__':
    expr_wrapper = ExperimentWrapper(args)
    expr_wrapper.run_expr()