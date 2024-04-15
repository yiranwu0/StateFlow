system_message = """You are given a description of a household, please interact with the household to solve the task. 
This is a simulation of and all the actions are high-level shortcuts. Follow the instructions to give your next reply.

## RESPONSE FORMAT
Reply with the following template (<...> is the field description):
Thought: <your thought>
Action: <your action>
or
Action: <your action>
In you reply, you can give both a thought and an action, or just an action. You can only give one action at a time.

## Environment feedback
After each of your turn, the environment will give you immediate feedback.
Observation: <observation>
"""

system_message_end = """
Here is the task."""


plan_head = """## Instructions
You are given a household setting and a task to accomplish.
Please make a plan to complete the task.
Based on the object you need to find and the household setting, you should enumerate all the possible places where the object might be found. Start with the most likely places and list them in the order you would check.
Please follow the examples EXACTLY to give your reply. Do not add any additional information.
"""

plan_examples = {
    "pick_and_place": """## Examples
Your task is to: put some spraybottle on toilet.
Plan: I need to 1. search around for spraybottle and take it. 2. go to toilet and put it down. A spraybottle is more likely to appear in cabinet (1-4), countertop (1), toilet (1), sinkbasin (1-2), garbagecan (1). I can check one by one, starting with cabinet 1.
Your task is to: find some apple and put it in sidetable.
Plan: I need to 1. search around for an apple and take it. 2. go to sidetable and put it down. An apple is more likely to appear in fridges (1), diningtables (1-3), sidetables (1), countertops (1), sinkbasins (1), garbagecan (1). I can check one by one, starting with fridge 1.
""",
    "pick_clean_then_place": """
You must use the sinkbasin to clean the object.
## Examples
Your task is to: put a clean lettuce in diningtable.
Plan: I need to 1. search around for some lettuce and take it, 2. go to a sinkbasin and clean it, 3. go to diningtable and put it down. First I need to find a lettuce. A lettuce is more likely to appear in fridge (1), diningtable (1), sinkbasin (1), stoveburner (1-3), cabinet (1-13). I can check one by one, starting with fridge 1.
Your task is to: clean some apple and put it in sidetable.
Plan: I need to 1. search around for some apple and take it, 2. go to a sinkbasin and clean it, 3. go to sidetable and put it down. First I need to find an apple. An apple is more likely to appear in fridges (1), diningtable (1-3), sidetable (1), countertop (1), sinkbasin (1), garbagecan (1). I can check one by one, starting with fridge 1.
""",
    "pick_heat_then_place": """## Examples
Your task is to: heat some egg and put it in diningtable.
Plan: I need to 1. search around for an egg and take it, 2. go to microwave and heat it, 3. go to diningtable and put it down. An egg is more likely to appear in fridge (1), countertop (1-3), diningtable (1), stoveburner (1-4), toaster (1), garbagecan (1), cabinet (1-10). I can check one by one, starting with fridge 1.
Your task is to: put a hot apple in fridge.
Plan: I need to 1. search around for an apple and take it, 2. go to microwave and heat it, 3. go to fridge and put it down. An apple is more likely to appear in fridge (1), diningtable (1), coffeetable (1), drawer (1), cabinet (1-13), garbagecan (1). I can check one by one, starting with fridge 1.
""",
    "pick_cool_then_place": """## Examples
Your task is to: cool some pan and put it in stoveburner.
Plan: I need to 1. search around for a pan and take it, 2. go to fridge and cool it, 3. go to stoveburner and put it down. An pan is more likely to appear in stoveburner (1-4), sinkbasin (1), diningtable (1), countertop (1-2), cabinet (1-16), drawer (1-5). I can check one by one, starting with stoveburner 1.
Your task is to: put a cool mug in shelf.
Plan: I need to 1. search around for a mug and take it, 2. go to fridge and cool it, 3. go to shelf and put it down. A mug is more likely to appear in countertop (1-3), coffeemachine (1), cabinet (1-9), shelf (1-3), drawer (1-9). I can check one by one, starting with countertop 1.
""",
    "look_at_obj": """## Examples
Your task is to: look at bowl under the desklamp.
Plan: I need to 1. search around for a bowl and take it, 2. find a desklamp and use it. First I need to find a bowl. A bowl is more likely to appear in drawer (1-3), desk (1), sidetable (1-2), shelf (1-5), garbagecan (1). I can check one by one, starting with drawer 1.
Your task is to: examine the pen with the desklamp.
Plan: I need to 1. search around for a pen and take it, 2. find a desklamp and use it. First I need to find a pen. A pen is more likely to appear in drawer (1-10), shelf (1-9), bed (1), garbagecan (1). I can check one by one, starting with drawer 1.
""",
    
    "pick_two_obj": """## Examples
Your task is to: put two creditcard in dresser.
Plan: I need to 1. search around for a creditcard and take it, 2. go to dresser and put it down. 3. find another creditcard, 4. go to dresser and put it down. First I need to find the first creditcard. A creditcard is more likely to appear in drawer (1-2), coutertop (1), sidetable (1), diningtable (1), armchair (1-2), bed (1). I can check one by one, starting with drawer 1.
Your task is to: put two cellphone in sofa.
Plan: I need to 1. search around for a cellphone and take it, 2. go to sofa and put it down. 3. find another cellphone, 4. go to sofa and put it down. First I need to find the first cellphone. A cellphone is more likely to appear in coffeetable (1), diningtable (1), sidetable (1-2), drawer (1-4), sofa (1), dresser (1), garbagecan (1). I can check one by one, starting with coffeetable 1.
""",

}


action_prompts = {
    # plan placeholder
    "plan": """## Instructions
""",

    # pick
    "pick": """## Instructions
Please follow the plan to check receptacles in the household one by one to find the object of interest.
Each time, you can observe all the objects in the receptacle. Determine if the object you are looking for is in that receptacle.
You need to find the EXACT object that is asked for. 
For example, if you need to find a "soapbar", only take it when you see a "soapbar {i}" in the receptacle, instead of a "soapbottle {i}".
Use "open {recept}" command to open a receptacle. 

## Examples 
- Use "go to {recept}" command to go to the receptacle:
Action: go to cabinet 1

Action: go to fridge 1

Action: go to diningtable 1

- Take the object only if the place have the exact object you are looking for:
Thought: Now I find the soapbar (1). Next, I need to take it.
Action: take spraybottle 2 from cabinet 2

Thought: Now I find the apple (1). Next, I need to take it.
Action: take apple 1 from diningtable 1
""",
    
    "wrong_pick": """## Instructions
You just took the wrong object. Please put it down with the "put {obj} in/on {place}" command, where "place" is the place where you took the object from.
Please also give your thought of what is the next place to check based on the plan.

## Examples
Thought: I accidentally took the tomato instead of the apple. I need to put it back, and then check diningtable 2.
Action: put tomato 1 in/on diningtable 1

Thought: The object I want to take is a soapbar, but I took a soapbottle. I need to put it back, and then check the sinkbasin 1.
Action: put soapbottle 4 in/on toilet 1
""",

    # heat
    "heat": """## Instructions
You now take the object of interest with you. Now, please go to the microwave to heat the object.
You must first go to the microwave with the "go to {microwave}" command.
Then, use the "heat {obj} with {microwave}" command to heat the object. You don't need to open the microwave or put the object in the microwave.
    
## Examples:
- If you just picked the object, go to the microwave first:
Action: go to microwave 1
- Then heat the object:
Action: heat apple 1 with microwave 1
Action: heat bread 1 with microwave 1""",
    
    # cool
    "cool": """## Instructions
You now take the object of interest with you. Now, please go to the fridge to cool the object.
You must first go to the fridge with the "go to {fridge}" command.
Then, use the "cool {obj} with {fridge}" command to cool the object. You don't need to open the fridge or put the object in the fridge.

## Examples:
- If you just picked the object, go to the fridge first:
Action: go to fridge 1
Action: go to fridge 1
- Then cool the object:
Action: cool pan 1 with fridge 1
Action: cool potato 2 with fridge 1""",

    # clean
    "clean": """## Instructions
You now take the object of interest with you. Now, please go to the sinkbasin to clean the object.
You must first go to the sinkbasin with the "go to {sinkbasin}" command.
Then, use the "clean {obj} with {sinkbasin}" command to clean the object. You don't need water or soap to clean the object.

## Examples:
- Go to the sinkbasin first:
Action: go to sinkbasin 1
Action: go to sinkbasin 2
- Then clean the object:
Action: clean lettuce 1 with sinkbasin 1
Action: clean soapbar 4 with sinkbasin 2
""",

    # find_lamp
    "find_lamp": """## Instructions
You have found and taken the object, now please go around to find a desklamp.
Plese use "go to <place>" command to go to different places in the household to find a desklamp.
Use "open {place}" command to open a closed place if you need to.

## Examples
Action: go to sidetable 1
Action: go to dresser 1
""",

    # use_lamp
    "use_lamp": """## Instructions
You now find a desklamp.
Please use the "use {desklamp}" command to look at the object. "{desklamp}" denotes the desklamp you just found. You should not perform any other actions.

## Examples:
1. Observation: On the sidetable 2, you see a desklamp 3, a newspaper 1, and a statue 2.
Action: use desklamp 3
2. On the sidetable 2, you see a alarmclock 1, a desklamp 1, and a pen 2.
Thought: Now I find a desklamp (1). Next, I need to use it.
Action: use desklamp 1
""",

    # put
    "put": """## Instructions
You now take the object of interest with you. Now, please go to the required place to put down the object.
You must first go to the receptacle with "go to {recept}" command.
If the receptacle is closed, use the "open {recept}" command to open it.
You can only take one object at a time. If you task is to put two objects, please go to the required place to put the first object first.
When you are at the place, use the "put {obj} in/on {place}" command to put down the object.
    
## Examples:
- Always go to the receptacle first:
Action: go to sidetable 1
Action: go to toilet 1
Action: go to diningtable 1
Action: go to sofa 1
- Then put down the object:
Action: put apple 3 in/on sidetable 1
Action: put soapbar 4 in/on toilet 1
""",

}

