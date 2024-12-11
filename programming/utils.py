# utils.py

import os
import jsonlines
import gzip
import json
from typing import List
from typing import List, Union, Optional, Literal
import dataclasses
import os
from vllm import LLM, SamplingParams
from tenacity import (
    retry,
    stop_after_attempt,  # type: ignore
    wait_random_exponential,  # type: ignore
)
from openai import OpenAI
from transformers import GPT2Tokenizer, AutoTokenizer
# from getKeyWords import *
MessageRole = Literal["system", "user", "assistant"]
@dataclasses.dataclass()
class Message():
    role: MessageRole
    content: str


def message_to_str(message: Message) -> str:
    return f"{message.role}: {message.content}"


def messages_to_str(messages: List[Message]) -> str:
    return "\n".join([message_to_str(message) for message in messages])
def read_jsonl(path: str) -> List[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File `{path}` does not exist.")
    elif not path.endswith(".jsonl"):
        raise ValueError(f"File `{path}` is not a jsonl file.")
    items = []
    with jsonlines.open(path) as reader:
        for item in reader:
            items += [item]
    return items

def read_jsonl_map(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File `{path}` does not exist.")
    elif not path.endswith(".jsonl"):
        raise ValueError(f"File `{path}` is not a jsonl file.")
    items = {}
    with jsonlines.open(path) as reader:
        for item in reader:
            items[item['task_id']] = item
    return items

def write_jsonl(path: str, data: List[dict], append: bool = False):
    with jsonlines.open(path, mode='a' if append else 'w') as writer:
        for item in data:
            writer.write(item)

def replace_seed_test(item, items_seed, items_test):
    if item['task_id'] in items_seed:
        item['seed'] = items_seed[item['task_id']]['solution']
        if 'is_passing' in items_seed[item['task_id']]:
            item['is_passing'] = items_seed[item['task_id']]['is_passing']
        else:
            item['is_passing'] = False
    else:
        item['seed'] = ""
    if item['task_id'] in items_test:
        item['given_tests'] = items_test[item['task_id']]['given_tests']
    else:
        item['given_tests'] = []
    return item
def print_messages(messages: List[Message], prefix = "") -> None:
    print("::CHAT MESSAGE::" +prefix)
    for msg in messages:
        print(msg.content)
    print("==================")


def print_chat(message: str, prefix=""):
    print("::CHAT MESSAGE::" +prefix)
    print(message)
    print("==================")

import jsonlines
import tiktoken

def calculate_token_count(text: str, model_name: str = "gpt-4o-mini") -> int:
    # Initialize the tokenizer for the specified model
    enc = tiktoken.encoding_for_model(model_name)
    
    # Encode the text to get the list of tokens
    tokenized_text = enc.encode(text)
    
    # Return the length of the list which corresponds to the number of tokens
    return len(tokenized_text)
def calculate_combined_token_count(failure_analysis: str, guides: str, model_name: str = "gpt-4o-mini") -> int:
    combined_text = failure_analysis + "\n" + guides
    return calculate_token_count(combined_text, model_name=model_name)

def save_debugging_to_jsonl(file_path: str, task: dict, code_implementations: List[str], passed_tests: List[str], failed_tests: List[str], is_solved: bool, debug_iteration: int, analysis: str, guides: str):
    # Create the structure for the debugging process
    debugging_data = {
        "task_id": task["task_id"],
        "prompt": task["prompt"],
        "entry_point": task["entry_point"],
        "test": task["test"],
        "canonical_solution": task["canonical_solution"],
        "is_passing": len(failed_tests) == 0,
        "given_tests": task["given_tests"],
        "is_solved": is_solved,
        "implementations": code_implementations,
        "test_feedback": failed_tests,
        "solution": code_implementations if code_implementations else "",
        "generated_test": passed_tests,
        "debug_iter": debug_iteration,
        "token_nums": calculate_combined_token_count(analysis, guides),
        # "key_words": extract_keywords(task["prompt"],code_implementations if code_implementations else "")
    }

    # Write to a JSONL file
    write_jsonl(file_path, [debugging_data], append=True)

import jsonlines

def save_debugging_to_jsonl_apps(file_path: str, task: dict, code_implementations: List[str], passed_tests: List[str], failed_tests: List[str], is_solved: bool, debug_iteration: int, analysis: str, guides: str, solve_rate,difficulty):
    # Create the structure for the debugging process
    debugging_data = {
        "task_id": task["task_id"],
        "prompt": task["description"],
        "entry_point": task["starter_code"],
        "test": task["test_list"],
        "is_passing": len(failed_tests) == 0,
        "given_tests": task["test_list"][:int(len(task["test_list"])/2)],
        "is_solved": is_solved,
        "implementations": code_implementations,
        "test_feedback": failed_tests,
        "solution": code_implementations if code_implementations else "",
        "generated_test": passed_tests,
        "debug_iter": debug_iteration,
        "token_nums": calculate_combined_token_count(analysis, guides),
        "solve_rate": solve_rate,
        "difficulty": difficulty
    }

    # Write to a JSONL file
    write_jsonl(file_path, [debugging_data], append=True)

import jsonlines

def save_debugging_to_jsonl_apps_competition(file_path: str, task: dict, code_implementations: List[str], passed_tests: List[str], failed_tests: List[str], is_solved: bool, debug_iteration: int, analysis: str, guides: str, solve_rate,difficulty):
    # Create the structure for the debugging process
    debugging_data = {
        "task_id": task["task_id"],
        "prompt": task["description"],
        "entry_point": task["starter_code"],
        "test": task["given_tests"],
        "is_passing": len(failed_tests) == 0,
        "given_tests": task["given_tests"][:int(len(task["given_tests"])/2)],
        "is_solved": is_solved,
        "implementations": code_implementations,
        "test_feedback": failed_tests,
        "solution": code_implementations if code_implementations else "",
        "generated_test": passed_tests,
        "debug_iter": debug_iteration,
        "token_nums": calculate_combined_token_count(analysis, guides),
        "solve_rate": solve_rate,
        "difficulty": difficulty
    }

    # Write to a JSONL file
    write_jsonl(file_path, [debugging_data], append=True)

import jsonlines

def calculate_pass_rate(file_path: str) -> float:
    """
    Calculate the pass rate based on the 'is_solved' field in the JSONL file.
    
    Args:
        file_path (str): The path to the humaneval_cleaned.jsonl file.
    
    Returns:
        float: The pass rate as a percentage.
    """
    total_tasks = 0
    solved_tasks = 0
    iter_more_than_one = 0
    # Read the JSONL file and calculate the pass rate
    with jsonlines.open(file_path) as reader:
        for obj in reader:
            total_tasks += 1
            if obj.get('is_solved', False):  # Check if 'is_solved' is True
                solved_tasks += 1
                if obj.get('debug_iter') > 0:
                    iter_more_than_one += 1
    
    # Calculate pass rate as a percentage
    if total_tasks == 0:
        return 0.0  # Avoid division by zero
    pass_rate = (solved_tasks / total_tasks) * 100
    print(f"iter more than one are: {iter_more_than_one}")
    return pass_rate


import re
import jsonlines

def extract_given_tests(prompt: str) -> List[str]:
    """
    Extracts the given tests from the prompt.
    """
    # Find all occurrences of tests between triple quotes (""")
    matches = re.findall(r'>>> (.*?)\n\s+(.*?)\n', prompt, re.DOTALL)
    given_tests = [f"assert {test} == {result}" for test, result in matches]
    return given_tests

def process_and_save_jsonl(input_path: str, output_path: str):
    """
    Processes the input JSONL file, extracts given tests from the prompt, 
    and saves the data to a new JSONL file with the given tests added.
    """
    with jsonlines.open(input_path) as reader, jsonlines.open(output_path, mode='w') as writer:
        for task in reader:
            # Extract the given tests from the prompt
            given_tests = extract_given_tests(task['prompt'])
            
            # Add the given_tests to the task
            task['given_tests'] = given_tests
            
            # Write the modified task to the new JSONL file
            writer.write(task)