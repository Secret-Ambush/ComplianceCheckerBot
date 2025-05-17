def generate_compliance_report(documents, results):
    lines = []
    lines.append("# 📋 Compliance Report\n")

    # Matched documents
    lines.append("## 📎 Matched Documents:")
    for doc_type, doc in documents.items():
        if doc_type == "reference":
            continue
        filename = doc.get("filename", "Unknown")
        lines.append(f"- **{doc_type.capitalize()}**: `{filename}`")
    lines.append("\n---\n")

    # Rule Results
    lines.append("## ✅❌ Rule Evaluation Summary:")
    passed = failed = 0

    for res in results:
        rule_id = res.get("rule_id", "Unknown Rule")
        status = "✅ PASS" if res["result"] == "pass" else "❌ FAIL"
        description = res.get("reason", "Passed")
        lines.append(f"### {status} – `{rule_id}`")
        lines.append(f"- **Result**: {res['result'].upper()}")
        if res["result"] == "fail":
            lines.append(f"- **Reason**: {description}")
            if "llm_commentary" in res:
                lines.append(f"- **LLM Insight**: {res['llm_commentary']}")
            failed += 1
        else:
            passed += 1
        lines.append("")  # blank line

    total = passed + failed
    lines.append("\n---\n")
    lines.append("## 📊 Summary:")
    lines.append(f"- Total rules evaluated: **{total}**")
    lines.append(f"- ✅ Passed: **{passed}**")
    lines.append(f"- ❌ Failed: **{failed}**")

    missing = [r["rule_id"] for r in results if any(v is None for v in r["details"].values())]
    if missing:
        lines.append(f"- ⚠️ Rules with missing inputs: {', '.join(missing)}")

    return "\n".join(lines)
