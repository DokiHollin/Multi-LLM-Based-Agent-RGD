from .model import ModelBase,GPTOpenAIModel
from ..config import OPENAI_API_KEY

def model_factory(model_name: str, key: str = OPENAI_API_KEY) -> ModelBase:
    # can use different moddel
    return GPTOpenAIModel(model_name, key)