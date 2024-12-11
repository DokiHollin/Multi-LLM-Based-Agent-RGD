import re
import json
from typing import List
from ..model import Message, AgentBase

def extract_code(response: str) -> str:
    # A utility function to extract Python code from a code block
    match = re.search(r"```python(.*?)```", response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # Remove explanatory comments and multi-line strings from code
        cleaned_code = re.sub(r'^\s*#.*$', '', code, flags=re.MULTILINE)
        cleaned_code = re.sub(r'""".*?"""', '', cleaned_code, flags=re.DOTALL)
        return cleaned_code.strip()
    return ""

class DebugAgent(AgentBase):
    def generate_code(self, guides: str, prompt: str) -> List[Message]:
        # Generate code according to the provided guides and prompts
        messages = [
            Message(role="system", content="You are an expert python programming assistant."),
            Message(role="user", content=f"Complete the following task in Python. Please respond with code only (with the code inside a Markdown code block).\n{prompt}"),
            Message(role="user", content=f"Here are some guides to help you solve the task:\n{guides}"),
            Message(role="user", content="Please generate the code implementation based on the above information.")
        ]
        
        # Calling model to generate code
        initial_code = self.model.generate_chat(messages=messages, temperature=0.0)
        return [Message(role="assistant", content=initial_code)]

    def fix_code(self, refined_guides: str, prompt: str, code_content: str, passed_tests: List[str], failed_tests: List[str], analysis: str) -> List[Message]:
        passed_ls = passed_tests[:5] if len(passed_tests) > 5 else passed_tests
        failed_ls = failed_tests[:5] if len(failed_tests) > 5 else failed_tests

        messages = [
            Message(role="system", content="You are an expert Python programming assistant."),
            Message(role="user", content=f"Here is a task description:\n{prompt}"),
            Message(role="user", content=f"Here are the generation guides:\n{refined_guides}"),
            Message(role="user", content=f"The current code is as follows:\n```python\n{code_content}\n```"),
            Message(role="user", content=f"Here are the test cases that passed:\n{passed_ls}"),
            Message(role="user", content=f"Here are the test cases that failed:\n{failed_ls}"),
            Message(role="user", content=f"Here may be part of the reason for these failures:\n{analysis}"),
            Message(role="user", content="Please refine the code based on the above information to fix the issues causing the failures while ensuring the passed tests still pass."),
            Message(role="user", content="Please respond with code only, no assertion required. (with the code inside a Markdown code block)")
        ]   

        new_code_response = self.model.generate_chat(messages, max_tokens=2048, temperature=0,agent_name="Debug Agent")
        new_code = extract_code(new_code_response)
        
        return [Message(role="assistant", content=new_code)]
