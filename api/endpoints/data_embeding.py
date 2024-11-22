import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


api_key = os.getenv("API_KEY_gm")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=api_key)

data = pd.read_json(r"D:\RAG chatbot\maitri_data\maitri_data.json")

df = pd.DataFrame(data)
df.columns = ["Title", "Text"]

def embed_fn(title, text):

    return genai.embed_content(model="models/text-embedding-004", content=text)["embedding"]

df["Embeddings"] = df.apply(lambda row: embed_fn(row["Title"], row["Text"]), axis=1)

df.to_feather("maitri_data/data_with_embeddings.feather")

print("Data Embedded and Saved to data/data_with_embeddings.feather")
