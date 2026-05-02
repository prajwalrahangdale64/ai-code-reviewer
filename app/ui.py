import streamlit as st
import sys, os, json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.llm import review_code
from core.github_fetcher import fetch_pr_info, fetch_file_content, fetch_pr_code
from core.storage import save_dump

st.set_page_config(page_title="AI Code Reviewer", layout="wide")
st.title("🔍 AI Code Reviewer")

input_mode = st.radio("Input method", ["Paste Code", "Upload File", "GitHub PR URL"])

code = ""


# ── Shared review display ──────────────────────────────────────────────────────

def _display_review(result: dict) -> None:
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

    def _line_label(lines):
        if len(lines) == 1:      return f"Line {lines[0]}"
        if len(lines) <= 4:      return "Lines " + ", ".join(str(l) for l in lines)
        return f"Lines {lines[0]}–{lines[-1]}"

    # ── Issues ────────────────────────────────────────────────────────────────
    st.subheader("🐛 Issues Found")
    if issues:
        for idx, issue in enumerate(issues, 1):
            sev   = issue["severity"].upper()
            cat   = issue["category"].lower()
            badge = SEVERITY_BADGE.get(sev, "⚪")
            icon  = CATEGORY_ICON.get(cat, "⚙️")
            ll    = _line_label(issue.get("line_numbers", []))

            with st.expander(
                f"{badge} [{sev}]  {icon} {cat}  —  {issue['message']}   📍 `{ll}`"
            ):
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", cat.replace("_", " ").title())
                col2.metric("Severity", sev.title())
                col3.metric("Location", ll)
                st.markdown("---")
                original = issue.get("original_code", "").strip()
                st.markdown("**🔎 Problematic Code**")
                st.code(original if original else "— not available —", language="python")
    else:
        st.success("✅ No issues found — great code!")

    st.divider()

    # ── Suggestions ───────────────────────────────────────────────────────────
    st.subheader("💡 Suggestions & Fixes")
    if issues:
        st.markdown("#### 🔧 Issue-Specific Fixes")
        for idx, issue in enumerate(issues, 1):
            sev   = issue["severity"].upper()
            cat   = issue["category"].lower()
            badge = SEVERITY_BADGE.get(sev, "⚪")
            icon  = CATEGORY_ICON.get(cat, "⚙️")
            ll    = _line_label(issue.get("line_numbers", []))

            with st.expander(
                f"Fix #{idx}  {badge} [{sev}]  {icon} {cat}  —  {issue['message']}   📍 `{ll}`"
            ):
                left, right = st.columns(2)
                with left:
                    st.markdown("**🔎 Before**")
                    st.code(
                        issue.get("original_code", "").strip() or "— not available —",
                        language="python",
                    )
                with right:
                    st.markdown("**✅ After**")
                    st.code(
                        issue.get("correction", "").strip() or "— not available —",
                        language="python",
                    )

    general = result.get("suggestions", [])
    if general:
        st.markdown("#### 📋 General Recommendations")
        for i, s in enumerate(general, 1):
            st.markdown(f"**{i}.** {s}")


# ── File-tree helpers ──────────────────────────────────────────────────────────

def _build_tree(files: list[dict]) -> dict:
    """Convert a flat list of file dicts into a nested dict tree.
    Leaves are file dicts (have a 'raw_url' key); interior nodes are plain dicts.
    """
    tree: dict = {}
    for f in files:
        parts = f["filename"].split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = f
    return tree


def _render_tree(node: dict) -> None:
    """Recursively render a tree node. Folders → expanders, files → buttons."""
    selected_filename = (st.session_state.get("selected_file") or {}).get("filename")

    for name in sorted(node.keys()):
        value = node[name]
        is_file = "raw_url" in value          # leaf node

        if is_file:
            is_selected = value["filename"] == selected_filename
            status_icon = {"added": "🟢", "removed": "🔴", "modified": "🟡"}.get(
                value.get("status", "modified"), "🟡"
            )
            label = f"{'✅' if is_selected else status_icon} {name}"
            if st.button(label, key=f"file__{value['filename']}"):
                st.session_state.selected_file  = value
                st.session_state.pr_result      = None   # clear stale review
                st.rerun()
        else:
            with st.expander(f"📁 {name}", expanded=True):
                _render_tree(value)


# ── Input modes ────────────────────────────────────────────────────────────────

if input_mode == "Paste Code":
    code = st.text_area("Paste your code here", height=300)

elif input_mode == "Upload File":
    uploaded = st.file_uploader("Upload a .py file", type=["py", "txt", "js", "ts"])
    if uploaded:
        code = uploaded.read().decode("utf-8")
        st.code(code, language="python")

# ── GitHub PR URL mode ─────────────────────────────────────────────────────────
elif input_mode == "GitHub PR URL":
    pr_url = st.text_input(
        "Enter GitHub PR URL",
        placeholder="https://github.com/owner/repo/pull/123",
    )

    # ① Fetch PR info when URL changes
    if pr_url and st.session_state.get("pr_url") != pr_url:
        try:
            with st.spinner("Fetching PR info from GitHub..."):
                pr_info = fetch_pr_info(pr_url)
            st.session_state.pr_url           = pr_url
            st.session_state.pr_info          = pr_info
            st.session_state.selected_file    = None
            st.session_state.pr_result        = None
        except (ValueError, Exception) as e:
            st.error(f"❌ {e}")
            st.session_state.pr_info = None

    pr_info = st.session_state.get("pr_info")

    if pr_info:
        # ② Branch info
        st.markdown(f"### 🔀 {pr_info['title']}")
        col1, col2 = st.columns(2)
        col1.info(f"**Source branch:** `{pr_info['source_branch']}`")
        col2.info(f"**Target branch:** `{pr_info['base_branch']}`")
        st.divider()

        # ③ File tree
        st.markdown("### 📂 Changed Files")
        st.caption("🟢 added · 🟡 modified · 🔴 removed · ✅ selected")

        changed = pr_info.get("changed_files", [])
        if not changed:
            st.warning("No supported code files found in this PR (.py, .js, .ts, etc.)")
        else:
            tree = _build_tree(changed)
            _render_tree(tree)

        # ④ Review selected file
        selected = st.session_state.get("selected_file")
        if selected:
            st.divider()
            st.success(f"**Selected:** `{selected['filename']}`")

            if st.button("🔍 Review Selected File"):
                try:
                    with st.spinner("Fetching file content..."):
                        fetched_code = fetch_file_content(selected["raw_url"])
                    with st.spinner("Analyzing code..."):
                        st.session_state.pr_result = review_code(fetched_code)
                    label = selected["filename"].replace("/", "_")
                    saved_path = save_dump(st.session_state.pr_result, label=label)
                    st.caption(f"💾 Dump saved → `{saved_path}`")
                except (ValueError, Exception) as e:
                    st.error(f"❌ {e}")

        if st.session_state.get("pr_result"):
            st.divider()
            _display_review(st.session_state.pr_result)
            st.download_button(
                label="⬇️ Download Error Dump",
                data=json.dumps(st.session_state.pr_result, indent=2),
                file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

# ── Paste / Upload review button ───────────────────────────────────────────────
if input_mode in ("Paste Code", "Upload File"):
    if st.button("Review Code") and code.strip():
        with st.spinner("Analyzing code..."):
            result = review_code(code)
        saved_path = save_dump(result, label="paste_or_upload")
        st.caption(f"💾 Dump saved → `{saved_path}`")
        _display_review(result)
        st.download_button(
            label="⬇️ Download Error Dump",
            data=json.dumps(result, indent=2),
            file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )