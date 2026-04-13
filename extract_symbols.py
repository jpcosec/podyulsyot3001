import ast
import os
import json

def get_symbols(file_path):
    with open(file_path, "r") as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return []
    
    symbols = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append({"type": "Class", "name": node.name})
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            symbols.append({"type": "Function", "name": node.name})
    return symbols

project_tree = {}
for root, dirs, files in os.walk("src/automation"):
    if "__pycache__" in root: continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            project_tree[path] = get_symbols(path)

print(json.dumps(project_tree, indent=2))
