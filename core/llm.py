import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# ── Pydantic schema ────────────────────────────────────────────────────────────

class Issue(BaseModel):
    category: str = Field(
        description="Exactly one of: readability | security | best_practices | maintainability"
    )
    message: str = Field(
        description="Precise description of the issue. Reference the specific variable, "
                    "function, or construct by name. Do NOT write generic statements."
    )
    severity: str = Field(
        description="Exactly one of: low | medium | high"
    )
    line_numbers: list[int] = Field(
        description="The exact 1-indexed line numbers (from the numbered code) where this "
                    "issue appears. MUST contain at least one number — never leave empty."
    )
    original_code: str = Field(
        description="The exact line(s) of code from the input that contain the issue, "
                    "copied verbatim (without the line-number prefix)."
    )
    correction: str = Field(
        description="The corrected replacement code for the lines in original_code. "
                    "Must be valid, runnable code — not a prose description."
    )


class CodeReview(BaseModel):
    overall_score: int = Field(
        description="Integer from 1 (worst) to 10 (best) reflecting overall code quality."
    )
    issues: list[Issue] = Field(
        description="Every real issue found. One Issue object per distinct problem. "
                    "Do NOT group unrelated problems into one Issue."
    )
    suggestions: list[str] = Field(
        description="High-level improvement suggestions that go beyond the specific issues listed."
    )


# ── LangChain setup ────────────────────────────────────────────────────────────

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior software engineer performing a strict code review.

RULES YOU MUST FOLLOW:
1. The code you receive has line numbers prepended in the format: "   1 | <code>".
   Use those numbers exactly when filling `line_numbers`.
2. Every Issue MUST have at least one line number — never return an empty list.
3. `original_code` must be the verbatim source line(s), stripped of the "N | " prefix.
4. `correction` must be actual corrected code, not prose like "add error handling here".
5. One Issue per distinct problem. Do not lump multiple unrelated issues together.
6. Do not invent issues that are not present. Do not skip real ones.
7. Categories are strictly: readability | security | best_practices | maintainability""",
    ),
    (
        "human",
        "Review the following code.\n\n{code}",
    ),
])

_chain = _prompt | _llm.with_structured_output(CodeReview)


# ── Public function ────────────────────────────────────────────────────────────

def review_code(code: str) -> dict:
    # Pre-number every line so the LLM has unambiguous line references
    numbered_code = "\n".join(
        f"{i + 1:>4} | {line}" for i, line in enumerate(code.splitlines())
    )
    result: CodeReview = _chain.invoke({"code": numbered_code})
    return result.model_dump()