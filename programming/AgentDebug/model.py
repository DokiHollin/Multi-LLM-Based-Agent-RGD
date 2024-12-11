import os
import json
import dataclasses
from typing import List, Dict, Optional, Union
from transformers import GPT2Tokenizer
from openai import OpenAI

MessageRole = str  # "system", "user", "assistant"

@dataclasses.dataclass
class Message:
    role: MessageRole
    content: str

# ========= factory pattern =========
class ModelBase:
    def __init__(self, model_name: str, api_key: str = ""):
        self.model_name = model_name
        self.api_key = api_key

    def generate_chat(
        self, 
        messages: List[Message], 
        stop: Optional[List[str]] = None, 
        max_tokens: int = 1024, 
        temperature: float = 0.0, 
        num_comps: int = 1,
        agent_name: str = "Unknown"
    ) -> Union[List[str], str]:
        """
        All model implement this
        """
        raise NotImplementedError

class GPTOpenAIModel(ModelBase):
    """
    OpenAI model
    """
    def __init__(self, model_name: str, api_key: str = ""):
        super().__init__(model_name, api_key)
        self.client = OpenAI(api_key=self.api_key)

    def generate_chat(
        self, 
        messages: List[Message], 
        stop: Optional[List[str]] = None, 
        max_tokens: int = 1024, 
        temperature: float = 0.0, 
        num_comps: int = 1,
        agent_name: str = "Unknown"
    ) -> Union[List[str], str]:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[dataclasses.asdict(m) for m in messages],
            temperature=temperature,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            n=num_comps,
            max_tokens=max_tokens,
            stop=stop
        )
        # save token
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        data = {
            'task_id': response.id,
            'agent': agent_name,  # customizable
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens
        }
        file_path = './token.counter.jsonl'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                existing_data = [json.loads(line) for line in f.readlines()]
        else:
            existing_data = []
        existing_data.append(data)
        with open(file_path, 'w') as f:
            for entry in existing_data:
                f.write(json.dumps(entry) + '\n')

        if num_comps == 1:
            return response.choices[0].message.content
        return [choice.message.content for choice in response.choices]


# =========== Agent===========

class AgentBase:
    def __init__(self, model: ModelBase):
        self.model = model

    def generate(self, prompt: str) -> str:
        """
        According to the Agent's role strategy, construct messages, and then call model.generate_chat(). 
        Different agents have different ways of constructing system and user instructions.
        """
        raise NotImplementedError
