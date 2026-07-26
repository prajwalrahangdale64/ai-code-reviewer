from core.llm import review_code

sample = """
def get_user(id):
    import sqlite3
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {id}")
    return cursor.fetchone()
"""

result = review_code(sample)
print(f"Score: {result['overall_score']}/10")
for issue in result['issues']:
    print(f"[{issue['severity'].upper()}] {issue['category']}: {issue['message']}")
for s in result['suggestions']:
    print(f"  → {s}")