
import autogen
from .prompt_assistant import PromptAssistant


bash_head = """Interact with a Bourne Shell system using BASH queries to answer a question.
Follow the user's instructions to solve the problem."""

# BASH
bash_prompts = {
    # solve
    "solve": """## Instructions
Given the question, please give a BASH command to solve it.

## Examples 
Thought: I can try to use `od` (octal dump) command to get a hexadecimal dump and stitch together the values into one continuous string.
Action: execute[od -A n -t x1 -N 16 /testbed/textfile7.txt | awk '{{$1=$1;print}}' | tr -d ' ']
Thought: I should find the paths to all java files in the testbed directory, then apply the word count command to each path.
Action: execute[find /testbed -name "*.java" -type f -exec md5sum {{}} + | sort | uniq -D -w 32 | awk '{{print $1}}']
Thought: I should find the paths to all php files in the testbed directory, then apply the word count command to each path.
Action: execute[find /testbed -name "*.php" -type f -exec cat {{}} + | wc -l]
Thought: The `du` command is useful for printing out disk usage of a specific directory. I can use the -h option to print in human readable format and the -s option to only print the total disk usage.
Action: execute[du -sh /workspace]

Please follow this RESPONSE FORMAT to give your thought and action.
## RESPONSE FORMAT
For action, put your BASH command in the execute[] block. Only give one command per turn.
Reply with the following template (<...> is the field description, replace it with your own response):

Thought: <your thought on how the question should be solved in one short sentence>
Action: execute[<your command>]
""",
    # error
    "error": """## Instruction
Please carefully check your last command and output to understand what went wrong. Revise and modify your command accordingly or try another command.

## Examples
Observation: /bin/bash: line 1: xxd: command not found
Thought: Seems like xxd is not available. I can try to use `od` (octal dump) command to get a hexadecimal dump.
Action: execute[od -A n -t x1 -N 16 /testbed/textfile7.txt]

Please follow this RESPONSE FORMAT to give your thought and action.
## RESPONSE FORMAT
For action, put your BASH command in the execute[] block. Only give one command per turn.
Reply with the following template (<...> is the field description, replace it with your own response):

Thought: <your thought on whether last command is wrong and how you would revise it.>
Action: execute[<your command>]
""",

    # verify
    "verify": """## Instructions
Carefully check if the question is answered.
- Please check if the desired tasks have been performed.
- If the question also asks for output, please check your last command and output, and make sure the output is in the desired format, and doesn't contain any extra fields.
- If the desired tasks have been performed, please submit the query with this "Action: submit" command. 

## Examples
Thought: This gives me storage information for every folder under the workspace directory, but I only need the storage for just the `workspace/` directory. The `-s` option should help with this.
Action: execute[du -sh /workspace]
Thought: This shows the output hashes and they have the same values, indicating that these files are duplicates. However, the file names are also shown, which are not needed.
Action: execute[find /testbed -name "*.java" -type f -exec md5sum {{}} + | sort | uniq -D -w 32 | awk '{{print $1}}']
Thought: This shows me too much information, I only need the total number of lines. I should add up the lines together and output a single number.
Action: execute[find /testbed -name "*.php" -type f -exec cat {{}} + | wc -l]
Thought: The hello.txt file has been created successfully in the testbed/ directory, and it contains the Hello World text. I can submit.
Action: submit

Please follow this RESPONSE FORMAT to give your thought and action.
## RESPONSE FORMAT
For action, put your BASH command in the execute[] block. Only give one command per turn.
If the question is solved, your action should be "Action: submit".
Reply with the following template (<...> is the field description, replace it with your own response, "|" is the "or" operation):

Thought: <your thought on whether the question is answered in one sentence>
Action: execute[<your new command>] | submit
"""
}


def check_success(observation):
    if "exec failed" in observation or "missing argument" in observation or "command not found" in observation or "invalid option" in observation or "Command timed out" in observation or "No such file or directory" in observation or "syntax error" in observation:
        print("Static Check: NO")
        return False
    return True


def state_transition(last_speaker, groupchat):
    messages = groupchat.messages
    last_message = messages[-1]['content']

    if "TERMINATE" in last_message:
        return None
    
    if last_speaker.name == "init":
        return groupchat.agent_by_name("solve")
    
    if last_speaker.name != "intercode":
        return groupchat.agent_by_name("intercode")

    # last speaker is intercode
    if not check_success(last_message):
        return groupchat.agent_by_name("error")

    last_action = messages[-2]['content'].split("Action:")[-1].strip()
    last_state = messages[-2]['name']
    print(last_state, last_action)
    if last_state == "solve":
        return groupchat.agent_by_name('verify')
    elif last_state == "error":
        return groupchat.agent_by_name('verify')
    elif last_state == "verify":
        if last_action == "submit":
            return "submit"
        return groupchat.agent_by_name('verify')
    elif last_state == "submit":
        return None
    

model = "gpt-35-turbo-1106"
config_list = autogen.config_list_from_json(
    "/home/ykw5399/TreeOfPrompts/intercod/intercode/experiments/OAI_CONFIG_LIST",
    filter_dict={"model": model},
)

llm_config = {
    "config_list": config_list,
    "temperature": 0,
    "model": model,
    "cache_seed": 41,
    "stop" : ["Observation:"]
}

all_agents = []
for key in bash_prompts:
    all_agents.append(
        PromptAssistant(
            name=key,
            system_message=bash_head,
            base_prompt=bash_prompts[key],
            llm_config=llm_config,
            code_execution_config=False,
        )
    )