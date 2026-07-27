import json
from collections import defaultdict
from pathlib import Path


def build_graph(rules):
    """Build a concept graph from extracted rules.
    Nodes = unique categories/attributes. Edges = co-occurrence relationships."""
    nodes = {}
    edges = []
    cat_attrs = defaultdict(set)

    for rule in rules:
        cat = rule.get("category", "Unknown")
        attr = rule.get("attribute", "Unknown")
        cat_attrs[cat].add(attr)

        if cat not in nodes:
            nodes[cat] = {"type": "category", "attributes": []}
        if attr not in nodes[cat]["attributes"]:
            nodes[cat]["attributes"].append(attr)

    # Create edges: categories that share attributes are related
    categories = list(cat_attrs.keys())
    for i, cat_a in enumerate(categories):
        for cat_b in categories[i + 1:]:
            shared = cat_attrs[cat_a] & cat_attrs[cat_b]
            if shared:
                edges.append({
                    "from": cat_a,
                    "to": cat_b,
                    "relation": "shares_attributes",
                    "shared": list(shared)
                })

    # Add attribute-level edges within each category
    for cat, attrs in cat_attrs.items():
        for attr in attrs:
            edges.append({"from": cat, "to": attr, "relation": "has_attribute"})

    return {"nodes": nodes, "edges": edges}


def get_related(graph, concept):
    """Return all concepts connected to the given one."""
    related = set()
    for edge in graph["edges"]:
        if edge["from"].lower() == concept.lower():
            related.add(edge["to"])
        elif edge["to"].lower() == concept.lower():
            related.add(edge["from"])
    return list(related)


def save_graph(graph, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(graph, indent=2))


def load_graph(path):
    return json.loads(Path(path).read_text())
