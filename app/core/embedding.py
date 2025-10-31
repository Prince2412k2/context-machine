from fastembed import TextEmbedding


embed_model=None
def init_embedding_model():
    global embed_model
    if embed_model is None:
        embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return embed_model
   