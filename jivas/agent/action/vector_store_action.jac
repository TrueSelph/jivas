import:py math;
import:py json;
import:py yaml;
import:py logging;
import:py traceback;
import:py from typing { Any, Tuple }
import:py from logging { Logger }
import:jac from action { Action }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from interact_graph_walker {interact_graph_walker}
import:py from langchain_community.document_loaders { TextLoader }
import:py from langchain_text_splitters { CharacterTextSplitter }
import:py from langchain_core.vectorstores.base { VectorStore }
import:py from langchain_core.documents.base { Document }
import:py from langchain_openai { OpenAIEmbeddings }
import:py from langchain_openai { AzureOpenAIEmbeddings }
import:py from jivas.agent.modules.embeddings.jivas_embeddings { JivasEmbeddings }

node VectorStoreAction :Action: {
    # base node for all store action implementations
    # a store action specifies abilities which facilitate vector store interfacing

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has embedding_model_endpoint:str = "";
    has embedding_model_api_key:str = "";
    has embedding_model_api_version:str = "";
    has embedding_model_name:str = ""; # e.g. text-embedding-3-large
    has embedding_model_provider:str = "openai"; # e.g. openai / azure / google / jivas


    can get_client() {
        # """
        # Override to initialize and return a VectorStore client using configuration settings
        # from environment variables.

        # Returns:
        #     A configured vectorstore client instance.

        # Raises:
        #     ValueError: If any required environment variable is not set.
        # """
    }

    can get_collection(collection_name:str) {
        # """
        # Returns a collection by name or None if it doesn't exist
        # """
    }

    can get_vectorstore() {
        # """
        # Override to initialize and return a vectorstore reference using client

        # Returns:
        #     A vectorstore object.

        # Raises:
        #     ValueError: If any required environment variable is not set.
        # """
    }

    can load_text_document(filepath:str, chunk_size:int=400, chunk_overlap:int=0) {
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

            # add documents to vectorstore
            return self.add_documents(documents = docs);

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can import_knodes(data: list) -> bool {

        # Try to parse the content as JSON
        importing_error_message= "";

        if(isinstance(data, str)) {
            try {
                knodes = json.loads(data);
            } except json.JSONDecodeError as e {
                importing_error_message = f"Failed to import knode JSON, {e}";
            }

            # Try to parse the content as YAML
            try {
                knodes = yaml.safe_load(data);
            } except yaml.YAMLError as e {
                importing_error_message = f"Failed to import knode YAML, {e}";
            }
        }else {
            knodes = data;
        }

        try {

            failed = [];
            successful = [];

            self.logger.info(f"Importing {knodes} ...");

            for knode in knodes {

                if(knode.get('id')){
                    metadatas = [knode['metadata']];
                    ids = self.add_texts(
                        texts=[str(knode['text'])],
                        metadatas=metadatas,
                        ids = [knode['id']]
                    );
                }else{
                    metadatas = [knode['metadata']];
                    ids = self.add_texts(
                        texts=[str(knode['text'])],
                        metadatas=metadatas
                    );
                }

                if(not ids) {
                    self.logger.error(f"Failed to add text to vectorstore - {str(knode['text'][:50])}...");
                    failed.append(knode);
                } else {
                    self.logger.info(f"Added to vectorstore - [{ids}] {str(knode['text'][:50])}...");
                    successful.append(knode);
                }
            }

            if(failed) {
                self.logger.error(f"Failed to import {len(failed)} knodes");
                return False;
            } else {
                self.logger.info(f"Successfully imported {len(successful)} knodes");
                return True;
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
            self.logger.error(importing_error_message);
            return False;
        }
    }

    can export_knodes(as_json:bool = False, embeddings:bool = False, with_ids:bool = False) -> str {
        # """
        # Export all documents from the vectorstore as knodes.

        # :returns knode YAML
        # """
        try {

            if(collection := self.get_collection(self.collection_name)) {

                excluded_fields = '';

                if with_ids {
                    if(not embeddings) {
                        excluded_fields = 'vec';
                    }
                } else {
                    excluded_fields = 'id,vec';
                    if(embeddings) {
                        excluded_fields = 'id';
                    }
                }
                per_page = 250;
                page = 1;
                # Fetch documents using the search endpoint
                results = collection.documents.search({
                    'q': '*',
                    'per_page': per_page,
                    'page': page,
                    'exclude_fields': excluded_fields
                });

                # extract the document record
                documents = [];
                hits = results.get('hits', []);
                total = results.get('found', 0);
                for item in hits {
                    documents.append(item.get('document'));
                }

                # Calculate the total number of pages needed
                total_pages = math.ceil(total / per_page);

                # Loop through remaining pages
                for page in range(2, total_pages + 1){
                    results = collection.documents.search({
                        'q': '*',
                        'per_page': per_page,
                        'page': page,
                        'exclude_fields': excluded_fields
                    });
                    hits = results.get('hits', []);
                    for item in hits{
                        documents.append(item.get('document'));
                    }
                }

                if(as_json) {
                    return json.dumps(documents);
                } else {
                    return Utils.yaml_dumps(documents);
                }
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can add_texts(texts:list[str], metadatas:list[dict]|None=None, ids:list[str]|None=None, **kwargs:Any) -> list[str] {
        # """
        # Run more texts through the embedding and add to the vectorstore.

        # :param texts (Iterable[str]) – Iterable of strings to add to the vectorstore.
        # :param metadatas (List[dict] | None) – Optional list of metadatas associated with the texts.
        # :param ids (List[str] | None) – Optional list of ids to associate with the texts.
        # :param kwargs (Any)
        # :returns List of IDs of the added texts.
        # """
        try {

            return self.get_vectorstore().add_texts(
                texts = texts,
                metadatas = metadatas,
                ids = ids,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can add_documents(documents:list[Document], **kwargs:Any) -> list[str] {
        # """
        # Add or update documents in the vectorstore.

        # :param documents (list[Document]) – Documents to add to the vectorstore.
        # :param kwargs (Any)
        # :returns List of IDs of the added texts.
        # """
        try {

            return self.get_vectorstore().add_documents(
                documents = documents,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can get_embedding_model() {
        # interpret the provider and return the appropriate model

        if(self.embedding_model_provider == "openai") {
            if(self.embedding_model_name) {
                return OpenAIEmbeddings(model=self.embedding_model_name, api_key=self.embedding_model_api_key);
            }
            return OpenAIEmbeddings(api_key=self.embedding_model_api_key);
        } elif(self.embedding_model_provider == "azure") {

            if(self.embedding_model_name) {
                return AzureOpenAIEmbeddings(
                    azure_endpoint = self.embedding_model_endpoint,
                    model=self.embedding_model_name,
                    api_key=self.embedding_model_api_key,
                    open_api_version=self.embedding_model_api_version
                );
            }
            return AzureOpenAIEmbeddings(
                    azure_endpoint = self.embedding_model_endpoint,
                    api_key=self.embedding_model_api_key,
                    open_api_version=self.embedding_model_api_version
                );
        } elif(self.embedding_model_provider == "jivas") {

            if(self.embedding_model_name) {
                return JivasEmbeddings(
                    base_url = self.embedding_model_endpoint,
                    api_key=self.embedding_model_api_key,
                    model=self.embedding_model_name
                );
            }
            return JivasEmbeddings(
                base_url = self.embedding_model_endpoint,
                api_key=self.embedding_model_api_key
            );
        } else {
            self.logger.error(f"Provider {self.embedding_model_provider} not supported for embedding model {self.embedding_model_name}");
            return None;
        }
    }

    can similarity_search(query:str, k:int=10, filter:str|None='', **kwargs:Any) -> List[Document] {
        # """
        # Return typesense documents most similar to query.

        # :param query (str) – Text to look up documents similar to.
        # :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        # :param filter (str | None) – typesense filter_by expression to filter documents on
        # :param kwargs (Any)
        # :returns List of Documents most similar to the query and score for each
        # """

        try {

            return self.get_vectorstore().similarity_search(
                query = query,
                k = k,
                filter = filter,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can similarity_search_with_score(query:str, k:int=10, filter:str|None='', **kwargs:Any) -> List[Tuple[Document,float]] {
        # """
        # Return typesense documents most similar to query.

        # :param query (str) – Text to look up documents similar to.
        # :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        # :param filter (str | None) – typesense filter_by expression to filter documents on
        # :param kwargs (Any)
        # :returns List of Documents most similar to the query and score for each
        # """

        try {

            return self.get_vectorstore().similarity_search_with_score(
                query = query,
                k = k,
                filter = filter,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can max_marginal_relevance_search(query:str, k:int=10, fetch_k:int = 20, lamda_mult:float = 0.5, **kwargs:Any) -> List[Document,float] {
        # """
        # Maximal marginal relevance optimizes for similarity to query AND diversity among selected documents.

        # :param query (str) – Text to look up documents similar to.
        # :param k (int) – Number of Documents to return. Defaults to 10. Minimum 10 results would be returned.
        # :param filter (str | None) – typesense filter_by expression to filter documents on
        # :param kwargs (Any)
        # :returns List of Documents most similar to the query and score for each
        # """

        try {

            return self.get_vectorstore().max_marginal_relevance_search(
                query = query,
                k = k,
                fetch_k = fetch_k,
                lamda_mult = lamda_mult,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can vector_similarity_search(embedding:list[float], k:int=10, **kwargs:Any) -> List[Document] {
        # """
        # Return docs most similar to embedding vector.

        # :param embedding (list[float]) – Embedding to look up documents similar to.
        # :param k (int) – Number of Documents to return. Defaults to 4.
        # :param (Any) – Arguments to pass to the search method.
        # :returns List of Documents most similar to the query vector.
        # """

        try {

            return self.get_vectorstore().similarity_search_by_vector(
                embedding = embedding,
                k = k,
                **kwargs
            );

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can metadata_search(metadata:dict, k:int = 10, **kwargs:Any) -> List[Document] {
        # """
        # Override to return documents matching metadata.
        # Ensure to implement any necessary translations of metadata dict into the vectorstore's filter format

        # :param metadata (dict) – Metadata to look up documents similar to.
        # :returns List of Documents most similar to the query and score for each
        # """
    }

    can list_documents(page:int = 1, per_page:int = 10) -> dict {
        # """
        # Override to list all documents in the vectorstore with pagination.

        # :param page (int) – the current page.
        # :param per_page (int) – the maximum number of items per page
        # :param params (Dict) – Optional list of typesense params.

        # :returns List of documents with this structure
        # {
        #     'page': 1,
        #     'per_page': 10,
        #     'total': 114,
        #     'documents': [ {id:'abc', 'metadata':{}, 'text':'xyz'} ]
        # }
        # """
    }

    can get_document(id:str) -> bool {
        # """
        # Override to retrieves a document by its ID.

        # :param id: ID of the document

        # :return: the document
        # """
    }

    can update_document(id:str, data:dict) -> bool {
        # """
        # Override to update a document by its ID.

        # :param id: ID of the document to update
        # :param data: fields of the document to update, e.g. text, metadata

        # :return: the document
        # """
    }

    can delete_document(id:str) -> bool {
        # """
        # Override to delete a document by its ID.

        # :param id: ID of the document to delete

        # :return: the deleted document
        # """
    }

    can delete_collection() -> bool {
        # """
        # Override to delete an entire collection by its name.

        # :return: bool
        # """
    }

    can healthcheck() -> Union[bool, dict] {
        try {
            if(not self.embedding_model_provider){
                return {
                    "status": False,
                    "message": "Embedding model provider not set",
                    "severity": "error"
                };
            }

            embedded_texts = self.get_embedding_model().embed_documents(["this is a test"]);
            if not embedded_texts {
                return {
                    "status": False,
                    "message": "Embedding model not functional. Check your configuration",
                    "severity": "error"
                };
            }

            # check if the vectorstore is available
            if(not self.get_vectorstore()) {
                return {
                    "status": False,
                    "message": "Vectorstore not configured",
                    "severity": "error"
                };
            }

            return True;
        } except Exception as e {
            return False;
        }
    }

}
