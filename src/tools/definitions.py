from tools.base import Tool, tool_registry
from vector_db.retrieval import retriever
from config import config
import time


class KnowledgeSearchTool:
    name = "knowledge_search"
    description = "Search the knowledge base for relevant information. Use this to find answers from FAQs, policies, and procedures."

    def run(self, query: str, category: str = None, top_k: int = None):
        start_time = time.time()

        search_query = query
        if category:
            search_query = f"Category: {category}\nQuery: {query}"

        documents, scores = retriever.hybrid_search(
            query=search_query, top_k=top_k or config.TOP_K
        )

        context_parts = []
        for doc in documents:
            source = doc["metadata"].get("source", "Knowledge Base")
            section = doc["metadata"].get("section", "")
            context_parts.append(
                f"Source: {source} | Section: {section}\n\n{doc['text']}"
            )

        combined_context = "\n\n---\n\n".join(context_parts)

        processing_time = time.time() - start_time

        return {
            "results": documents,
            "context": combined_context,
            "scores": scores,
            "processing_time": processing_time,
        }


class IntentClassifierTool:
    name = "classify_intent"
    description = "Classify the user's query to determine intent, category, and sentiment. Use this to understand what the user needs."

    def run(self, query: str, conversation_history: list = None):
        import google.generativeai as genai

        start_time = time.time()
        model = genai.GenerativeModel(config.LLM_MODEL)

        conversation_text = ""
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                conversation_text += f"{role}: {msg.get('content', '')}\n"

        conversation_text += f"User: {query}"

        prompt = f"""Analyze this customer support query and classify it.

Conversation:
{conversation_text}

Provide analysis in JSON format:
{{
    "category": "billing|technical|shipping|returns|general|account",
    "intent": "get_info|troubleshoot|report_issue|request_action|complaint",
    "sentiment": "positive|neutral|negative|frustrated",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Return only valid JSON, no markdown formatting."""

        response = model.generate_content(prompt)

        try:
            result = json.loads(response.text)
        except:
            result = {
                "category": "general",
                "intent": "get_info",
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "reasoning": "Default classification due to parsing error",
            }

        processing_time = time.time() - start_time

        return {**result, "processing_time": processing_time}


class TicketCreatorTool:
    name = "create_ticket"
    description = "Create a support ticket for human escalation when the query cannot be resolved automatically."

    def run(self, user_query: str, category: str, sentiment: str, reason: str = None):
        import uuid

        start_time = time.time()

        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

        response = f"""Thank you for reaching out. Your inquiry requires specialist attention.

I've created support ticket **{ticket_id}** and a member of our team will assist you shortly.

Ticket Details:
- Ticket ID: {ticket_id}
- Category: {category}
- Priority: {"High" if sentiment == "frustrated" else "Normal"}
- Expected Response: Within 1 hour

You'll receive updates via email. We appreciate your patience!"""

        processing_time = time.time() - start_time

        return {
            "ticket_id": ticket_id,
            "response": response,
            "category": category,
            "sentiment": sentiment,
            "processing_time": processing_time,
        }


class ResponseGeneratorTool:
    name = "generate_response"
    description = "Generate a helpful response to the user based on retrieved knowledge and context."

    def run(
        self,
        query: str,
        context: str,
        category: str,
        sentiment: str,
        confidence: float,
        conversation_history: list = None,
    ):
        import google.generativeai as genai

        start_time = time.time()
        model = genai.GenerativeModel(config.LLM_MODEL)

        system_prompt = f"""You are a helpful, empathetic customer support agent.

Guidelines:
- Use the provided knowledge base context for accurate information
- Be concise but helpful (keep responses under 200 words)
- If unsure, offer to escalate to a specialist
- Be professional and friendly
- Acknowledge the customer's sentiment and emotion

Category: {category}
Customer Sentiment: {sentiment}
Confidence in retrieved context: {confidence:.2%}

Knowledge Base Context:
{context}

Important: If confidence is below {config.CONFIDENCE_THRESHOLD} or you don't have clear answer, suggest escalation."""

        conversation_messages = []
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "user" if msg.get("role") == "user" else "model"
                conversation_messages.append(
                    {"role": role, "parts": [{"text": msg.get("content", "")}]}
                )

        conversation_messages.append({"role": "user", "parts": [{"text": query}]})

        response = model.generate_content(
            contents=conversation_messages,
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=config.LLM_TEMPERATURE, max_output_tokens=500
            ),
        )

        processing_time = time.time() - start_time

        return {
            "response": response.text,
            "needs_escalation": (
                confidence < config.CONFIDENCE_THRESHOLD
                or sentiment == "frustrated"
                or any(
                    phrase in response.text.lower()
                    for phrase in [
                        "escalate",
                        "specialist",
                        "supervisor",
                        "unable to help",
                    ]
                )
            ),
            "processing_time": processing_time,
        }


knowledge_search_tool = KnowledgeSearchTool()
classify_intent_tool = IntentClassifierTool()
create_ticket_tool = TicketCreatorTool()
generate_response_tool = ResponseGeneratorTool()

tool_registry.register(
    Tool(
        "knowledge_search", knowledge_search_tool.description, knowledge_search_tool.run
    )
)
tool_registry.register(
    Tool("classify_intent", classify_intent_tool.description, classify_intent_tool.run)
)
tool_registry.register(
    Tool("create_ticket", create_ticket_tool.description, create_ticket_tool.run)
)
tool_registry.register(
    Tool(
        "generate_response",
        generate_response_tool.description,
        generate_response_tool.run,
    )
)
