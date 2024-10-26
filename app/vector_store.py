# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma


# def prepare_vector_store(retrieved_data):
#     embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
    
#     documents = [
#         f"Aspect: {data['aspect']}, Sentiment: {data['sentiment']}, Opinions: {', '.join(data['all_opinions'])}"
#         for data in retrieved_data
#     ]
    
#     return Chroma.from_texts(documents, embeddings)
