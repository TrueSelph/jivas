import:py logging;
import:py traceback;
import:py from typing { Optional }
import:py from logging { Logger }
import:jac from interact_action { InteractAction }
import:jac from interact_graph_walker { InteractGraphWalker }
import:jac from model_action { ModelAction, ModelActionResult }

node RetrievalInteractAction :InteractAction: {
    # Integrates with vector database for retrieval augmented generation tasks

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    # the directive template for RAG
    has directive:str = "Ignore your own knowledge and assumptions. Use only CONTEXT to craft your response to the question. Do not include any information not found in the CONTEXT. If relevant content is not available in CONTEXT, advise the user that you do not have the relevant information at this time.\n\nCONTEXT: \n{context}\n";
    # the null directive template for RAG
    has null_directive:str = "Ignore the user's query. Let them know that you can't answer it right now, but you'll get back to them as soon as possible. Alternatively, use your roles as an excuse to avoid answering the query altogether.\n";
    # context_rewriting_prompt
    has query_completion_prompt:str = "Based on the conversation history, perform the following tasks:\n\n      1. **Understand the User's Intent**:\n         - Analyze the user's message to determine their intent.\n         - If the message is a **query** (a question or request for information), proceed to step 2.\n         - If the message is **small talk**, a **greeting**, or a **statement** that does not seek additional information, proceed to step 3.\n\n      2. **Refine the User's Query**:\n         - Rephrase and enhance the user's query by incorporating relevant details from the conversation history.\n         - Make the query more explicit and detailed to clearly convey the user's request.\n         - Focus solely on refining the query, without providing an answer or additional information.\n\n      3. **Provide the Final Message**:\n         - Output **only** the refined query from step 2 or the original user message if no refinement was necessary.\n         - Do not include any answers, explanations, or additional commentary.\n\n      **Note:** Your task is to **craft a refined query** when applicable, not to answer the query. Ensure that the final output is either the refined query or the original message, with no extra content.";
    # the number of results
    has k:int = 3;
    # the score threshold (smaller numbers are usually more accurate)
    has score_threshold:float = 0.3;
    # max marginal relevance search
    has mmr:bool = False;
    # the vector store action name bound to this retrieval action
    has vector_store_action:str = "";

    has history_size:int = 3;
    has max_statement_length:int = 400;
    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.2;
    has model_max_tokens:int = 10000;

    can healthcheck() -> bool {
        try {
            if (
                self.directive and
                self.null_directive and
                self.query_completion_prompt and
                self.k > 0 and
                self.vector_store_action and
                self.history_size and
                self.model_action and
                self.model_name and
                self.model_temperature and
                self.model_max_tokens > 0 and
                self.max_statement_length > 0
            ) {
                return True;
            }
            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }

    can touch(visitor: interact_graph_walker) -> bool {
        # implementation of touch for retrieval interact
        if(visitor.utterance) {
            return True;
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # implementation of execute for retrieval interact

        # first prepare the query with context completion
        if(not (query := self.prepare_query(visitor)) ) {
            query = visitor.utterance;
        }

        visitor.interaction_node.context_data['RetrievalInteractAction_query'] = query;
        # update the rewritten utterance
        visitor.utterance = query;

        # handle context, if any and queue directive
        if(context := self.retrieve_context(query)) {
            context_directive = self.directive.format(context=context);
            visitor.interaction_node.add_directive(directive = context_directive);
        } else {
            directives = visitor.interaction_node.get_directives();
            if(not directives){
                visitor.interaction_node.add_directive(directive = self.null_directive);
            }
        }

        return visitor.export();
    }

    can prepare_query(visitor: interact_graph_walker) -> str {

        query = None;

        # grab the history, if any
        if (statements := visitor.frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length)) {

            prompt_messages = [];
            prompt_messages.extend(statements);
            prompt_messages.extend([{"system": self.query_completion_prompt}]);

            result = None;

            if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {

                 if( model_action_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = {},
                    kwargs = {
                        "model_name": self.model_name,
                        "model_temperature": self.model_temperature,
                        "model_max_tokens": self.model_max_tokens
                    },
                    interaction_node = visitor.interaction_node
                )) {
                    # add the resulting intent, if any to the interaction to trigger the relevant action(s)
                    query = model_action_result.get_result();
                }
            }
        }

        return query;
    }


    can retrieve_context(query:str, filter:Optional[str] = "") -> str {
        # override to implement custom retrieval operation

        # """
        # retrieves document for context

        # :param visitor (InteractGraphWalker) – interact graph walker state containing interaction, utterance, etc.

        # :returns string of context data relevant for RAG or None
        # """

        if( vector_store_action := self.get_agent().get_actions().get(action_label = self.vector_store_action) ) {

            texts = "";

            if(self.mmr) {
                if(documents := vector_store_action.max_marginal_relevance_search(query = query, k = self.k)) {

                    for doc in documents {
                        texts += f"{doc.page_content} --- ";
                    }

                    return texts;
                }
            }
            # perform similarity search
            if(documents_and_score := vector_store_action.similarity_search_with_score(query = query, k = self.k, filter = filter)) {
            # iterate through resultset and return top-ranked texts

                for (doc, score) in documents_and_score {
                    if(self.score_threshold >= score) {
                        texts += f"{doc.page_content} --- ";
                    }
                }

                return texts;
            }
        }

        return None;
    }

}