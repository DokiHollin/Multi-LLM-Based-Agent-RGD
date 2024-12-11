from typing import List
from multiprocessing import Process, Pool
from .AgentDebug import model_factory
from .AgentDebug import ParticipantGenerator
from .utils import *
def async_main(
        model_name: str,
        dataset: str,
    ) -> None:
    gen = ParticipantGenerator()
    model = model_factory(model_name)
    # print(gen.generate(model))
    if dataset == 'humaneval':
        # get current path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # construct path to the input dataset
        input_file_path = os.path.join(current_dir, '..', 'input_data', 'humaneval', 'input.jsonl')
        
        # standardise path
        input_file_path = os.path.normpath(input_file_path)
        
        # detect whether exist
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"The file {input_file_path} does not exist.")
        
        # read input.jsonl
        data = read_jsonl(input_file_path)
        gen.generate(model=model,dataset=data)
        
    elif dataset == 'mbpp':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_file_path = os.path.join(current_dir, '..', 'input_data', 'mbpp', 'input.jsonl')
        input_file_path = os.path.normpath(input_file_path)
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"The file {input_file_path} does not exist.")
        data = read_jsonl(input_file_path)
        gen.generate(model=model,dataset=data)
    #     data,responses,background_data = gen.generate(model,language,i)
    # save(data,responses=responses,background_row=background_data.iloc[0], language=language)
    else:
        print("Other dataset")
    # exit(0)
def run_debug(
        model_name: str,
        dataset: str,
    ) -> None:
    async_main(model_name, dataset)
