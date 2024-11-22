import base64
import json
import os
import pandas as pd
import numpy as np
import google.generativeai as genai


def rag_using_json(message: str, top_n=5):
    try:
        df = pd.read_feather("maitri_data/maitri_data_with_embeddings.feather")
        
        if "Embeddings" not in df.columns or "Text" not in df.columns:
            raise ValueError("The required columns ('Embeddings', 'Text') are missing from the data.")
        
        query_embedding = genai.embed_content(model="models/text-embedding-004", content=message)["embedding"]
        
        query_embedding = np.array(query_embedding).astype(np.float32)

        embeddings = np.array(df["Embeddings"].tolist()).astype(np.float32)
        
        dot_products = np.dot(embeddings, query_embedding)

        top_indices = np.argsort(dot_products)[-top_n:][::-1]

        rag_passages = df.iloc[top_indices]["Text"].tolist()

        escaped_passages = [passage.replace("'", "").replace('"', "").replace("\n", " ") for passage in rag_passages]

        joined_passages = "\n\n".join(f"PASSAGE {i + 1}: {passage}" for i, passage in enumerate(escaped_passages))

        prompt = f"""
                CONTEXT:{joined_passages}

                QUESTION: {message}

                 Please provide a detailed answer based on the context above. If the context does not contain sufficient information to answer the question, please say so.
                 """

        return prompt

    except Exception as e:
        return f"An error occurred: {e}"
    


    