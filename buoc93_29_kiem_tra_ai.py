from pathlib import Path
import ast

path = Path("backend/routers/ai_live.py")
source = path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)

print("=== BUOC 93.29: KIEM TRA NOI SU DUNG DU LIEU AI ===")

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "read_rooms":
            print(f"read_rooms() tai dong {node.lineno}")

print("\n=== CAC API AI ===")

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and func.attr in ("get", "post"):
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        print(
                            f"Dong {node.lineno}: "
                            f"{func.attr.upper()} {decorator.args[0].value} "
                            f"-> {node.name}"
                        )

print("\n=== HOAN THANH ===")
