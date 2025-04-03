import:py json;
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
    has directive:str = """
Use CONTEXT as your knowledge base, intelligently assess the user question, review CONTEXT for context and finally produce an informative and accurate response.
Do not include any information outside of the CONTEXT. If relevant content is not available in CONTEXT, advise the user that you do not have the relevant information at this time.

CONTEXT:
{context}


""";

    # the directive which is used to generate the response containing references from the matched context
    has ref_directive:str = """
Use CONTEXT as your knowledge base, intelligently assess the user question and perform the following tasks:
a. Review 'content' in CONTEXT for the appropriate context to produce an accurate answer. Do not include any information outside of the CONTEXT.
b. For each applicable item in CONTEXT, include after your response, a formatted list of unique references taken from REF_FIELDS under 'metadata' in CONTEXT.
c. If relevant content is not available in CONTEXT, advise the user that you do not have the relevant information at this time.

REF_FIELDS:
{ref_fields}

CONTEXT:
{context}

""";

    # the null directive template for RAG
    has null_directive:str = "No context information was retrieved based on user utterance. If the user utterance is a question which relates to your knowledge, advise them that you do not have the relevant information at this time to answer their question.\n";

    # context_rewriting_prompt
    has query_completion_prompt:str = """
Based on the conversation history, perform the following tasks:

1. **Understand the User's Intent**:
    - Analyze the user's message to determine their intent.
    - If the message is a **query** (a question or request for information), proceed to step 2.
    - If the message is **small talk**, a **greeting**, or a **statement** that does not seek additional information, proceed to step 3.
2. **Refine the User's Query**:
    - Rephrase and enhance the user's query by incorporating relevant details from the conversation history.
    - Make the query more explicit and detailed to clearly convey the user's request.
    - Focus solely on refining the query, without providing an answer or additional information.
3. **Provide the Final Message**:
    - Output **only** the refined query from step 2 or the original user message if no refinement was necessary.
    - Do not include any answers, explanations, or additional commentary.

**Note:**
Your task is to **craft a refined query** when applicable, not to answer the query.
Ensure that the final output is either the refined query or the original message, with no extra content.

""";

    # the number of results
    has k:int = 3;
    # the score threshold (smaller numbers are usually more accurate)
    has score_threshold:float = 0.3;
    # max marginal relevance search
    has mmr:bool = False;
    # whether to return metadata with context or not
    has metadata:bool = False;
    # whether we wish to process context references or not
    has references:bool = False;
    # the field or fields (comma separated) in the metadata to use for crafting the references
    has metadata_ref_fields:str = "";
    # the vector store action name bound to this retrieval action
    has vector_store_action:str = "";

    has history_size:int = 3;
    has max_statement_length:int = 400;
    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.2;
    has model_max_tokens:int = 10000;

    can touch(visitor: interact_graph_walker) -> bool {
        # implementation of touch for retrieval interact
        if(visitor.utterance) {
            return True;
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # implementation of execute for retrieval interact

        # we safe check the references configuration; if references is true, then metadata is also true
        if(self.references) {

            if (not self.metadata_ref_fields) {
                self.logger.warning("References are enabled, but metadata_ref_fields is not set. Turning 'references' off.");
                self.references = False;
            } elif (not self.metadata) {
                self.logger.warning("References are enabled, but metadata is not. Setting metadata to True.");
                self.metadata = True;
            }

        }

        # first prepare the query with context completion
        if(not (query := self.prepare_query(visitor)) ) {
            query = visitor.utterance;
        }

        visitor.interaction_node.context_data['RetrievalInteractAction_query'] = query;
        # update the rewritten utterance
        visitor.utterance = query;

        # handle context, if any and queue directive
        if(context := self.retrieve_context(query)) {

            context_directive = None;

            # determine if references are in effect
            if(self.references and self.metadata_ref_fields and self.metadata) {
                # if references are in effect, we need to format the context
                # and add the field and context in the reference directive
                context_directive = self.ref_directive.format(context=context, ref_fields=self.metadata_ref_fields);
            } else {
                # otherwise, we just add the context as is
                context_directive = self.directive.format(context=context);
            }

            visitor.interaction_node.add_directive(directive = context_directive);
        } else {
            directives = visitor.interaction_node.get_directives();
            if(not directives) {
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

        # :returns JSON string of context data relevant for RAG or None
        # """
        context_data = [];

        if(vector_store_action := self.get_agent().get_actions().get(action_label=self.vector_store_action)) {

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
                    if context_data {
                        return json.dumps(context_data);
                    }
                }
            }
        }

        return None;
    }

}