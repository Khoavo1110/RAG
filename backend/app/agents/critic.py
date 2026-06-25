import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from backend.app.config import settings
from backend.app.agents.tools import chunker  # Reuse the embedder/chunker context if needed

class CriticResult(BaseModel):
    is_valid: bool = Field(description="True if the draft answer is fully faithful to the context and complete, False otherwise.")
    feedback: str | None = Field(default=None, description="Detailed explanation of why the draft is invalid (hallucinations, incorrect facts, or missing details).")
    refinement_query: str | None = Field(default=None, description="A new query to search in the databases for missing info.")

def get_llm(temperature: float = 0.0):
    """
    Helper to get the appropriate LLM client based on environment configuration.
    """
    if settings.GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        # Check model name prefix
        model = settings.LLM_MODEL
        if not model.startswith("gemini-"):
            model = "gemini-2.5-flash"
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature
        )
    elif settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        # Check if using GitHub Models
        if "github" in settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base="https://models.inference.ai.azure.com",
                temperature=temperature
            )
        else:
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
    else:
        raise ValueError("No LLM API keys found in settings (GEMINI_API_KEY or OPENAI_API_KEY).")

class CriticAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.0)
        
        self.system_prompt = (
            "You are a meticulous Critic Agent in an Agentic RAG system.\n"
            "Your job is to evaluate a draft answer against the retrieved context to verify its accuracy (faithfulness) and completeness.\n\n"
            "Please evaluate:\n"
            "1. Faithfulness (Grounding): Are all facts in the draft answer fully supported by the retrieved context? "
            "If the draft contains ANY information not present in the context, it is unfaithful (hallucination).\n"
            "2. Completeness: Does the draft answer fully and directly address the user's query? "
            "If the query asks about details that are missing from the context but can be found in the system, suggest a refinement query.\n\n"
            "Respond in JSON matching the schema of CriticResult."
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "User Query: {query}\n\nRetrieved Context:\n{context}\n\nDraft Answer:\n{draft_answer}")
        ])

        try:
            self.structured_llm = self.llm.with_structured_output(CriticResult)
        except Exception as e:
            # Fallback if with_structured_output is not supported
            print(f"Structured output not supported on this model: {e}. Falling back to manual JSON parsing.")
            self.structured_llm = None

    async def evaluate(self, query: str, context: str, draft_answer: str) -> CriticResult:
        """
        Evaluate the draft answer.
        Returns a CriticResult object.
        """
        if not context.strip():
            # If no context was retrieved, the answer cannot be verified.
            return CriticResult(
                is_valid=False,
                feedback="No context was retrieved to verify this answer.",
                refinement_query=query
            )

        messages = self.prompt_template.format_messages(
            query=query,
            context=context,
            draft_answer=draft_answer
        )

        if self.structured_llm:
            try:
                result = await self.structured_llm.ainvoke(messages)
                return result
            except Exception as e:
                print(f"Error in structured invocation: {e}. Falling back to manual parsing.")

        # Fallback manual parsing
        # Append JSON format instructions
        messages_manual = self.prompt_template.format_messages(
            query=query,
            context=context,
            draft_answer=draft_answer
        )
        messages_manual.append(("user", "IMPORTANT: Respond ONLY with a raw JSON object matching: {\"is_valid\": bool, \"feedback\": string_or_null, \"refinement_query\": string_or_null}"))
        
        res = await self.llm.ainvoke(messages_manual)
        content = res.content.strip()
        
        # Clean markdown code block wraps if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
            return CriticResult(
                is_valid=data.get("is_valid", False),
                feedback=data.get("feedback"),
                refinement_query=data.get("refinement_query")
            )
        except Exception as pe:
            # Safe default
            return CriticResult(
                is_valid=False,
                feedback=f"Failed to parse Critic response JSON: {pe}. Raw output: {content}",
                refinement_query=query
            )

# Singleton instance
critic_agent = CriticAgent()
