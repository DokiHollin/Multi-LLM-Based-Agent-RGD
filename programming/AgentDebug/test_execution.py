from typing import List, Tuple
from typing import NamedTuple, List, Tuple
from abc import ABC, abstractmethod
from ..utils import *
import ast
import signal
import astunparse
from ..execute_utils import *

class ExecuteResult(NamedTuple):
    is_passing: bool
    passed_tests: List[str]
    failed_tests: List[str]

class Executor(ABC):
    @abstractmethod
    def execute(self, func: str, tests: List[str], entry: str = "", timeout: int = 5) -> ExecuteResult:
        ...

    @abstractmethod
    def evaluate(self, name: str, func: str, test: str, timeout: int = 5) -> bool:
        ...
def clean_code_from_message(message: str) -> str:
    # Remove the ```python and ``` delimiters if they exist
    if message.startswith("```python"):
        message = message[len("```python"):].strip()
    if message.endswith("```"):
        message = message[:-len("```")].strip()
    return message
class PyExecutor(Executor):
    def execute(self, func: str, tests: List[str], entry: str = "", timeout: int = 5) -> ExecuteResult:
        print("|| Begin Executing...")
        
        # Combine function code and assert statements for each test
        imports = 'from typing import *'
        func_test_list = [f'{imports}\n{func}\n{test}' for test in tests]

        # Run the tests and collect the results
        passed_tests = []
        failed_tests = []
        is_passing = True
        
        for i, func_test in enumerate(func_test_list):
            try:
                function_with_timeout(exec, (func_test, globals()), timeout)
                passed_tests.append(tests[i])
            except Exception as e:
                
                output = get_output(func, tests[i], timeout=timeout)
                failed_tests.append(f"{tests[i]} # Real Execution Output: {output}")
                is_passing = False

        print("|| End Executing...")
        return ExecuteResult(is_passing, passed_tests, failed_tests)

    def evaluate(self, name: str, func: str, test: str, timeout: int = 5) -> bool:
        func = clean_code_from_message(func)    
        code = f"""{func}

{test}

check({name})
"""
        print("Constructed Code Block:\n", code)

        try:
            function_with_timeout(exec, (code, globals()), timeout)
            return True
        except Exception as e:
            print("Evaluation failed:", str(e))
            return False

def get_call_str(assert_statement: str) -> str:
    ast_parsed = ast.parse(assert_statement)
    try:
        call_str = ast_parsed.body[0].test.left  # type: ignore
    except:
        call_str = ast_parsed.body[0].test  # type: ignore

    return astunparse.unparse(call_str).strip()

def get_output(func: str, assert_statement: str, timeout: int = 5) -> str:
    try:
        exec(f"from typing import *\n{func}", globals())
        func_call = get_call_str(assert_statement)
        output = function_with_timeout(eval, (func_call, globals()), timeout)
        return output
    except TimeoutError:
        return "TIMEOUT"
    except Exception as e:
        return str(e)

def clean_code_from_message(message: str) -> str:
    # Remove the ```python and ``` delimiters
    if message.startswith("```python"):
        message = message[len("```python"):].strip()
    if message.endswith("```"):
        message = message[:-len("```")].strip()
    return message

def execute_tests(func_message: str, tests: List[str], visible: bool = True) -> Tuple[List[str], List[str]]:
    # Clean the code from the Message object content
    func = clean_code_from_message(func_message)
    executor = PyExecutor()
    result = executor.execute(func, tests)
    return result.passed_tests, result.failed_tests

# def execute_tests(func: str, tests: List[str], visible: bool = True) -> Tuple[List[str], List[str]]:
#     executor = PyExecutor()
#     result = executor.execute(func, tests)
#     return result.passed_tests, result.failed_tests

# # Example usage
# task = {
#     "task_id": "HumanEval/32",
#     "prompt": "...",  # Assume the full prompt is included here
#     "entry_point": "find_zero",
#     "given_tests": [
#         "assert round(find_zero([1, 2]), 2) == -0.5",
#         "assert round(find_zero([-6, 11, -6, 1]), 2) == 1.0"
#     ]
# }

# # Assume `code` is the initial generated code for the task
# visible_passed, visible_failed = execute_tests(code, task['given_tests'], visible=True)

# print("Passed Tests:", visible_passed)
# print("Failed Tests:", visible_failed)
if __name__ == "__main__":
    func_message = """```python
def split_sequence(n, a):
    from collections import defaultdict

    # Create a list of tuples (value, index) and sort it
    indexed_a = sorted((value, index + 1) for index, value in enumerate(a))

    # Create a mapping from original indices to their sorted positions
    position_map = {index: i for i, (value, index) in enumerate(indexed_a)}

    # Create a list to hold the subsequences
    subsequences = []
    visited = [False] * n

    for i in range(n):
        if not visited[i]:
            current_subsequence = []
            current_index = i

            while not visited[current_index]:
                visited[current_index] = True
                current_subsequence.append(indexed_a[current_index][1])  # Store the original index
                current_index = position_map[indexed_a[current_index][1]]

            subsequences.append(current_subsequence)

    # Prepare the output
    result = [len(subsequences)]
    for subseq in subsequences:
        result.append([len(subseq)] + subseq)

    return result
```"""
    tests = [
    "assert split_sequence(6, [3, 2, 1, 6, 5, 4]) == [4, [2, 1, 3], [1, 2], [2, 4, 6], [1, 5]]",
    "assert split_sequence(6, [83, -75, -49, 11, 37, 62]) == [1, [6, 1, 2, 3, 4, 5, 6]]",
    "assert split_sequence(1, [1]) == [1, [1, 1]]",
    "assert split_sequence(2, [1, 2]) == [2, [1, 1], [1, 2]]",
    "assert split_sequence(2, [2, 1]) == [1, [2, 1, 2]]",
    "assert split_sequence(3, [1, 2, 3]) == [3, [1, 1], [1, 2], [1, 3]]",
    "assert split_sequence(3, [3, 2, 1]) == [2, [2, 1, 3], [1, 2]]",
    "assert split_sequence(3, [3, 1, 2]) == [1, [3, 1, 2, 3]]",
    "assert split_sequence(10, [3, 7, 10, 1, 9, 5, 4, 8, 6, 2]) == [3, [6, 1, 4, 7, 2, 10, 3], [3, 5, 6, 9], [1, 8]]",
    "assert split_sequence(20, [363756450, -204491568, 95834122, -840249197, -49687658, 470958158, -445130206, 189801569, 802780784, -790013317, -192321079, 586260100, -751917965, -354684803, 418379342, -253230108, 193944314, 712662868, 853829789, 735867677]) == [3, [7, 1, 4, 7, 2, 10, 3, 13], [11, 5, 14, 15, 6, 16, 12, 17, 18, 20, 19, 9], [2, 8, 11]]",
    "assert split_sequence(50, [39, 7, 45, 25, 31, 26, 50, 11, 19, 37, 8, 16, 22, 33, 14, 6, 12, 46, 49, 48, 29, 27, 41, 15, 34, 24, 3, 13, 20, 47, 9, 36, 5, 43, 40, 21, 2, 38, 35, 42, 23, 28, 1, 32, 10, 17, 30, 18, 44, 4]) == [6, [20, 1, 43, 34, 25, 4, 50, 7, 2, 37, 10, 45, 3, 27, 22, 13, 28, 42, 40, 35, 39], [23, 5, 33, 14, 15, 24, 26, 6, 16, 12, 17, 46, 18, 48, 20, 29, 21, 36, 32, 44, 49, 19, 9, 31], [2, 8, 11], [2, 23, 41], [2, 30, 47], [1, 38]]",
    "assert split_sequence(100, [39, 77, 67, 25, 81, 26, 50, 11, 73, 95, 86, 16, 90, 33, 14, 79, 12, 100, 68, 64, 60, 27, 41, 15, 34, 24, 3, 61, 83, 47, 57, 65, 99, 43, 40, 21, 94, 72, 82, 85, 23, 71, 76, 32, 10, 17, 30, 18, 44, 59, 35, 89, 6, 63, 7, 69, 62, 70, 4, 29, 92, 87, 31, 48, 36, 28, 45, 97, 93, 98, 56, 38, 58, 80, 8, 1, 74, 91, 53, 55, 54, 51, 96, 5, 42, 52, 9, 22, 78, 88, 75, 13, 66, 2, 37, 20, 49, 19, 84, 46]) == [6, [41, 1, 76, 43, 34, 25, 4, 59, 50, 7, 55, 80, 74, 77, 2, 94, 37, 95, 10, 45, 67, 3, 27, 22, 88, 90, 13, 92, 61, 28, 66, 93, 69, 56, 71, 42, 85, 40, 35, 51, 82, 39], [45, 5, 84, 99, 33, 14, 15, 24, 26, 6, 53, 79, 16, 12, 17, 46, 100, 18, 48, 64, 20, 96, 83, 29, 60, 21, 36, 65, 32, 44, 49, 97, 68, 19, 98, 70, 58, 73, 9, 87, 62, 57, 31, 63, 54, 81], [8, 8, 75, 91, 78, 89, 52, 86, 11], [2, 23, 41], [2, 30, 47], [2, 38, 72]]"
] 
    func = clean_code_from_message(func_message)
    executor = PyExecutor()
    visible_passed, visible_failed = execute_tests(func, tests, visible=True)

    print(f"Passed visible tests are:")
    for passed in visible_passed:
        print(passed)
    print(f"Failed visible tests are:")
    for failed in visible_failed:
        print(failed)

