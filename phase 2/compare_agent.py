import json
from datetime import datetime, timezone

import config
import database
from rule_generator import call_llm, read_document
from retriever import retrieve_rules, build_system_prompt


DOC_SELECT_PROMPT = """You have these construction documents:
{doc_list}

User wants to: {query}

Which 2 documents are most relevant to compare? Output ONLY valid JSON:
{{"selected": ["file1.txt", "file2.txt"], "reason": "brief explanation"}}"""


COMPARE_PROMPT = """Compare these two documents using the rules in your instructions.

=== DOCUMENT A: {name_a} ===
{text_a}

=== DOCUMENT B: {name_b} ===
{text_b}

Output a structured comparison:
1. Summary
2. Matches (what both agree on)
3. Differences (where they diverge)
4. Rule violations (which rules are broken, by which document)
5. Recommendations"""


def select_documents(query, doc_list):
    names = [d["source"] for d in doc_list]
    prompt = DOC_SELECT_PROMPT.format(doc_list="\n".join(f"- {n}" for n in names), query=query)
    raw = call_llm(prompt)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        return {"selected": names[:2], "reason": "Default: first two documents"}
    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError:
        return {"selected": names[:2], "reason": "Default: first two documents"}


def compare(doc_a, doc_b, system_prompt):
    prompt = COMPARE_PROMPT.format(
        name_a=doc_a["source"], text_a=doc_a["text"][:3000],
        name_b=doc_b["source"], text_b=doc_b["text"][:3000]
    )
    return call_llm(prompt, system=system_prompt)


def run_comparison(query, graph):
    # 1. Retrieve relevant rules
    retrieval = retrieve_rules(query, graph)
    print(f"Retrieved {retrieval['rule_count']} rules from: {retrieval['categories']}")

    # 2. Build system prompt
    system_prompt = build_system_prompt(retrieval["rules"])

    # 3. Select documents
    doc_list = [{"source": p.name} for p in sorted(config.DOCUMENTS.glob("*.txt"))]
    selection = select_documents(query, doc_list)
    print(f"Selected: {selection['selected']}")
    print(f"Reason: {selection.get('reason', 'N/A')}")

    # 4. Read and compare
    selected = selection.get("selected", [])[:2]
    if len(selected) < 2:
        return {"error": "Could not select 2 documents"}

    doc_a = read_document(config.DOCUMENTS / selected[0])
    doc_b = read_document(config.DOCUMENTS / selected[1])

    print("Comparing...")
    report = compare(doc_a, doc_b, system_prompt)

    # 5. Log
    log_entry = {
        "query": query,
        "selected_documents": selected,
        "reason": selection.get("reason", ""),
        "categories": retrieval["categories"],
        "rules_applied": retrieval["rule_count"],
        "report": report,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    log_id = database.log_comparison(log_entry)
    print(f"Logged: {log_id}")

    return {"report": report, "log_id": log_id, "selection": selection}
