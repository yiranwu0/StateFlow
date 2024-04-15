from typing import Callable, Dict, List, Literal, Union, Tuple, Any, Optional
from autogen import Agent, OpenAIWrapper, ConversableAgent


class PromptAssistant(ConversableAgent):
    """Use completion way instead of the message way.
"""

    def __init__(
        self,
        name: str,
        system_message: Optional[str] = "",
        base_prompt = "",
        llm_config: Optional[Union[Dict, Literal[False]]] = None,
        is_termination_msg: Optional[Callable[[Dict], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = None,
        human_input_mode: Optional[str] = "NEVER",
        description: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            name,
            system_message,
            is_termination_msg,
            max_consecutive_auto_reply,
            human_input_mode,
            llm_config=llm_config,
            description=description,
            **kwargs,
        )
        self.register_reply([Agent, None], PromptAssistant.generate_oai_reply)
        self.base_prompt = base_prompt
    

    def generate_oai_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[OpenAIWrapper] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:

        client = self.client if config is None else config
        if client is None:
            return False, None
        if messages is None:
            messages = self._oai_messages[sender]
    
        prompt = self.base_prompt + "\n\nHere is the question and current progress:"
        for m in messages:
            prompt += "\n" + m['content'].strip()
        
        tmp_messages = [{"content": prompt, "role": "user"}]

        response = client.create(
            context=messages[-1].pop("context", None),
            messages=self._oai_system_message + tmp_messages,
            cache=self.client_cache,
        )
        thought_action = response.choices[0].message.content.strip()

        try: 
            a = thought_action.strip().split(f"Action: ") 
            thought, action = a[0], a[1]
        except: 
            # fail to split, assume last step is thought, call model again to get action
            # assume last step is thought
            thought = thought_action.strip()
            if not "Thought:" in thought:
                thought = f"Thought: {thought}"

            tmp_messages[-1]['content'] += f"\n{thought}\nAction: "
            response = client.create(
                context=messages[-1].pop("context", None),
                messages=self._oai_system_message + tmp_messages,
                cache=self.client_cache,
            )
            action = response.choices[0].message.content.strip()

        
        thought_action = f"{thought.strip()}\nAction: {action.strip()}"
        return (False, None) if thought_action is None else (True, thought_action)
