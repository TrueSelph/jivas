import json;
import logging;
import traceback;
import from typing { Optional, Union }
import from logging { Logger }
import from jivas.agent.action.interact_action { InteractAction }
import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jivas.agent.action.model_action { ModelAction, ModelActionResult }

node RetrievalInteractAction(InteractAction) {
    # Integrates with vector database for retrieval augmented generation tasks

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    # the directive template for RAG
    has directive:str = """
    Use CONTEXT as your knowledge base, intelligently assess the user question, review CONTEXT for context and finally produce an informative and accurate response.
    Do not include any information outside of the CONTEXT. If relevant content is not available in CONTEXT, advise the user that you do not have the relevant information at this time.

    CONTEXT:
    {context}

    """;

    # the null directive template for RAG
    has null_directive:str = "No context information was retrieved based on user utterance. If the user utterance is a question which relates to your knowledge, advise them that you do not have the relevant information at this time to answer their question.\n";

    # context_rewriting_prompt
    has query_completion_prompt:str = """
    Based on the conversation history, perform the following tasks:

    1. **Analyze Context and Intent**:
        - Review the conversation history to establish context
        - Determine if the user's message is a query requiring information
        - Skip refinement for small talk, greetings, or acknowledgments

    2. **Query Refinement** (if applicable):
        - Enhance the query by incorporating key context from conversation history
        - Make implicit references explicit using historical context
        - Ensure the query is specific, clear, and self-contained
        - Remove ambiguous pronouns or references
        - Maintain original intent while improving clarity

    3. **Output Format**:
        Return a JSON object (no delimiters!) with the following keys:
         - "query": "the refined query or original message",
         - "is_query": true/false (true if message requires context search, false otherwise)

    Note: Focus solely on query clarification and refinement.
    The 'query' field should contain only the refined query or original message without commentary.
    The 'is_query' field should be true for information-seeking questions and false for casual conversation.

    """;

    # the number of results
    has k:int = 3;
    # the score threshold (smaller numbers are usually more accurate)
    has score_threshold:float = 0.3;
    # max marginal relevance search
    has mmr:bool = False;
    # whether to return metadata with context or not
    has metadata:bool = False;
    # the vector store action name bound to this retrieval action
    has vector_store_action:str = "";
    has history_size:int = 3;
    has max_statement_length:int = 400;
    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.2;
    has model_max_tokens:int = 10000;

    def on_register() {

        # load the agent's default vector store action if none is specified
        if not self.vector_store_action {
            self.vector_store_action = (self.get_agent()).vector_store_action;
        }
    }

    def touch(visitor: agent_graph_walker) -> bool {
        # implementation of touch for retrieval interact
        if(visitor.utterance) {
            return True;
        }
    }

    def execute(visitor: agent_graph_walker) {

        # first prepare the query with context completion
        # prepare query using conversation history or fallback to original utterance
        query = self.process_query(visitor);

        if(not query) {
            # if no query is generated, return early
            return;
        }

        if not query.get("is_query", False) {
            # if the query is not a query, return early
            return;
        }

        # update interaction node with query and context data
        interaction_context = visitor.interaction_node.data_get(key=self.get_type());
        if not interaction_context {
            interaction_context = {};
        }
        interaction_context['query'] = query.get("query", visitor);

        # handle context, if any and queue directive
        if(context_data := self.retrieve_context(interaction_context['query'])) {

            context_directive = None;
            # add raw context to the interaction node
            interaction_context['context'] = context_data;
            # convert context data to JSON for composing the directive
            context_json = json.dumps(context_data);
            # prepare context directive
            context_directive = self.directive.format(context=context_json);
            # add the context directive to the interaction node
            visitor.interaction_node.add_directive(directive = context_directive);
        } else {
            directives = visitor.interaction_node.get_directives();
            if(not directives) {
                visitor.interaction_node.add_directive(directive = self.null_directive);
            }
        }

        visitor.interaction_node.data_set(key=self.get_type(), value=interaction_context);

    }

    def process_query(visitor: agent_graph_walker) -> dict {

        query = {};

        # grab the history, if any
        if (statements := visitor.frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length)) {

            prompt_messages = [];
            prompt_messages.extend(statements);
            prompt_messages.extend([{"human": visitor.utterance}]);
            prompt_messages.extend([{"system": self.query_completion_prompt}]);

            result = None;

            if(model_action := self.get_agent().get_action(action_label=self.model_action)) {

                 if( model_action_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = {},
                    interaction_node = visitor.interaction_node,
                    model_name=self.model_name,
                    model_temperature=self.model_temperature,
                    model_max_tokens=self.model_max_tokens
                )) {
                    # add the resulting intent, if any to the interaction to trigger the relevant action(s)
                    query = model_action_result.get_json_result();
                }
            }
        }

        return query;
    }


    def retrieve_context(query:str, filter:Optional[str] = "") -> list {
        # override to implement custom retrieval operation

        # """
        # retrieves document for context

        # :param visitor (InteractGraphWalker) – interact graph walker state containing interaction, utterance, etc.

        # :returns context data relevant for RAG or [] if no context is found
        # """
        context_data = [];

        if(vector_store_action := self.get_agent().get_action(action_label=self.vector_store_action)) {

            if(self.mmr) {
                if(documents := vector_store_action.max_marginal_relevance_search(query=query, k=self.k)) {
                    for doc in documents {
                        context_item = {
                            "content": doc.page_content
                        };
                        if(self.metadata) {
                            context_item["metadata"] = doc.metadata;
                        }
                        context_data.append(context_item);
                    }
                    if context_data {
                        return json.dumps(context_data);
                    }
                }
            } else {
                # perform similarity search
                if(documents_and_score := vector_store_action.similarity_search_with_score(query=query, k=self.k, filter=filter)) {
                    for (doc, score) in documents_and_score {
                        if(score <= self.score_threshold) {
                            context_item = {
                                "content": doc.page_content
                            };
                            if(self.metadata) {
                                context_item["metadata"] = doc.metadata;
                            }
                            context_data.append(context_item);
                        }
                    }
                }
            }
        }

        return context_data;
    }

    def healthcheck() -> Union[bool, dict] {

        vector_store_action = self.get_agent().get_action(action_label=self.vector_store_action);
        if(not vector_store_action) {
            return {
                "status": False,
                "message": f"Unable to find a valid vector store action. Check your configuration and try again.",
                "severity": "error"
            };
        }

        return True;
    }

}