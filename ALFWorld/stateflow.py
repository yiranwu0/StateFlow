
import os
import json
os.environ["ALFWORLD_DATA"] = "Your path to ALFWorld data here."

from autogen import gather_usage_summary, GroupChat, Agent, AssistantAgent, UserProxyAgent, GroupChatManager
from typing import Union
from collections import defaultdict

# take_prompt, put_prompt, clean_prompt, cool_prompt, heat_prompt, find_prompt, find_lamp_prompt, use_lamp_prompt,
from stateflow_prompts import system_message, action_prompts, system_message_end, plan_head, plan_examples
from src.completion_utils import ALFAgent, get_all_game_files, set_context

from other_agents import PromptAssistant
import autogen

seed = [2, 30, 32, 21354, 31452, 31453]
seed_i = 0

model = "gpt-35-turbo-1106"
config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={"model": model},
)

prefixs = [
    "look_at_obj",
    "pick_and_place",
    "pick_clean_then_place",
    "pick_heat_then_place",
    "pick_cool_then_place",
    "pick_two_obj",
]
base_dir = f"logs_sfagent_{seed[seed_i]}/"

llm_config = {
    "config_list": config_list,
    "temperature": 0,
    "model": model,
    "cache_seed": seed[seed_i],
    "stop" : ["Observation:"]
}

init_agent = UserProxyAgent(
    name="initiator",
    code_execution_config = False
)

all_agents = []
for key in action_prompts:
    all_agents.append(
        PromptAssistant(
            name=key,
            system_message=system_message+action_prompts[key]+system_message_end,
            llm_config=llm_config,
            code_execution_config=False,
        )
    )


# --------------------------------------------------------
# --------------------------------------------------------
# -------------determine object of interest---------------
check_agent = AssistantAgent(
    name="check",
    system_message="""Please determine what the object of interest is.
At the beginning, you are given the task. The task asks to put/heat/cool/clean/examine/look at an object.
Examples: 
put a clean lettuce in diningtable.
Object of interest: lettuce
put a hot apple in fridge.
Object of interest: apple
put a cool mug in shelf.
Object of interest: mug
put two cellphone in sofa
Object of interest: cellphone

Please reply: Object of interest: <object>
""",
    llm_config=llm_config,
    code_execution_config=False,
)

tmp_agent = UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: True,
    code_execution_config=False,
    human_input_mode="NEVER",
)
def get_object_of_interest(task_message):
    tmp_agent._oai_messages = defaultdict(list)
    check_agent._oai_messages = defaultdict(list)
    messages = [{"content": task_message.split("Your task is to:")[1], "role": "user"}]
    set_context(messages, tmp_agent, check_agent)
    tmp_agent.initiate_chat(message="Please determine what the object of interest is", recipient=check_agent, clear_history=False, silent=True)

    object_of_interest = check_agent._oai_messages[tmp_agent][-1]["content"].split(":")[-1].strip().lower()
    print("Object of interest:", object_of_interest)
    return object_of_interest
# --------------------------------------------------------
# --------------------------------------------------------


# keys: find, take, heat, cool, clean, find_lamp, use_lamp, put

def state_transition(
    last_speaker: Agent, groupchat: GroupChat
) -> Union[Agent, str, None]:
    messages = groupchat.messages
    last_message = messages[-1]['content']
    if "Task success" in last_message or "Task failed" in last_message:
        return None

    if last_speaker.name == "initiator":
        return groupchat.agent_by_name("plan")
    elif last_speaker.name == "plan":
        return groupchat.agent_by_name("pick")
    elif last_speaker.name != "ALFWorld":
        return groupchat.agent_by_name("ALFWorld")
    
    state_name = messages[-2]["name"]

    if "Nothing happens." in last_message:
        return groupchat.agent_by_name(state_name)

    type_task = groupchat.agent_by_name("initiator").task_prefix
    object_of_interest = groupchat.agent_by_name("initiator").object_of_interest
    print("last state:", state_name)
    
    if state_name == "pick":
        if f"You pick up the {object_of_interest}" in last_message:
            print("State: Object found: ", object_of_interest)
            if type_task == "pick_clean_then_place":
                return groupchat.agent_by_name("clean")
            elif type_task == "pick_heat_then_place":
                return groupchat.agent_by_name("heat")
            elif type_task == "pick_cool_then_place":
                return groupchat.agent_by_name("cool")
            elif type_task == "pick_and_place" or type_task == "pick_two_obj":
                return groupchat.agent_by_name("put")
            elif type_task == "look_at_obj":
                return groupchat.agent_by_name("find_lamp")
            else:
                raise ValueError("Task type not found")
        elif f"You pick up the" in last_message:
            return groupchat.agent_by_name("wrong_pick")
        else:
            return groupchat.agent_by_name("pick")

    elif state_name == "wrong_pick":
        return groupchat.agent_by_name("pick")

    elif state_name in ["clean", "heat", "cool"]:
        if "You clean the" in last_message or "You cool the" in last_message or "You heat the" in last_message:
            return groupchat.agent_by_name("put")
        else:
            return groupchat.agent_by_name(state_name)
        
    elif state_name == "put": 
        if type_task == "pick_two_obj":
            # todo: we can add more logic here
            return groupchat.agent_by_name("pick")
        else:
            return groupchat.agent_by_name("put")

    elif state_name == "find_lamp":
        if "desklamp" in last_message:
            return groupchat.agent_by_name("use_lamp")
        else:
            return groupchat.agent_by_name("find_lamp")
    
    elif state_name == "use_lamp":
        return  groupchat.agent_by_name("use_lamp")
    
    else:
        raise ValueError("State not found:", state_name)

# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------
game_files = get_all_game_files("src/tasks/base_config.yaml")
game_files.sort()
print(f"Loaded a total of {len(game_files)} game files.")
success_all = 0
success_best = 0
count_all = 0
cost_all = 0

counts = [0]* len(prefixs)
success_counts = [0]* len(prefixs)

for prefix in prefixs:
    os.makedirs(base_dir + f"{prefix}/", exist_ok=True)

run_times = 1
for i, file in enumerate(game_files):
    if len(prefixs) == 0:
        break

    correct_prefix = None
    for prefix in prefixs:
        if prefix in file:
            correct_prefix = prefix
            # prefixs.remove(correct_prefix)
            break
    if correct_prefix is None:
        continue
    counts[prefixs.index(correct_prefix)] += 1

    path = base_dir + f"{correct_prefix}/{i}.json"

    print(f"Evaluating file {i}...")
    success = 0

    for cnt in range(run_times):
        try:
            alfagent = ALFAgent(name="ALFWorld", task_path=file)
            task_message = "Household setting: " + "".join(alfagent.observation[0].split("\n\n")[1:])
            task_message = task_message.replace("Your task is to:", "\nYour task is to:")
            
            for agent in all_agents:
                if agent.name == "plan":
                    agent._oai_system_message = [{"content": plan_head+plan_examples[correct_prefix], "role": "system"}]
                    break

            stateflow_chat = GroupChat(
                agents=[init_agent, alfagent, *all_agents],
                messages=[],
                speaker_selection_method=state_transition,
                max_round=100,
            )
            manager = GroupChatManager(groupchat=stateflow_chat, llm_config=llm_config)
            init_agent.task_prefix = correct_prefix
            init_agent.object_of_interest = get_object_of_interest(task_message)

            init_agent.initiate_chat(manager, message=task_message)
            count_all += 1

            history = stateflow_chat.messages
            reply = history[-1]["content"]

            # ------added------
            total_usage_summary, actual_usage_summary = gather_usage_summary([check_agent, *all_agents])
            check_agent.reset()
            for agent in all_agents:
                agent.reset()

            token_1k_35_1106 = (0.001, 0.002)
            model_key = list(total_usage_summary.keys())[1]
            if model == "gpt-35-turbo-1106":
                total_usage_summary['total_cost'] = (token_1k_35_1106[0] * total_usage_summary[model_key]["prompt_tokens"] +
                                                    token_1k_35_1106[1] * total_usage_summary[model_key]["completion_tokens"]) / 1000

            cost_all += total_usage_summary["total_cost"]
            print(cost_all, "for", i, "files")

            history.append({'object_of_interest': init_agent.object_of_interest})
            if "Task success" in reply:
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

            with open(f"{base_dir}{correct_prefix}/{i}_max_limit.json", "w") as f:
                json.dump(history, f, indent=4)

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



