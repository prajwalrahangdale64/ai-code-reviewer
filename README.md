## Project Structure

```
ai-code-reviewer/
├── app/
│   └── ui.py              # Streamlit UI
├── core/
│   ├── llm.py             # LLM-based code review logic
│   └── github_fetcher.py  # GitHub PR code fetcher
├── main.py                # App entry point
├── requirements.txt       # Python dependencies
└── .env                   # Local API keys (not committed)
```

## Project Flow

1) User input
  The app accepts code in three ways: pasted code, uploaded file, or GitHub PR URL through the Streamlit interface.
2) GitHub PR support
  When a PR URL is provided, the system retrieves all changed files from the pull request, extracts their full code content, and consolidates them into a single input for end-to-end review.
3) LLM-based review
  The combined code is passed through a LangChain pipeline using ChatGroq, with a strict structured output schema (Pydantic). The input is line-numbered to ensure precise referencing. The model returns granular, line-specific issues with category, severity, exact problematic code, and concrete corrected replacements—along with an overall quality score and high-level improvement suggestions.
4) Review output display
The Streamlit interface presents the generated review in a structured format, including the overall score, detailed issue breakdowns, before/after fixes, and general recommendations.

## UI Preview

### Screenshot 1:

  <img width="1366" height="550" alt="Screenshot (540)" src="https://github.com/user-attachments/assets/683bc910-8a9d-48ca-9713-2d6fb6295cdd" />

---

### Screenshot 2:

  <img width="1366" height="611" alt="Screenshot (541)" src="https://github.com/user-attachments/assets/21c71175-9e8d-4d9e-b548-91c999abc4b5" />

---

### Screenshot 3:

  <img width="1366" height="459" alt="Screenshot (542)" src="https://github.com/user-attachments/assets/df8ef8b2-4c50-4cde-86a5-60cdd3754667" />

---

### Screenshot 4:

  <img width="1366" height="562" alt="Screenshot (543)" src="https://github.com/user-attachments/assets/dda02ddc-ed2b-44f4-9cdd-98aabb9c53f1" />

---

### Screenshot 5:

  <img width="1366" height="295" alt="Screenshot (544)" src="https://github.com/user-attachments/assets/2ea220b9-7d3a-45ac-a10b-8462845e8c96" />

---
