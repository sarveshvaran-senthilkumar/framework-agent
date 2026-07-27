import sys

import config
import database
from rule_generator import process_all_documents
from knowledge_graph import build_graph, save_graph, load_graph
from compare_agent import run_comparison

GRAPH_FILE = config.BASE / "knowledge_graph.json"


# --- CLI ---

def cmd_ingest():
    print("Processing all documents...")
    rules = process_all_documents()
    database.clear_rules()
    database.insert_rules(rules)
    print(f"Stored {len(rules)} rules in MongoDB ({config.MONGO_DB})")


def cmd_graph():
    rules = database.get_all_rules()
    if not rules:
        print("No rules found. Run 'ingest' first.")
        return
    graph = build_graph(rules)
    save_graph(graph, GRAPH_FILE)
    print(f"Built: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")


def cmd_compare(query):
    rules = database.get_all_rules()
    if not rules:
        print("No rules found. Run 'ingest' first.")
        return
    graph = load_graph(GRAPH_FILE)
    result = run_comparison(query, graph)
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    print(result["report"])


def cmd_categories():
    cats = database.get_categories()
    if not cats:
        print("No categories. Run 'ingest' first.")
        return
    for cat in cats:
        count = len(database.find_by_category(cat))
        print(f"  {cat}: {count} rules")


def cmd_stats():
    rules = database.get_all_rules()
    logs = database.get_logs()
    docs = list(config.DOCUMENTS.glob("*.txt"))
    print(f"Documents:   {len(docs)}")
    print(f"Rules:       {len(rules)}")
    print(f"Categories:  {len(database.get_categories())}")
    print(f"Comparisons: {len(logs)}")


def cmd_serve():
    import uvicorn
    from fastapi import FastAPI, Query

    app = FastAPI(
        title="Construction Knowledge Validation Platform",
        description="RAV system: extract rules from construction docs, compare with LLM, report violations.",
        version="1.0.0"
    )

    @app.get("/rules", summary="List rules", tags=["Knowledge"])
    def api_rules(category: str = Query(None)):
        if category:
            return database.find_by_category(category)
        return database.get_all_rules()

    @app.get("/categories", summary="List categories", tags=["Knowledge"])
    def api_categories():
        return database.get_categories()

    @app.get("/graph", summary="Knowledge graph", tags=["Knowledge"])
    def api_graph():
        return load_graph(GRAPH_FILE)

    @app.post("/ingest", summary="Process docs and extract rules", tags=["Pipeline"])
    def api_ingest():
        rules = process_all_documents()
        database.clear_rules()
        database.insert_rules(rules)
        graph = build_graph(rules)
        save_graph(graph, GRAPH_FILE)
        return {"rules": len(rules), "nodes": len(graph["nodes"])}

    @app.post("/compare", summary="Compare documents", tags=["Comparison"])
    def api_compare(query: str = Query(..., description="e.g. Compare beam and column specs")):
        graph = load_graph(GRAPH_FILE)
        return run_comparison(query, graph)

    @app.get("/logs", summary="Comparison logs", tags=["Comparison"])
    def api_logs():
        return database.get_logs()

    @app.get("/stats", summary="Statistics", tags=["Info"])
    def api_stats():
        return {
            "documents": len(list(config.DOCUMENTS.glob("*.txt"))),
            "rules": len(database.get_all_rules()),
            "categories": len(database.get_categories()),
            "comparisons": len(database.get_logs())
        }

    print("Swagger UI -> http://localhost:8002/docs")
    uvicorn.run(app, host="0.0.0.0", port=8002)


# --- Entry ---

COMMANDS = {
    "ingest":     "Process documents, extract rules, store in MongoDB",
    "graph":      "Build knowledge graph from rules",
    "compare":    "Compare documents (usage: compare \"query\")",
    "categories": "List rule categories",
    "stats":      "Show counts",
    "serve":      "Start API with Swagger UI (port 8002)",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python main.py <command>\n")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd:12} {desc}")
        return

    cmd = sys.argv[1]
    if cmd == "ingest":     cmd_ingest()
    elif cmd == "graph":    cmd_graph()
    elif cmd == "compare":  cmd_compare(sys.argv[2] if len(sys.argv) > 2 else input("Query: "))
    elif cmd == "categories": cmd_categories()
    elif cmd == "stats":    cmd_stats()
    elif cmd == "serve":    cmd_serve()

if __name__ == "__main__":
    main()
