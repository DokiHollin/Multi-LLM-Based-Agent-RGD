import warnings
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import jsonlines
import numpy as np
import os
from joblib import Parallel, delayed

warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# 加载SBERT模型
model = SentenceTransformer("all-MiniLM-L6-v2")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def get_embedding(text: str) -> np.ndarray:
    """Generate SBERT embedding vectors for text"""
    embedding = model.encode(text)
    return embedding

def compute_sbert_similarity(task_embedding: np.ndarray, entry: dict) -> float:
    """Compute the SBERT similarity of the task description."""
    memory_embedding = get_embedding(entry['description'])
    return cosine_similarity([task_embedding], [memory_embedding])[0][0]

def compute_bm25_similarity(entry_keywords: list, entry_description: str) -> float:
    """
    Treat the items in the entry_keywords list as a whole keyword and perform a BM25 similarity match with entry_description。
    """
    query = " ".join(entry_keywords)
    bm25 = BM25Okapi([entry_description.split()])
    return bm25.get_scores([query])[0]

def compute_hybrid_score(sbert_sim: float, bm25_sim: float, alpha: float = 0.7) -> float:
    """Calculate the hybrid score, alpha controls the weight of the two."""
    return alpha * sbert_sim + (1 - alpha) * bm25_sim

def find_most_similar_task(task_prompt: str, memory_pool_path: str, alpha: float = 0.7) -> list:
    """
    Use hybrid scoring to find the task most similar to the given task from the memory pool.

    parameter:
    - task_prompt (str)。
    - memory_pool_path (str)。
    - alpha (float): default 0.7。

    return:
    - list: A list containing the most similar task IDs and instructions。
    """
    task_embedding = get_embedding(task_prompt)

    most_similar = None
    highest_hybrid_score = -1

    with jsonlines.open(memory_pool_path) as reader:
        entries = list(reader)

    # 并行计算相似度
    results = Parallel(n_jobs=4, backend="threading")(
        delayed(compute_similarity)(task_embedding, entry, alpha) for entry in entries
    )

    # 找到具有最高混合得分的任务
    for hybrid_score, task_id, guides in results:
        if hybrid_score > highest_hybrid_score:
            highest_hybrid_score = hybrid_score
            most_similar = [task_id, guides]

    return most_similar

def compute_similarity(task_embedding: np.ndarray, entry: dict, alpha: float) -> tuple:
    """Calculate the mixed similarity score for a single task。"""
    # SBERT similarity
    sbert_similarity = compute_sbert_similarity(task_embedding, entry)
    # BM25 similarity
    bm25_similarity = compute_bm25_similarity(entry['key_words'], entry['description'])
    hybrid_score = compute_hybrid_score(sbert_similarity, bm25_similarity, alpha)
    return hybrid_score, entry['task_id'], entry['guides']
# Task input and memory pool path
task_prompt = """
\ndef is_simple_power(x, n):\n    \"\"\"Your task is to write a function that returns true if a number x is a simple\n    power of n and false in other cases.\n    x is a simple power of n if n**int=x\n    For example:\n    is_simple_power(1, 4) => true\n    is_simple_power(2, 2) => true\n    is_simple_power(8, 2) => true\n    is_simple_power(3, 2) => false\n    is_simple_power(3, 1) => false\n    is_simple_power(5, 3) => false\n    \"\"\"\n
"""
memory_pool_path = "/home/hollin/thesis/Reflection/pool.jsonl"

# Run the similarity search
most_similar_entry = find_most_similar_task(task_prompt, memory_pool_path)
print(most_similar_entry)