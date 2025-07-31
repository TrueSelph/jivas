import math;
import json;
import yaml;
import logging;
import traceback;
import from typing { Any, Optional, Tuple, List, Dict, Union, Iterator }
import from logging { Logger }
import from jivas.agent.action.action { Action }

import from jivas.agent.modules.data.serialization { yaml_dumps }

import from jivas.agent.action.agent_graph_walker {agent_graph_walker}
import from langchain_community.document_loaders { TextLoader }
import from langchain_text_splitters { CharacterTextSplitter }
import from langchain_core.vectorstores.base { VectorStore }
import from langchain_core.documents.base { Document }
import from langchain_openai { OpenAIEmbeddings }
import from langchain_openai { AzureOpenAIEmbeddings }
import from jivas.agent.modules.embeddings.jivas_embeddings { JivasEmbeddings }

node VectorStoreAction(Action) {
    # base node for all vector store action implementations
    has collection_name:str = "";
    has logger:Logger = logging.getLogger(__name__);
    has embedding_model_endpoint:str = "";
    has embedding_model_api_key:str = "";
    has embedding_model_api_version:str = "";
    has embedding_model_name:str = "";
    has embedding_model_provider:str = "openai";
    has export_page_size:int = 250;  # default page size for export operations

    #*
    Abstract interface defining operations for managing a vector store.
    This interface provides methods for initializing and managing vector store connections,
    performing document operations, and executing metadata-based searches.

    Abilities:
        get_client():
            Initializes and returns a vector store client using environment variables.
            Returns: Configured vectorstore client instance.
            Raises: ValueError if required environment variables are missing.

        get_collection(collection_name: str):
            Retrieves a collection by name.
            Args:
                collection_name (str): Name of the collection to retrieve.
            Returns: Collection object or None if not found.

        get_vectorstore():
            Initializes and returns a vectorstore reference using the client.
            Returns: Vectorstore object.
            Raises: ValueError if required environment variables are missing.

        metadata_search(metadata: dict, k: int = 10, **kwargs: Any) -> List[Document]:
            Searches for documents matching specified metadata.
            Args:
                metadata (dict): Metadata criteria for document search.
                k (int): Maximum number of results to return (default: 10).
                **kwargs: Additional search parameters.
            Returns: List of Document objects with similarity scores.

        list_documents(page: int = 1, per_page: int = 10, with_embeddings:bool=False) -> dict:
            Lists documents with pagination support.
            Args:
                page (int): Current page number (default: 1).
                per_page (int): Items per page (default: 10).
            Must return: {
                'page': int,
                'per_page': int,
                'total': int,
                'documents': list[dict]  # Each dict must have 'text' and 'metadata'
            }

        get_document(id: str) -> bool:
            Retrieves a specific document by ID.
            Args:
                id (str): Document identifier.
            Returns: Document object if found.

        update_document(id: str, data: dict) -> bool:
            Updates an existing document.
            Args:
                id (str): Document identifier.
                data (dict): Updated document fields.
            Returns: Updated document object.

        add_texts_with_embeddings(data: dict) -> str:
            inserts a whole document with embeddings.
            Args:
                data (dict): document fields with embeddings.
            Returns: document id.

        delete_document(id: str) -> bool:
            Removes a document from the store.
            Args:
                id (str): Document identifier.
            Returns: Deleted document object.

        delete_collection() -> bool:
            Deletes the entire collection.
            Returns: True if successful, False otherwise.
    *#

    def get_client() abs;
    def get_collection(collection_name:str) abs;
    def get_vectorstore() abs;
    def metadata_search(metadata:dict, k:int=10, **kwargs:dict) -> List[Document] abs;
    def list_documents(page:int=1, per_page:int=10, with_embeddings:bool=False) -> dict abs;
    def get_document(id:str) -> Union[dict, None] abs;
    def update_document(id:str, data:dict) -> Union[dict, None] abs;
    def delete_document(id:str) -> Union[dict, None] abs;
    def delete_collection() -> bool abs;

    def load_text_document(filepath:str, chunk_size:int=400, chunk_overlap:int=0) -> Union[list[str], None] {
        # """
        # Loads a text-based document into vectorstore

        # :param filepath (string) – path to text-based file
        # :param chunk_size (int) – the size of the text chunks (in chars) per document
        # :param chunk_overlap (int) – the overlap of the text chunks (in chars) per document

        # :returns List of IDs of the added texts.
        # """
        try {
            loader = TextLoader(filepath);
            documents = loader.load();
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap);
            docs = text_splitter.split_documents(documents);
            return self.add_documents(documents=docs);
        } except Exception as e {
            self.logger.error(f"Document loading failed: {traceback.format_exc()}");
            return None;
        }
    }

    def import_knodes(data: Union[list, str], with_embeddings: bool = False) -> bool {
        # Import knodes (knowledge nodes) into the vector store.
        knodes = [];
        if isinstance(data, str) {
            try {
                knodes = json.loads(data);
            } except json.JSONDecodeError {
                try {
                    knodes = yaml.safe_load(data);
                } except yaml.YAMLError as e {
                    self.logger.error(f"Invalid data format: {e}");
                    return False;
                }
            }
        } else {
            knodes = data;
        }

        try {
            failed = [];
            for knode in knodes {
                metadata = knode.get('metadata', {});
                text = str(knode['text']);
                doc_id = knode.get('id');
                embedding = knode.get('vec');

                if with_embeddings and embedding {
                    ids = self.add_texts_with_embeddings(
                        texts=[text],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        ids=[doc_id] if doc_id else None
                    );
                } else {
                    ids = self.add_texts(
                        texts=[text],
                        metadatas=[metadata],
                        ids=[doc_id] if doc_id else None
                    );
                }

                if not ids {
                    failed.append(knode);
                    self.logger.error(f"Failed to add: {text[:50]}...");
                } else {
                    self.logger.info(f"Added [{ids[0]}]: {text[:50]}...");
                }
            }
            return len(failed) == 0;
        } except Exception as e {
            self.logger.error(f"Import failed: {traceback.format_exc()}");
            return False;
        }
    }

    def export_knodes(as_json: bool = False, with_embeddings: bool = False, with_ids: bool = False) -> str {
        # Export knodes from the vector store in a standardized format.

        try {
            all_documents = [];

            # Collect all documents using standardized generator
            for batch in self.list_documents_generator(
                page_size=self.export_page_size,
                with_embeddings=with_embeddings
            ) {
                all_documents.extend(batch);
            }

            # Transform to knode format
            knodes = [];
            for doc in all_documents {
                knode = {
                    'text': doc['text'],
                    'metadata': doc['metadata']
                };
                if with_ids and 'id' in doc {
                    knode['id'] = doc['id'];
                }
                if with_embeddings and 'vec' in doc {
                    knode['vec'] = doc['vec'];
                }
                knodes.append(knode);
            }

            if as_json {
                return json.dumps(knodes, indent=2);
            } else {
                return yaml_dumps(knodes);
            }

        } except Exception as e {
            self.logger.error(f"Export failed: {traceback.format_exc()}");
            return "";
        }
    }

    def list_documents_generator(page_size: int = 250, with_embeddings:bool = False) -> Iterator[List[Dict]] {
        #*
        Generator that yields batches of documents in a standardized format
        {id: str, text: str, metadata: dict}
        *#
        page = 1;
        while True {
            result = self.list_documents(page=page, per_page=page_size, with_embeddings=with_embeddings);
            if not result or 'documents' not in result or not result['documents'] {
                break;
            }
            # Convert to standardized format
            standardized_batch = [];
            for doc in result['documents'] {
                standardized = {
                    'text': doc.get('text', ''),
                    'metadata': doc.get('metadata', {})
                };
                if 'id' in doc {
                    standardized['id'] = doc['id'];
                }
                if with_embeddings and 'vec' in doc {
                    standardized['vec'] = doc['vec'];
                }
                standardized_batch.append(standardized);
            }

            yield standardized_batch;

            # Check if we've reached the end
            if len(result['documents']) < page_size {
                break;
            }
            page += 1;
        }
    }

    def add_texts(texts:list[str], metadatas:Union[list[dict], None]=None,
                 ids:Union[list[str], None]=None, **kwargs:dict) -> Union[list[str], None] {
        #*
        Run more texts through the embedding and add to the vectorstore.

        :param texts (Iterable[str]) – Iterable of strings to add to the vectorstore.
        :param metadatas (List[dict] | None) – Optional list of metadatas associated with the texts.
        :param ids (List[str] | None) – Optional list of ids to associate with the texts.
        :param kwargs (Any)
        :returns List of IDs of the added texts.
        *#

        try {
            return self.get_vectorstore().add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"Add texts failed: {traceback.format_exc()}");
            return None;
        }
    }

    def add_texts_with_embeddings(texts:list[str], embeddings:Optional[List[List[float]]], metadatas:Union[list[dict], None]=None,
                 ids:Union[list[str], None]=None, **kwargs:dict) -> Union[list[str], None] {
        #*
        Run more texts through the embedding and add to the vectorstore.

        :param texts (Iterable[str]) – Iterable of strings to add to the vectorstore.
        :param embeddings (Optional[List[List[float]]]) – Iterable of vectors to add to the vectorstore.
        :param metadatas (List[dict] | None) – Optional list of metadatas associated with the texts.
        :param ids (List[str] | None) – Optional list of ids to associate with the texts.
        :param kwargs (Any)
        :returns List of IDs of the added texts with vectors.
        *#
        doc_ids = [];

        for (i, text) in enumerate(texts) {
            doc = {
                "text": text,
                "vec": embeddings[i] if embeddings[i] else None
            };
            if(metadatas and i < len(metadatas)) {
                doc["metadata"] = metadatas[i];
            }
            if(ids and i < len(ids)) {
                doc["id"] = ids[i];
            }
            id = self.insert_document(doc);
            if id {
                doc_ids.append(id);
            } else {
                self.logger.error(f"Failed to insert text with embedding: {text[:50]}...");
            }
        }

        return doc_ids;
    }

    def insert_document(data:dict) -> Union[str, None] {
        #*
        Insert a document with its metadata and vector into the vectorstore.

        :param data (dict) – Document data including 'text', 'metadata', and optional 'id'.
        :returns ID of the inserted document or None if failed.
        *#
        try {

            if collection := self.get_collection(self.collection_name) {
                record = collection.documents.upsert(data);
                if record and 'id' in record {
                    return record['id'];
                } else {
                    self.logger.error("Insert failed, no ID returned");
                    return None;
                }
            }

        } except Exception as e {
            self.logger.error(f"Insert document failed: {traceback.format_exc()}");
            return None;
        }
    }

    def add_documents(documents:list[Document], **kwargs:dict) -> Union[list[str], None] {
        #*
        Add or update documents in the vectorstore.

        :param documents (list[Document]) – Documents to add to the vectorstore.
        :param kwargs (Any)
        :returns List of IDs of the added texts.
        *#
        try {
            return self.get_vectorstore().add_documents(
                documents=documents,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"Add documents failed: {traceback.format_exc()}");
            return None;
        }
    }

    def get_embedding_model() -> Union[OpenAIEmbeddings, AzureOpenAIEmbeddings, JivasEmbeddings, None] {
        if self.embedding_model_provider == "openai" {
            return OpenAIEmbeddings(
                model=self.embedding_model_name,
                api_key=self.embedding_model_api_key
            ) if self.embedding_model_name else OpenAIEmbeddings(api_key=self.embedding_model_api_key);
        } elif self.embedding_model_provider == "azure" {
            return AzureOpenAIEmbeddings(
                azure_endpoint=self.embedding_model_endpoint,
                model=self.embedding_model_name,
                api_key=self.embedding_model_api_key,
                api_version=self.embedding_model_api_version
            );
        } elif self.embedding_model_provider == "jivas" {
            return JivasEmbeddings(
                base_url=self.embedding_model_endpoint,
                api_key=self.embedding_model_api_key,
                model=self.embedding_model_name
            ) if self.embedding_model_name else JivasEmbeddings(
                base_url=self.embedding_model_endpoint,
                api_key=self.embedding_model_api_key
            );
        } else {
            self.logger.error(f"Unsupported provider: {self.embedding_model_provider}");
            return None;
        }
    }

    def similarity_search(query:str, k:int=10, filter:Union[str, None]=None, **kwargs:dict) -> Union[List[Document], None] {
        #*
        Return typesense documents most similar to query.

        :param query (str) – Text to look up documents similar to.
        :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        :param filter (str | None) – typesense filter_by expression to filter documents on
        :param kwargs (Any)
        :returns List of Documents most similar to the query and score for each
        *#
        try {
            return self.get_vectorstore().similarity_search(
                query=query,
                k=k,
                filter=filter,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"Search failed: {traceback.format_exc()}");
            return None;
        }
    }

    def similarity_search_with_score(query:str, k:int=10, filter:Union[str, None]=None, **kwargs:dict) -> Union[List[Tuple[Document, float]], None] {
        #*
        Return typesense documents most similar to query.

        :param query (str) – Text to look up documents similar to.
        :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        :param filter (str | None) – typesense filter_by expression to filter documents on
        :param kwargs (Any)
        :returns List of Documents most similar to the query and score for each
        *#
        try {
            return self.get_vectorstore().similarity_search_with_score(
                query=query,
                k=k,
                filter=filter,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"Scored search failed: {traceback.format_exc()}");
            return None;
        }
    }

    def max_marginal_relevance_search(query:str, k:int=10, fetch_k:int=20,
                                     lamda_mult:float=0.5, **kwargs:dict) -> Union[List[Document], None] {
        #*
        Maximal marginal relevance optimizes for similarity to query AND diversity among selected documents.

        :param query (str) – Text to look up documents similar to.
        :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        :param filter (str | None) – typesense filter_by expression to filter documents on
        :param kwargs (Any)
        :returns List of Documents most similar to the query and score for each
        *#
        try {
            return self.get_vectorstore().max_marginal_relevance_search(
                query=query,
                k=k,
                fetch_k=fetch_k,
                lamda_mult=lamda_mult,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"MMR search failed: {traceback.format_exc()}");
            return None;
        }
    }

    def vector_similarity_search(embedding:list[float], k:int=10, **kwargs:dict) -> Union[List[Document], None] {
        #*
        Return docs most similar to embedding vector.

        :param embedding (list[float]) – Embedding to look up documents similar to.
        :param k (int) – Number of Documents to return. Defaults to 4.
        :param (Any) – Arguments to pass to the search method.
        :returns List of Documents most similar to the query vector.
        *#
        try {
            return self.get_vectorstore().similarity_search_by_vector(
                embedding=embedding,
                k=k,
                **kwargs
            );
        } except Exception as e {
            self.logger.error(f"Vector search failed: {traceback.format_exc()}");
            return None;
        }
    }

    def healthcheck() -> Union[bool, dict] {
        try {
            if not self.get_embedding_model() {
                return {
                    "status": False,
                    "message": "Embedding model initialization failed",
                    "severity": "error"
                };
            }

            if not self.get_vectorstore() {
                return {
                    "status": False,
                    "message": "Vectorstore initialization failed",
                    "severity": "error"
                };
            }
            return True;
        } except Exception as e {
            return {
                "status": False,
                "message": f"Healthcheck failed: {str(e)}",
                "severity": "critical"
            };
        }
    }
}
