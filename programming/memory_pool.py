# memory_pool.py
import jsonlines
import os
import openai
from typing import List, Dict
from .utils import *
import json
from .config import OPENAI_API_KEY
def extract_keywords(task_description: str, generated_code: str) -> List[str]:
        """
        extract keyword return array。

        parameters:
        - task_description (str): task description。
        - generated_code (str): generated code。

        return:
        - List[str]: extract keyword。
        """
        gpt_model = GPTChat(model_name="gpt-4o", api_key=OPENAI_API_KEY)

        # define keyword prompt
        prompt = [
            {"role": "system", "content": "You are an assistant specialized in extracting precise and concise keywords for programming tasks."},
            {"role": "user", "content": f"Task description:\n{task_description}"},
            {"role": "user", "content": f"Generated code:\n{generated_code}"},
            {"role": "user", "content": "Identify three highly relevant keywords that capture the core task type, any specific operations required, and unique constraints or boundary conditions. Focus on terms that describe the task’s main functionality (e.g., 'sort integers in range', 'filter even numbers'), expected input/output (e.g., 'positive integers', 'boolean result'), and any specific conditions or cases (e.g., 'empty result if no match'). Provide the keywords as a comma-separated list."}
        ]

        # generate keyword
        keywords_text = gpt_model.generate_chat2(messages=prompt, max_tokens=64, temperature=0.3)
        keywords = [kw.strip() for kw in keywords_text.split(",")]

        return keywords
class GPTChat:
    def __init__(self, model_name: str, api_key: str = ""):
        self.model_name = model_name
        openai.api_key = api_key

    def generate_chat(self, messages: List[Dict[str, str]], stop: List[str] = None, max_tokens: int = 1024, temperature: float = 0.0, num_comps: int = 1) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            top_p=1,
            n=num_comps,
            max_tokens=max_tokens,
            stop=stop
        )
       
        return response.choices[0].message.content
    def generate_chat2(self, messages: List[Dict[str, str]], stop: List[str] = None, max_tokens: int = 1024, temperature: float = 0.0, num_comps: int = 1) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            top_p=1,
            n=num_comps,
            max_tokens=max_tokens,
            stop=stop
        )

        # Access the token usage information and save it
        # prompt_tokens = response['usage']['prompt_tokens']
        # completion_tokens = response['usage']['completion_tokens']
        data = {
            # 'task_id': response['id'],
            'agent': 'Keyword Extraction Agent',
            # 'prompt_tokens': prompt_tokens,
            # 'completion_tokens': completion_tokens
        }

        # # Append the new data to the JSONL file
        # with open(file_path, 'a') as f:
        #     f.write(json.dumps(data) + '\n')

        # print(f"Data appended to {file_path}")
        return response.choices[0].message.content

class MemoryPool:
    def __init__(self):
        self.pool = []
        base_dir = os.path.dirname(os.path.abspath(__file__))  
        self.path = os.path.join(base_dir, "pool.jsonl")
    
    def count_memories_in_jsonl(self) -> int:
        """
        Counts the number of memories (records) in a JSONL file.

        :param file_path: Path to the JSONL file.
        :return: Number of memories (records) in the file.
        """
        memory_count = 0
        with jsonlines.open(self.path) as reader:
            for _ in reader:
                memory_count += 1
        return memory_count
    
    def jsonl_save(self, file_path: str, task_id: str, guides: str, description: str, code: str, task: str):
        # Create the structure for the memory pool entry
        memory_pool_entry = {
            "task_id": task_id,
            "guides": guides,
            "description": description,
            "key_words": extract_keywords(task,code)
        }

        # Write to a JSONL file
        with jsonlines.open(file_path, mode='a') as writer:
            writer.write(memory_pool_entry)
        print("Saved Successfully")
        print("====================")

    def save(self, task: str, task_id: str, guides: str, code: str):
        # Generate a succinct task description
        gpt_model = GPTChat(model_name="gpt-4o", api_key=OPENAI_API_KEY)
        description_prompt = [
            {"role": "system", "content": "You are an expert in generating concise task descriptions."},
            {"role": "user", "content": f"Please generate a succinct description of the following task in less than 200 words:\n{task}"}
        ]
        description = gpt_model.generate_chat(messages=description_prompt, max_tokens=200, temperature=0.7)
        
        # Convert guides to a string if it is a Message object
        if isinstance(guides, Message):
            guides = guides.content  # Convert the Message object to its content string
        elif isinstance(guides, list):  # If guides is a list of Message objects
            guides = "\n".join([msg.content for msg in guides])  # Join all message contents into a single string

        # Save to memory pool
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  
            path = os.path.join(base_dir, "pool.jsonl")
            self.jsonl_save(path, task_id, guides, description,code,task)
        except Exception as e:
            print("Saving Error!!!")
            print(e)
