## Project Structure

```
ai-code-reviewer/
├── app/
│   └── ui.py              # Streamlit UI
├── core/
│   ├── llm.py             # LLM-based code review logic
│   ├── github_fetcher.py  # GitHub PR code fetcher
│   ├── storage.py         # Saves review outputs (error dumps)
│   └── error_dumps/       # Stored JSON review results
├── main.py                # App entry point
├── requirements.txt       # Python dependencies
└── .env                   # Local API keys (not committed)
```

## Project Flow

1) User input:
  The app accepts code in three ways: pasted code, uploaded file, or GitHub PR URL through the Streamlit interface.
2) GitHub PR support:
  When a PR URL is provided, the system retrieves PR metadata, shows the changed files in a folder-tree view, and lets the user select a specific file for review.
4) LLM-based review:
  The combined code is passed through a LangChain pipeline using ChatGroq, with a strict structured output schema (Pydantic). The input is line-numbered to ensure precise referencing. The model returns granular, line-specific issues with category, severity, exact problematic code, and concrete corrected replacements—along with an overall quality score and high-level improvement suggestions.
5) Error dump storage:
  After each review, the result is saved locally as a timestamped JSON file in an `error_dumps/` folder for later inspection or debugging.
7) Review output display:
  The Streamlit interface presents the generated review in a structured format, including the overall score, detailed issue breakdowns, before/after fixes, and general recommendations.

## UI Preview

### Screenshot 1:

  <img width="1366" height="559" alt="Screenshot (583)" src="https://github.com/user-attachments/assets/39d2a619-eabb-47b9-b318-2792856c7150" />
  
---

### Screenshot 2:

  <img width="1366" height="226" alt="Screenshot (584)" src="https://github.com/user-attachments/assets/bf96152a-c329-48cf-a65b-1185b69ef8b4" />

---

### Screenshot 3:

  <img width="1366" height="562" alt="Screenshot (585)" src="https://github.com/user-attachments/assets/4f616a87-d8d2-4015-9c6e-3d9e8ef01dc7" />

---

### Screenshot 4:

  <img width="1366" height="537" alt="Screenshot (586)" src="https://github.com/user-attachments/assets/3c77a3ea-4571-436c-b70e-570ee79a8955" />

---

### Screenshot 5:

  <img width="1366" height="409" alt="Screenshot (587)" src="https://github.com/user-attachments/assets/faee5490-8b55-40a5-b84a-6e1946384825" />

---

## Error dump file structure:

```
{
  "overall_score": 6,
  "issues": [
    {
      "category": "readability",
      "message": "The function 'runner' is not documented.",
      "severity": "low",
      "line_numbers": [36],
      "original_code": "@pytest.fixture\ndef runner():",
      "correction": "@pytest.fixture\ndef runner():\n    \"\"\"Fixture that ...\"\"\""
    }
  ],
  "suggestions": [
    "Consider adding more test cases to cover different scenarios.",
    "Consider using a linter to enforce coding standards."
  ]
}
```
