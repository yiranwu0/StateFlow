import argparse
from autogen.agentchat import AssistantAgent
import json
import os
import autogen

os.environ["ALFWORLD_DATA"] = "Your path to ALFWorld data here."

from src.multichat_utils import (
    ALFAgent,
    get_all_game_files,
    set_context,
    GroundingAgent,
    add_auto_reply,
    AssistantAgentAlf,
)

from autogen import gather_usage_summary

model = "gpt-35-turbo-1106"
config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={"model": model},
)
game_files = get_all_game_files("src/tasks/base_config.yaml")
game_files.sort()
print(f"Loaded a total of {len(game_files)} game files.")
prefixs = [
    "pick_and_place",
    "pick_clean_then_place",
    "pick_heat_then_place",
    "pick_cool_then_place",
    "look_at_obj",
    "pick_two_obj",
]

seed = [1222, 30, 12435, 21354, 31452, 31453]
seed_id = 1 # 1, 2
base_dir = f"logs_multiagent_s{seed[seed_id]}/"
success_all = 0
success_best = 0
cost_all = 0
count_all=0
counts = [0]* len(prefixs)
success_counts = [0]* len(prefixs)
for prefix in prefixs:
    os.makedirs(base_dir + f"{prefix}/", exist_ok=True)

run_times = 1
for i, file in enumerate(game_files):
    for prefix in prefixs:
        if prefix in file:
            correct_prefix = prefix
    path = base_dir + f"{correct_prefix}/{i}.json"

    print(f"Evaluating file {i}...")

    grounding_agent = GroundingAgent(name="GroundingAgent")
    success = 0

    for cnt in range(run_times):
        try:
            count_all += 1
            counts[prefixs.index(correct_prefix)] += 1

            user_proxy = ALFAgent(name="ALFWorld user proxy agent", task_path=file, grounding_agent=grounding_agent)
            assistant = AssistantAgentAlf(
                name="assistant",
                system_message="You are a helpful assistant",
                llm_config={
                    "config_list": config_list,
                    "temperature": 0,
                    "cache_seed": seed[seed_id],
                },
            )
            add_auto_reply(grounding_agent, user_proxy)
            context = user_proxy.get_examples()
            set_context(context, user_proxy, assistant)
            user_proxy.initiate_chat(assistant, clear_history=False, agent=grounding_agent)

            history = assistant.chat_messages[user_proxy]
            reply = history[-3]["content"]

            assistant.print_usage_summary()
            total_usage_summary, actual_usage_summary = gather_usage_summary([assistant, user_proxy])

            # If using azure, the model version is gpt-35-turbo without the version infomation, so the cost could be wrong.
            # we need to manually calculate the cost
            token_1k_35_1106 = (0.001, 0.002)
            model_key = list(total_usage_summary.keys())[1]
            if model == "gpt-35-turbo-1106":
                total_usage_summary['total_cost'] = (token_1k_35_1106[0] * total_usage_summary[model_key]["prompt_tokens"] +
                                                    token_1k_35_1106[1] * total_usage_summary[model_key]["completion_tokens"]) / 1000

            cost_all += total_usage_summary["total_cost"]
            print(cost_all, "for", i, "files")

            if "Task success, now reply TERMINATE" in reply and history[-3]["role"] == "user":
                with open(path, "w") as f:
                    json.dump(history, f, indent=4)
                success += 1
                success_counts[prefixs.index(correct_prefix)] += 1
            else:
                with open(f"{base_dir}{correct_prefix}/{i}_fail.json", "w") as f:
                    json.dump(history, f, indent=4)

        except Exception as e:
            # May encounter context overflow error, we should just skip it.
            print(e)
            cost_all += total_usage_summary["total_cost"]
            print(cost_all, "for", i, "files")

    success_all += success

    if success:
        success_best += 1

log_str = f"cost_all: {cost_all}\n"
for i, prefix in enumerate(prefixs):
    print(f"Sucess Count / Total Count for {prefix}: {success_counts[i]} / {counts[i]}")
    print(f"Success Rate for {prefix}: {success_counts[i]/counts[i]}")
    log_str += f"{prefix} | {success_counts[i]} / {counts[i]} | {round(success_counts[i]/counts[i], 3)}\n"

print(f"Sucess Count / Total Count: {success_all} / {count_all}")
print(f"Success Rate: {success_all/count_all}")
log_str += f"Total | {success_all} / {count_all} | {round(success_all/count_all, 3)}\n"
with open(f"{base_dir}log.txt", "w") as f:
    f.write(log_str)