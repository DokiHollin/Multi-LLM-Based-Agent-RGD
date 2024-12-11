from .model import ModelBase, Message
from ..utils import *
from ..memory_pool import MemoryPool
from .guide_agent.guide_generation import *
from .debug_agent.debug_agent import *
from .feedback_agent.feedback_agent import *
from .test_execution import *

class ParticipantGenerator:
    def generate(self, model: ModelBase, dataset):
        dataset_type = dataset[0]["task_id"].split("/")[0]
        if dataset_type in ["HumanEval", "MBPP"]:
            # get current path：.../programming/participants
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # return previous path：.../programming
            parent_dir = os.path.dirname(current_dir)
            # return previous path：.../ (top_level_directory)
            top_level_dir = os.path.dirname(parent_dir)

            # access output_data/dataset_type under the top_level_directory
            output_dir = os.path.join(top_level_dir, "output_data", dataset_type)
            os.makedirs(output_dir, exist_ok=True)

            # find exist outputfile previous generated
            existing_files = [f for f in os.listdir(output_dir) 
                              if f.startswith("output_") and (f.endswith("_pending.jsonl") or f.endswith("_complete.jsonl"))]

            max_num = -1
            last_file = None
            for f_name in existing_files:
                match = re.match(r"output_(\d{3})_(pending|complete)\.jsonl", f_name)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                        last_file = f_name

            if max_num == -1:
                # create output_000_pending.jsonl
                new_num = 0
                state = "pending"
            else:
                # if previous task not completed
                if last_file.endswith("_pending.jsonl"):
                    new_num = max_num
                    state = "pending"
                else:
                    # previosu completed create new jsonl file
                    new_num = max_num + 1
                    state = "pending"
            
            FILE_PATH = os.path.join(output_dir, f"output_{new_num:03d}_{state}.jsonl")
            if not os.path.exists(FILE_PATH):
                with open(FILE_PATH, 'w') as fp:
                    pass

            if os.path.exists(FILE_PATH):
                processed_tasks = {task['task_id'] for task in read_jsonl(FILE_PATH)}
            else:
                processed_tasks = set()
            # exit(0)

            memory_pool = MemoryPool()

            for task in dataset:
                if task['task_id'] in processed_tasks:
                    print(f"Skipping task {task['task_id']} as it is already processed.")
                    continue
                if task['is_solved']:
                    print(f"Skipping task {task['task_id']} as it is already solved.")
                    save_debugging_to_jsonl(
                        FILE_PATH,
                        task,
                        task['seed'],
                        '',
                        '',
                        True,
                        0,
                        '',
                        ''
                    )
                    continue
                analysis = ""
                # Ensure task is a dictionary
                if not isinstance(task, dict):
                    raise TypeError(f"Expected task to be a dictionary, but got {type(task)}")
                # Step 1: Generate initial guides
                print_chat("Generating Guide....", "step one")
                guide_agent = GuideAgent(model)
                guides = guide_agent.generate(task['prompt'])
                print(f"Finish Guide Generation: \n{guides}")
                
                # Initialize code and iteration counter
                debug_agent = DebugAgent(model)
                code = debug_agent.generate_code(guides, task['prompt'])
                iteration_count = 0
                max_iterations = 10
                print("Generated Code:")
                print_messages(code)

                # Step 3: Execute visible tests
                feedback_agent = FeedbackAgent(model)
                is_passing,code,iteration_count,visible_passed,visible_failed = self.iteration(iteration_count,max_iterations,task,code,model,feedback_agent,guide_agent,memory_pool,debug_agent,guides)
                print(is_passing)
                
                print_chat("Now test againist the hidden tests", "Step 8")
              
                exe = PyExecutor()  # Instantiate the executor class
                is_solved = exe.evaluate(task["entry_point"], code[0].content, task["test"], timeout=10)
                
                if is_solved:
                    # memory_pool.save_guides(guides)
                    print(f"Task {task['task_id']} solved successfully.")
                    task['is_solved'] = True
                    print_chat("Saving guide into memory pool...", "Step 9")
                    memory_pool:MemoryPool
                    memory_pool.save(task['prompt'], task['task_id'], guides,code[0].content)
                
                else:
                    print(f"Task {task['task_id']} failed hidden tests.")
                    task['is_solved'] = False

                # Convert analysis and guides to strings if they are not already
                analysis_text = analysis[0].content if isinstance(analysis, list) else analysis
                guides_text = guides[0].content if isinstance(guides, list) else guides

                save_debugging_to_jsonl(
                    FILE_PATH,
                    task,
                    code[0].content,
                    visible_passed,
                    visible_failed,
                    is_solved,
                    iteration_count,
                    analysis_text,
                    guides_text
                )
            # rename output file to output_xxx_complete
            if FILE_PATH.endswith("_pending.jsonl"):
                complete_path = FILE_PATH.replace("_pending.jsonl", "_complete.jsonl")
                os.rename(FILE_PATH, complete_path)
                file_path = complete_path
                pass_rate = calculate_pass_rate(file_path)
                print(f"Pass rate: {pass_rate:.2f}%")   
        else:
            print("not appropirate dataset")
            exit(0)

    def iteration(self,iteration_count,max_iterations,task,code,model,feedback_agent:FeedbackAgent,guide_agent:GuideAgent,memory_pool,debug_agent:DebugAgent,guides):
        while iteration_count < max_iterations:
            iteration_count += 1
            print_chat(f"Iteration {iteration_count}...", "iteration")

            # Step 3: Execute visible tests
            print_chat("Executing code with visible tests....", "step three")
          
            code_content = code[0].content
           
            visible_passed, visible_failed = execute_tests(code_content, task['given_tests'], visible=True)

            print(f"Passed visible tests are:")
            for passed in visible_passed:
                print(passed)
            print(f"Failed visible tests are:")
            for failed in visible_failed:
                print(failed)
            # return True
            # If no visible tests failed, break the loop and proceed to hidden tests
            if not visible_failed:
                print_chat("Passed visible tests, evaluating with hidden tests...", "step four")
                return True,code,iteration_count,visible_passed,visible_failed
            
            # Step 5: Failure Analysis
            print_chat("Begin failure analysis...", "step five")
            # feedback_agent = FeedbackAgent(model)
            analysis = feedback_agent.analyze_failure(task['prompt'], code_content, visible_passed, visible_failed)
            print_messages(analysis)
            # Step 6: Guide Refinement
            print_chat("Begin guide refinement...", "step six")
            guides = guide_agent.refine(guides, analysis[0].content, memory_pool, task['prompt'])
            print("Below are refined guides:")
            print_messages(guides)

            # Step 7: Generate new code based on refined guides
            print_chat("Begin code debugging...", "step seven")
            code = debug_agent.fix_code(guides, task['prompt'], code_content, visible_passed, visible_failed,analysis[0].content)
            print("Below is the fixed code:")
            print_messages(code)
        else:
            # If the loop completes without passing visible tests
            print(f"Task {task['task_id']} could not pass the visible test within {max_iterations} iterations.")
            return False,code,iteration_count,visible_passed,visible_failed