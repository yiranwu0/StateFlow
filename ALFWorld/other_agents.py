from typing import Callable, Dict, List, Literal, Union, Tuple, Any, Optional
from autogen import Agent, OpenAIWrapper, ConversableAgent

class PromptAssistant(ConversableAgent):
    """Use completion way instead of the message way.
"""

    def __init__(
        self,
        name: str,
        system_message: Optional[str] = "",
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
    
        # prompt = ""
        prompt = self._oai_system_message[0]['content'].strip() + "\n\n"
        for m in messages:
            prompt += "\n" + m['content'].strip()
        
        if not "Object of interest" in prompt:
            prompt += "\n"
        # print(prompt)
        # exit()
        tmp_messages = [{"content": prompt, "role": "user"}]

        if "instruct" in self.llm_config['model']:
            response = client.create(
                prompt=prompt,
                cache=self.client_cache,
            )
            extracted_response = response.choices[0].text.strip()
            if len(extracted_response.split("Thought")) > 2:
                extracted_response = extracted_response.split("Thought")[0] + "Thought" + extracted_response.split("Thought")[1]
        else:
            response = client.create(
                context=messages[-1].pop("context", None),
                messages=tmp_messages,
                cache=self.client_cache,
            )
            extracted_response = response.choices[0].message.content.strip()
        return (False, None) if extracted_response is None else (True, extracted_response)


