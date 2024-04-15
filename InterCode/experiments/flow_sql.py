
import autogen
from .prompt_assistant import PromptAssistant

sql_head = """Interact with a MySQL Database system using SQL queries to answer a question."""

sql_prompts = {
    # observe
    "observe": """## Instructions
Use the DESCRIBE [table_name] or DESC [table_name] command to understand the structure of the relevant tables.
Only give one DESC command in action.

## Examples
Action: execute[DESC highschooler]
Action: execute[DESC friends]

## RESPONSE FORMAT
For action, put your SQL command in the execute[] block.
Reply with the following template (<...> is the field description, replace it with your own response):

Thought: <your thought on which table(s) is/are relevant in one short sentence>
Action: execute[<your command>]
""",
    # select
    "select": """## Instructions
Based on the understanding of the tables and the problem, formulate a SQL query with SELECT that answers the question EXACTLY. Use specific clauses like WHERE, JOIN, GROUP BY, HAVING, etc if necessary.
If you need more information of another table, use DESC to explore the table.
Notes: 
- You should construct your command that the output answers the question exactly. For example, If the question asks for count, your command should output a single number. 
- Only select the field the question asks for. Do not include relevant but unnecessary fields such as ids or counts, unless the question specifically asks for it.
- No need to CAST or ROUND numbers unless the question asks for it.

## Examples:
Thought: I should write a SQL command that selects the names from a table about high schoolers in ascending order of their grades. Grade should not be selected.
Action: execute[SELECT name, grade FROM high_schoolers ORDER BY high_schoolers.grades ASC]
Thought: I can use the SUM and AVG functions to get the total population and average area values for North America. 
Action: execute[execute[SELECT SUM(population) AS total_population, AVG(area) AS avg_area FROM countries WHERE continent = 'North America' AND area > 3000]]
Thought: I should write a SQL query that gets the name field from contestants and exclude the name of 'Jessie Alloway'
Action: execute[SELECT contestant_name FROM contestants WHERE contestant_name != 'Jessie Alloway']

## RESPONSE FORMAT
For action, put your SQL command in the execute[] block.
Reply with the following template (<...> is the field description, replace it with your own response):

Thought: <your thought on constructing command to answer the query exactly>
Action: execute[<your command>]
""",

    # error
    "error": """## Instructions
Please carefully read the error message to understand what went wrong.
If you don't have enough information to solve the question, you can use the DESC [table_name] command to explore another table.
You may want to review other tables to see if they have the information you need.

## Examples
Thought: A `transcripts` table exists, but it doesn't have the `release_date` column I came up with. I should find out what columns are available.
Thought: The `friends` table has two ids. I should check if the `highschooler` table has a name associated with an ID.
Thought: The `contestants` is a table, it is not a column in `people`. I need to check the `contestants` table to see how to get the contestant names.
Thought: I get a single number that is the number of likes that the high schooler Kyle has. This should be the answer.

## RESPONSE FORMAT
For action, put your SQL command in the execute[] block.
Reply with the following template (<...> is the field description, replace it with your own response):

Thought: <your thought on why this query is error and whether you should gather more information or fix the error in one sentence>
Action: execute[<your command>]
""",

    # verify
    "verify": """## Instructions
Carefully check if the output answers the question exactly.
Make sure the output only display fields that the problem asks for. 
- If the output contains any extra fields, please revise and modify your query (column alias is fine, no need to round numbers).
- If the output doesn't answer the question, please revise and modify your query. You may use DESC/DESCRIBE to learn more about the tables.
- If the output answers the question exactly, please submit the query with this "Action: submit" command.

## Examples
Thought: The output displays the contestant names and also contestant count. Although the count is used for sorting, it should not be displayed in output. I should modify my query to only select the contestant names.
Thought: The question asks for the total population for North America. However, the output also has the continent id. I should modify my query to only select the total population.

## RESPONSE FORMAT
For action, put your SQL command in the execute[] block. If the problem is solved, your action should be "Action: submit".
Reply with the following template (<...> is the field description, replace it with your own response, "|" is the "or" operation):

Thought: <your thought on whether the output and command answers the problem>
Action: execute[<your new command>] | submit
"""
}


# observe, select, error, verify
def state_transition(last_speaker, groupchat):
    messages = groupchat.messages
    last_message = messages[-1]['content']

    if "TERMINATE" in last_message:
        return None
    
    if last_speaker.name == "init":
        return groupchat.agent_by_name("observe")
    
    if last_speaker.name != "intercode":
        return groupchat.agent_by_name("intercode")

    # last speaker is intercode

    # error handling
    if last_message is None or "Error executing query" in last_message:
        return groupchat.agent_by_name("error")

    last_action = messages[-2]['content'].split("Action:")[-1].strip()
    last_action = last_action.replace("\n", "")

    last_state = messages[-2]['name']
    print(last_state, last_action)
    if last_state == "observe":
        return groupchat.agent_by_name('select')
    
    elif last_state == "select":
        if "submit" in last_action:
            return "submit"
        if "execute[SELECT" in last_action:
            return groupchat.agent_by_name('verify')
        return groupchat.agent_by_name('select')
    
    elif last_state == "verify":
        if "submit" in last_action:
            return None
        if "execute[SELECT" in last_action:
            return groupchat.agent_by_name('verify')
        return groupchat.agent_by_name('select')
    
    elif last_state == "error":
        if "execute[SELECT" in last_action:
            return groupchat.agent_by_name('verify')
        return groupchat.agent_by_name('select')
    
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
for key in sql_prompts:
    all_agents.append(
        PromptAssistant(
            name=key,
            system_message=sql_head,
            base_prompt=sql_prompts[key],
            llm_config=llm_config,
            code_execution_config=False,
        )
    )
