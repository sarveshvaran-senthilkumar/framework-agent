import json

import config
import database
from rule_generator import call_llm
from knowledge_graph import get_related


CATEGORY_PROMPT = """Given this user query about construction document comparison,
identify which construction categories are relevant.

Available categories: {categories}

User query: {query}

Output ONLY a JSON array of relevant category names. Example: ["Concrete", "Structural"]"""


import re

def identify_categories(query, available_categories):
    raw = call_llm(CATEGORY_PROMPT.format(categories=", ".join(available_categories), query=query))
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start != -1 and end != 0:
        try:
            parsed = json.loads(raw[start:end])
            if isinstance(parsed, list) and parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback to keyword matching
    words = set(re.findall(r'\w+', query.lower()))
    matched = []
    for cat in available_categories:
        cat_lower = cat.lower()
        if cat_lower in query.lower() or any(w in cat_lower for w in words if len(w) > 3):
            matched.append(cat)
    return matched if matched else ["Concrete", "Structural"]


def retrieve_rules(query, graph):
    all_cats = database.get_categories()
    cats = identify_categories(query, all_cats)

    # Prioritize direct category matches
    direct_cats = set(c.lower() for c in cats)
    direct_rules = database.find_by_categories(list(direct_cats))

    # Expand via knowledge graph if we have few rules (< 30)
    expanded_rules = []
    if len(direct_rules) < 30:
        expanded_cats = set()
        for cat in cats:
            for related in get_related(graph, cat):
                rel_lower = related.lower()
                if rel_lower in {c.lower() for c in all_cats} and rel_lower not in direct_cats:
                    expanded_cats.add(related)
        if expanded_cats:
            expanded_rules = database.find_by_categories(list(expanded_cats))

    # Combine and limit to 50 rules to prevent HTTP 400 Bad Request due to context limits
    rules = (direct_rules + expanded_rules)[:50]
    final_cats = list(set(r.get("category", "") for r in rules))

    return {"query": query, "categories": final_cats, "rules": rules, "rule_count": len(rules)}


def build_system_prompt(rules):
    lines = [
        "You are a Construction Validation Expert.",
        "Use ONLY the following rules to validate and compare documents.",
        "For each finding, cite the rule number.",
        ""
    ]
    for i, rule in enumerate(rules, 1):
        cat = rule.get("category", "?")
        attr = rule.get("attribute", "?")
        desc = rule.get("description", "?")
        source = rule.get("source", "?")
        lines.append(f"Rule {i} [{cat}/{attr}]: {desc} (source: {source})")

    lines.append("")
    lines.append("Compare the provided documents against these rules.")
    lines.append("Report: matches, differences, violations, missing components.")
    return "\n".join(lines)
