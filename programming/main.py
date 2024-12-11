import os
from .participant import run_debug
import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, required=True, choices=["run_debug", "run_researcher"],
                        help="Strategy to run: `run_debug` or `run_researcher`")
    parser.add_argument("--model", type=str, required=True,
                        help="The model to use, e.g., GPT-4")
    parser.add_argument("--dataset", type=str, required=True,
                        help="dataset support either humaneval or mbpp")
    args = parser.parse_args()
    return args

def strategy_factory(strategy: str):
    def kwargs_wrapper_gen(func, delete_keys=[], add_keys={}):
        def kwargs_wrapper(**kwargs):
            for key in delete_keys:
                del kwargs[key]
            for key in add_keys:
                kwargs[key] = add_keys[key]
            return func(**kwargs)
        return kwargs_wrapper
    
    if strategy == "run_debug":
        return kwargs_wrapper_gen(run_debug)
    elif strategy == "run_researcher":
        return 1
    else:
        raise ValueError(f"Strategy `{strategy}` is not supported")

def main(args):
    # Get the strategy function
    run_strategy = strategy_factory(args.strategy)

    print(f"""
Starting run with the following parameters:
- Strategy: {args.strategy}
- Model: {args.model}
- dataset: {args.dataset}
""")
    if args.dataset != 'humaneval' and args.dataset != 'mbpp':
        raise ValueError(f"dataset `{args.dataset}` is not supported, should be either humaneval or mbpp")
    # Run the selected strategy
    run_strategy(model_name=args.model, dataset=args.dataset)

    print(f"Done! Processed dataset is: `{args.dataset}`")

if __name__ == "__main__":
    args = get_args()
    main(args)
