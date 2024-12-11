import dataclasses
from typing import List
from ..model import Message, AgentBase

class FeedbackAgent(AgentBase):
    def analyze_failure(self, task_prompt: str, code_content: str, visible_passed: List[str], visible_failed: List[str]) -> str:
        # only pass 5 failed testcases
        passed_ls = visible_passed[:5] if len(visible_passed) > 5 else visible_passed
        failed_ls = visible_failed[:5] if len(visible_failed) > 5 else visible_failed

        # construct prompt
        messages = [
            Message(role="system", content="You are an expert in analyzing Python code and providing constructive feedback based on the failed testcases."),
            Message(role="user", content=f"Task description:\n{task_prompt}"),
            Message(role="user", content=f"The code that was tested:\n{code_content}"),
            Message(role="user", content=f"Here are the test cases that passed:\n{passed_ls}"),
            Message(role="user", content=f"Here are the test cases that failed:\n{failed_ls}"),
            Message(
                role="user", 
                content="Based on the above information, please analyze why the code failed for the given test cases. "
                        "Provide a detailed explanation of the potential issues and suggest possible improvements or changes "
                        "to the code which can match failed test cases output with the Real Execution Output. "
                        "Do not include the actual code in your response, only the suggestions and failure reasons."
            )
        ]

        # generate feedback report
        analysis = self.model.generate_chat(messages=messages, max_tokens=1024, temperature=0.7,agent_name="Feedback Agent")
        msg = [
            Message(
                role="assistant",
                content=analysis
            )
        ]
        return msg
        # return analysis
