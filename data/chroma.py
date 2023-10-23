import os
from uuid import UUID

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from ai import open_ai

from core.config import BASE_DIR

openai_embedding_function = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"))


client = chromadb.PersistentClient(path=f"{BASE_DIR}/chroma/", settings=Settings(anonymized_telemetry=False))

def get_file_section_collection(project_id: UUID):
    return client.get_or_create_collection(
        f"{str(project_id)}-file_sections",
        embedding_function=openai_embedding_function,
    )

def delete_all_file_section_embeddings(project_id: UUID):
    get_file_section_collection(project_id).delete()

def create_file_section_embeddings(project_id: UUID, file_section_id: UUID, file_section: str):
    embedding = open_ai.create_embedding(file_section)
    get_file_section_collection(project_id).upsert(
        ids=[str(file_section_id)],
        embeddings=[embedding]
    )

def delete_file_section_embeddings(project_id: UUID, file_section_id: UUID):
    get_file_section_collection(project_id).delete(ids=[str(file_section_id)])
