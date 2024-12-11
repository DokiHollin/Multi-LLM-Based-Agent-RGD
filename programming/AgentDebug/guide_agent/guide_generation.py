import os
import openai
from typing import List, Dict
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,GenerationConfig
import json
from ..model import Message,AgentBase
from .similar_match import *
from programming.memory_pool import *

class GuideAgent(AgentBase):
    def generate(self, prompt: str) -> str:
        messages = [
            Message(role="system", content="You are a helpful assistant that generates guides for solving coding tasks."),
            Message(role="user", content=f"Task description:\n{prompt}"),
            Message(role="user", content="Please generate a detailed guide and advice on how to approach solving this task, but do not give code directly")
        ]
        result = self.model.generate_chat(messages=messages, max_tokens=1024, temperature=0.7,agent_name="Guide Agent")
        return result
    
    def refine(self, guides: str, analysis: str, memory_pool:MemoryPool, task: str) -> List[Message]:
        """
        Integrate the previous refine_guides logic here. 
        Improve and refine the existing guides based on the analysis results and previous failure cases.
        """
        # prompt
        messages = [
            Message(role="system", content="You are an expert in refining programming guides and strategies to improve code quality."),
            Message(role="user", content="By using the previous guides, the code failed the tests. After analyzing the failures, I need you to refine the guides to avoid the same issues in the future."),
            Message(role="user", content=f"Here were the original guides:\n{guides}"),
            Message(role="user", content=f"Here is the analysis of the failures:\n{analysis}"),
            Message(role="user", content="Please refine the guides with these specific concerns in mind, focusing on strategies to prevent these problems."),
            Message(role="user", content="Do not include the actual code in your response, only the refined guides."),
            Message(role="user", content=f"This is the task description: \n{task}")
        ]

        # If memory_pool has content, try to find the task most similar to the current task and attach relevant information
        if memory_pool.count_memories_in_jsonl() > 0:
            print("detected memory pool")
            most_similar_task = find_most_similar_task(task, memory_pool.path)
            if most_similar_task:
                print(f"find similar task with id: {most_similar_task[0]}")
                messages.append(Message(role="user", content=f"In the past, similar issues were encountered, and the following insights were gathered:\n{most_similar_task[1]}"))
                messages.append(Message(role="user", content="Use these insights along with the failure analysis to refine the guides."))

        # refine
        refined_guides = self.model.generate_chat(messages=messages, max_tokens=1024, temperature=0.7,agent_name="Guide Agent Refine")
        
        return [Message(role="assistant", content=refined_guides)]