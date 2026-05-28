import ast

with open('my_custom_addons/dl_wood_traceability/models/dl_wood_peeling.py', 'r') as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'default_get':
        print(f"Found default_get at line {node.lineno}")

