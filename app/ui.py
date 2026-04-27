import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.llm import review_code
from core.github_fetcher import fetch_pr_code          # ← NEW

st.set_page_config(page_title="AI Code Reviewer", layout="wide")
st.title("🔍 AI Code Reviewer")

input_mode = st.radio("Input method", ["Paste Code", "Upload File", "GitHub PR URL"])  # ← NEW option

code = ""

if input_mode == "Paste Code":
    code = st.text_area("Paste your code here", height=300)

elif input_mode == "Upload File":
    uploaded = st.file_uploader("Upload a .py file", type=["py", "txt", "js", "ts"])
    if uploaded:
        code = uploaded.read().decode("utf-8")
        st.code(code, language="python")

# ── NEW: GitHub PR URL mode ────────────────────────────────────────────────────
elif input_mode == "GitHub PR URL":
    pr_url = st.text_input("Enter GitHub PR URL", placeholder="https://github.com/owner/repo/pull/123")
    if pr_url:
        try:
            with st.spinner("Fetching PR files from GitHub..."):
                code = fetch_pr_code(pr_url)
            st.success("✅ PR files fetched successfully!")
            st.code(code, language="python")
        except ValueError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Failed to fetch PR: {e}")
# ── END NEW ───────────────────────────────────────────────────────────────────

if st.button("Review Code") and code.strip():
    with st.spinner("Analyzing code..."):
        result = review_code(code)

    # ── Overall Score ──────────────────────────────────────────────────────────
    score = result["overall_score"]
    color = "green" if score >= 7 else "orange" if score >= 4 else "red"
    st.markdown(f"## Overall Score: :{color}[{score} / 10]")
    st.divider()

    SEVERITY_BADGE = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    CATEGORY_ICON  = {
        "readability":     "📖",
        "security":        "🔒",
        "best_practices":  "✳️",
        "maintainability": "🔧",
    }

    issues = result.get("issues", [])

    # ── Issues Section — WHAT is wrong ────────────────────────────────────────
    st.subheader("🐛 Issues Found")

    if issues:
        for idx, issue in enumerate(issues, 1):
            sev      = issue["severity"].upper()
            cat      = issue["category"].lower()
            badge    = SEVERITY_BADGE.get(sev, "⚪")
            cat_icon = CATEGORY_ICON.get(cat, "⚙️")

            lines = issue.get("line_numbers", [])
            if len(lines) == 1:
                line_label = f"Line {lines[0]}"
            elif len(lines) <= 4:
                line_label = "Lines " + ", ".join(str(l) for l in lines)
            else:
                line_label = f"Lines {lines[0]}–{lines[-1]}"

            expander_title = (
                f"{badge} [{sev}]  {cat_icon} {cat}  —  {issue['message']}   "
                f"📍 `{line_label}`"
            )

            with st.expander(expander_title):
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", cat.replace("_", " ").title())
                col2.metric("Severity", sev.title())
                col3.metric("Location", line_label)

                st.markdown("---")

                original = issue.get("original_code", "").strip()
                st.markdown("**🔎 Problematic Code**")
                if original:
                    st.code(original, language="python")
                else:
                    st.info("Original lines not available.")
    else:
        st.success("✅ No issues found — great code!")

    st.divider()

    # ── Suggestions Section — HOW to fix ──────────────────────────────────────
    st.subheader("💡 Suggestions & Fixes")

    # Part 1: Per-issue fixes (with corrected code)
    if issues:
        st.markdown("#### 🔧 Issue-Specific Fixes")
        for idx, issue in enumerate(issues, 1):
            sev      = issue["severity"].upper()
            cat      = issue["category"].lower()
            badge    = SEVERITY_BADGE.get(sev, "⚪")
            cat_icon = CATEGORY_ICON.get(cat, "⚙️")

            lines = issue.get("line_numbers", [])
            if len(lines) == 1:
                line_label = f"Line {lines[0]}"
            elif len(lines) <= 4:
                line_label = "Lines " + ", ".join(str(l) for l in lines)
            else:
                line_label = f"Lines {lines[0]}–{lines[-1]}"

            fix_title = (
                f"Fix #{idx}  {badge} [{sev}]  {cat_icon} {cat}  —  {issue['message']}   "
                f"📍 `{line_label}`"
            )

            with st.expander(fix_title):
                correction = issue.get("correction", "").strip()
                original   = issue.get("original_code", "").strip()

                left, right = st.columns(2)
                with left:
                    st.markdown("**🔎 Before**")
                    st.code(original if original else "— not available —", language="python")
                with right:
                    st.markdown("**✅ After**")
                    st.code(correction if correction else "— not available —", language="python")

    # Part 2: General high-level suggestions from LLM
    general = result.get("suggestions", [])
    if general:
        st.markdown("#### 📋 General Recommendations")
        for i, s in enumerate(general, 1):
            st.markdown(f"**{i}.** {s}")