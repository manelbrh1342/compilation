from lark import Lark, Transformer
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import shutil

# Charger la grammaire .lark depuis le fichier (chemin relatif au script)
from pathlib import Path
script_dir = Path(__file__).parent
grammar_path = script_dir / "minipython.lark"
with open(grammar_path, "r", encoding="utf-8") as f:
    grammar = f.read()

parser = Lark(grammar, start="start", parser="lalr", lexer="contextual")

code_source = """
int x, y;
x = 10;
y = x + 5;
print(y);
"""

# ------------------------------
# 2. Analyse lexicale
# ------------------------------
print("\n=== Phase lexicale (Lark) ===")
tokens = list(parser.lex(code_source))
for t in tokens:
    print(t)

# ------------------------------
# 3. AST syntaxique avec Lark Transformer
# ------------------------------
class SyntaxTransformer(Transformer):
    def decl(self, items):
        names = []
        for i in items:
            if isinstance(i, list):
                names.extend([str(x) for x in i])
            elif str(i) != ",":
                names.append(str(i))
        return ("decl(L)", names, 'int')
    def var_list(self, items):
        return [str(i) for i in items if str(i) != ","]
    def assign(self, items):
        return ("assign(S)", str(items[0]), items[1])
    def add(self, items):
        return ('+(S)', str(items[0]), int(items[1]))
    def print_stmt(self, items):
        return ("print(S)", str(items[0]))
    def NUMBER(self, n):
        return int(n)
    def CNAME(self, n):
        return str(n)
    def stmt(self, items):
        return items[0]
    def start(self, items):
        return list(items)
    def expr(self, items):
        return items[0]

tree = parser.parse(code_source)
ast_syntax = SyntaxTransformer().transform(tree)

# If transformer returned a Tree, extract its children to get a list of statements
if hasattr(ast_syntax, 'children'):
    ast_syntax = list(ast_syntax.children)

print("\n=== AST syntaxique (Lark) ===")
for node in ast_syntax:
    print(node)

# ------------------------------
# 4. Analyse sémantique
# ------------------------------
class SemanticTransformer:
    def __init__(self):
        self.symbol_table = {}

    def check(self, ast_list):
        new_ast = []
        for stmt in ast_list:
            if stmt[0] == "decl(L)":
                for var in stmt[1]:
                    if var in self.symbol_table:
                        raise Exception(f"Erreur : variable {var} déjà déclarée")
                    self.symbol_table[var] = 'int'
                new_ast.append(stmt)

            elif stmt[0] == "assign(S)":
                var, expr = stmt[1], stmt[2]
                if var not in self.symbol_table:
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

            elif stmt[0] == "print(S)":
                var = stmt[1]
                if var not in self.symbol_table:
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

            elif stmt[0] == "+(S)":
                left, right = stmt[1], stmt[2]
                if left not in self.symbol_table and not isinstance(left, int):
                    raise Exception(f"Erreur : variable {left} non déclarée")
                new_ast.append(stmt)

        return new_ast

semantic = SemanticTransformer()
ast_semantic = semantic.check(ast_syntax)

print("\n=== AST après analyse sémantique (Lark) ===")
for node in ast_semantic:
    print(node)

# ------------------------------
# 5. Visualisation AST
# ------------------------------
def build_anytree(node, parent=None):
    if isinstance(node, tuple):
        n = Node(node[0], parent=parent)
        for c in node[1:]:
            build_anytree(c, n)
        return n
    elif isinstance(node, list):
        n = Node("list", parent=parent)
        for item in node:
            build_anytree(item, n)
        return n
    else:
        Node(str(node), parent=parent)
        return parent

root = build_anytree(("root", *ast_semantic))

print("\n=== AST visuel console ===")
for pre, fill, node in RenderTree(root):
    print(f"{pre}{node.name}")

# Attempt to export AST image via Graphviz. To avoid Graphviz writing to a
# temp file in a directory it may not have permission for, first write the
# DOT file into the project directory and then call `dot` on that file.
try:
    DotExporter(root).to_dotfile("ast_lark.dot")
    print("Wrote DOT file to ast_lark.dot")

    if shutil.which("dot") is not None:
        import subprocess
        try:
            subprocess.check_call(["dot", "-Tpng", "ast_lark.dot", "-o", "ast_lark.png"])
            print("AST image saved to ast_lark.png")
        except Exception as e:
            print(f"dot failed to create PNG: {e}")
            print("You can create the PNG manually:")
            print("    dot -Tpng ast_lark.dot -o ast_lark.png")
    else:
        print("Graphviz 'dot' not found in PATH. To create PNG, install Graphviz and run:")
        print("    dot -Tpng ast_lark.dot -o ast_lark.png")
except Exception as e:
    print(f"Could not write DOT file: {e}")

# ------------------------------
# 6. Exécution MiniPython
# ------------------------------
def execute(ast, symbol_table):
    runtime = {var: 0 for var in symbol_table.keys()}

    for stmt in ast:
        if stmt[0] == 'assign(S)':
            var = stmt[1]
            val = stmt[2]

            if isinstance(val, tuple) and val[0] == '+(S)':
                left_val = runtime[val[1]] if val[1] in runtime else int(val[1])
                right_val = val[2]
                runtime[var] = left_val + right_val
            else:
                runtime[var] = val if isinstance(val, int) else runtime[val]

        elif stmt[0] == 'print(S)':
            print(runtime[stmt[1]])

print("\n=== Exécution MiniPython ===")
execute(ast_semantic, semantic.symbol_table)