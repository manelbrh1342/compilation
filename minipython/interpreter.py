import sys
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import re

def run_minipython_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code_source = f.read()
    except FileNotFoundError:
        print(f"Erreur: Le fichier n'existe pas.")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {e}")
        sys.exit(1)

    if not code_source.strip():
        print("Aucun code dans le fichier. Programme terminé.")
        sys.exit(0)
    
    print("=== Code source ===")
    print(code_source)

    token_specification = [
        ('NUMBER', r'\d+'),
        ('INT', r'int'),
        ('FLOAT', r'float'),
        ('BOOL', r'bool'),
        ('STRING', r'string'),
        ('WHILE', r'while'),
        ('IF', r'if'),
        ('ELSE', r'else'),
        ('PRINT', r'print'),
        ('DEF', r'def'),
        ('RETURN', r'return'),
        ('ID', r'[A-Za-z_]\w*'),
        ('LTE', r'<='),
        ('GTE', r'>='),
        ('EQ', r'=='),
        ('NEQ', r'!='),
        ('LT', r'<'),
        ('GT', r'>'),
        ('AND', r'&&'),
        ('OR', r'\|\|'),
        ('NOT', r'!'),
        ('COMMA', r','),
        ('SEMICOLON', r';'),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('MULT', r'\*'),
        ('DIV', r'/'),
        ('EQUAL', r'='),
        ('LPAR', r'\('),
        ('RPAR', r'\)'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('SKIP', r'[ \t\n]+'),
        ('COMMENT', r'/\*.*?\*/')
    ]

    regex = '|'.join(f'(?P<{n}>{p})' for n, p in token_specification)
    tokens = [(m.lastgroup, m.group()) for m in re.finditer(regex, code_source, re.DOTALL) 
              if m.lastgroup not in ['SKIP', 'COMMENT']]

    print("\n=== Phase lexicale ===")
    for t in tokens:
        print(t)

    symbol_table = {}

    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0
            
        def current_token(self):
            if self.pos < len(self.tokens):
                return self.tokens[self.pos]
            return None
        
        def advance(self):
            self.pos += 1
        
        def parse_program(self):
            statements = []
            while self.pos < len(self.tokens):
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            return ('Program', statements)
        
        def parse_statement(self):
            tok = self.current_token()
            if not tok:
                return None
                
            if tok[0] in ['INT', 'FLOAT', 'BOOL', 'STRING']:
                return self.parse_declaration()
            elif tok[0] == 'WHILE':
                return self.parse_while()
            elif tok[0] == 'IF':
                return self.parse_if()
            elif tok[0] == 'PRINT':
                return self.parse_print()
            elif tok[0] == 'ID':
                return self.parse_assignment()
            else:
                self.advance()
                return None
        
        def parse_declaration(self):
            type_tok = self.current_token()
            var_type = type_tok[1]
            self.advance()
            
            vars_list = []
            while self.current_token() and self.current_token()[0] != 'SEMICOLON':
                if self.current_token()[0] == 'ID':
                    var_name = self.current_token()[1]
                    vars_list.append(var_name)
                    symbol_table[var_name] = var_type
                self.advance()
            
            if self.current_token() and self.current_token()[0] == 'SEMICOLON':
                self.advance()
            
            return ('Decl (L-attribué)', [('Var: ' + v + f' (type={var_type})') for v in vars_list])
        
        def parse_assignment(self):
            var_name = self.current_token()[1]
            self.advance()
            
            if self.current_token() and self.current_token()[0] == 'EQUAL':
                self.advance()
                expr = self.parse_expression()
                
                if self.current_token() and self.current_token()[0] == 'SEMICOLON':
                    self.advance()
                
                return ('Assign (S-attribué)', [('Var: ' + var_name), expr])
            return None
        
        def parse_expression(self):
            left = self.parse_term()
            
            while self.current_token() and self.current_token()[0] in ['PLUS', 'MINUS', 'LT', 'GT', 'LTE', 'GTE', 'EQ', 'NEQ', 'AND', 'OR']:
                op = self.current_token()[1]
                self.advance()
                right = self.parse_term()
                left = ('Expr: ' + op, [left, right])
            
            return left
        
        def parse_term(self):
            tok = self.current_token()
            if not tok:
                return None
            
            if tok[0] == 'NUMBER':
                self.advance()
                return ('Const: ' + tok[1])
            elif tok[0] == 'ID':
                self.advance()
                return ('Var: ' + tok[1])
            elif tok[0] == 'LPAR':
                self.advance()
                expr = self.parse_expression()
                if self.current_token() and self.current_token()[0] == 'RPAR':
                    self.advance()
                return expr
            elif tok[0] == 'NOT':
                self.advance()
                expr = self.parse_term()
                return ('Expr: !', [expr])
            return None
        
        def parse_while(self):
            self.advance()
            
            if self.current_token() and self.current_token()[0] == 'LPAR':
                self.advance()
            
            condition = self.parse_expression()
            
            if self.current_token() and self.current_token()[0] == 'RPAR':
                self.advance()
            
            if self.current_token() and self.current_token()[0] == 'LBRACE':
                self.advance()
            
            body = []
            while self.current_token() and self.current_token()[0] != 'RBRACE':
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            
            if self.current_token() and self.current_token()[0] == 'RBRACE':
                self.advance()
            
            return ('While (S-attribué)', [condition, ('Body', body)])
        
        def parse_if(self):
            self.advance()
            
            if self.current_token() and self.current_token()[0] == 'LPAR':
                self.advance()
            
            condition = self.parse_expression()
            
            if self.current_token() and self.current_token()[0] == 'RPAR':
                self.advance()
            
            if self.current_token() and self.current_token()[0] == 'LBRACE':
                self.advance()
            
            then_body = []
            while self.current_token() and self.current_token()[0] != 'RBRACE':
                stmt = self.parse_statement()
                if stmt:
                    then_body.append(stmt)
            
            if self.current_token() and self.current_token()[0] == 'RBRACE':
                self.advance()
            
            else_body = []
            if self.current_token() and self.current_token()[0] == 'ELSE':
                self.advance()
                if self.current_token() and self.current_token()[0] == 'LBRACE':
                    self.advance()
                
                while self.current_token() and self.current_token()[0] != 'RBRACE':
                    stmt = self.parse_statement()
                    if stmt:
                        else_body.append(stmt)
                
                if self.current_token() and self.current_token()[0] == 'RBRACE':
                    self.advance()
            
            if else_body:
                return ('If (S-attribué)', [condition, ('Then', then_body), ('Else', else_body)])
            else:
                return ('If (S-attribué)', [condition, ('Then', then_body)])
        
        def parse_print(self):
            self.advance()
            
            if self.current_token() and self.current_token()[0] == 'LPAR':
                self.advance()
            
            expr = self.parse_expression()
            
            if self.current_token() and self.current_token()[0] == 'RPAR':
                self.advance()
            
            if self.current_token() and self.current_token()[0] == 'SEMICOLON':
                self.advance()
            
            return ('Print (S-attribué)', [expr])

    try:
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        print("\n=== AST syntaxique brut ===")
        print(ast)
    except Exception as e:
        print(f"\n Erreur d'analyse syntaxique: {e}")
        sys.exit(1)

    # Analyse sémantique
    def semantic_check(node, symbol_table):
        if isinstance(node, tuple):
            node_type = node[0]
            
            if node_type.startswith('Var:'):
                var_name = node_type.split(': ')[1]
                if var_name not in symbol_table:
                    raise Exception(f"Erreur sémantique : variable {var_name} non déclarée")
            
            if len(node) > 1:
                for child in node[1:]:
                    if isinstance(child, (tuple, list)):
                        semantic_check(child, symbol_table)
        
        elif isinstance(node, list):
            for item in node:
                semantic_check(item, symbol_table)
        
        return node

    try:
        ast_semantic = semantic_check(ast, symbol_table)
        print("\n=== AST après analyse sémantique ===")
        print(ast_semantic)
        print("\nAnalyse sémantique réussie!")
        
        print("\n=== Table des symboles ===")
        for var, var_type in symbol_table.items():
            print(f"{var}: {var_type}")
    except Exception as e:
        print(f"\n {e}")
        sys.exit(1)

    def build_anytree(node, parent=None):
        if isinstance(node, tuple):
            n = Node(node[0], parent=parent)
            if len(node) > 1:
                for c in node[1:]:
                    if isinstance(c, (tuple, list)):
                        build_anytree(c, n)
                    else:
                        Node(str(c), parent=n)
            return n
        elif isinstance(node, list):
            for item in node:
                build_anytree(item, parent)
            return parent
        else:
            Node(str(node), parent=parent)
            return parent

    root_node = build_anytree(ast_semantic)
    print("\n=== AST visuel console ===")
    for pre, fill, node in RenderTree(root_node):
        print(f"{pre}{node.name}")

    from pathlib import Path
    import subprocess

    script_dir = Path(filepath).parent
    dot_path = script_dir / "ast_file.dot"
    png_path = script_dir / "ast_file.png"

    DotExporter(root_node).to_dotfile(str(dot_path))
    try:
        subprocess.check_call(["dot", str(dot_path), "-Tpng", "-o", str(png_path)])
        print(f"\nAST exporté en image : {png_path}")
    except FileNotFoundError:
        print("\n⚠️ Graphviz 'dot' not found. Install Graphviz and ensure 'dot' is in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️ Impossible d'exporter l'image: {e}")

    class TACGenerator:
        def __init__(self):
            self.code = []
            self.temp_count = 0
            self.label_count = 0
        
        def new_temp(self):
            self.temp_count += 1
            return f"t{self.temp_count}"
        
        def new_label(self):
            self.label_count += 1
            return f"L{self.label_count}"
        
        def generate(self, node):
            if isinstance(node, tuple):
                node_type = node[0]
                
                if node_type.startswith('Decl'):
                    for var in node[1]:
                        var_name = var.split(': ')[1].split(' ')[0]
                        self.code.append(f"DECLARE {var_name}")
                
                elif node_type.startswith('Assign'):
                    if len(node) > 2:
                        var = node[1][0].split(': ')[1]
                        expr_node = node[2]
                    else:
                        var = node[1][0].split(': ')[1]
                        expr_node = node[1][1] if len(node[1]) > 1 else None

                    if expr_node is not None:
                        result = self.generate_expr(expr_node)
                        self.code.append(f"STORE {result}, {var}")
                    else:
                        self.code.append(f"STORE None, {var}")
                
                elif node_type.startswith('While'):
                    start_label = self.new_label()
                    end_label = self.new_label()
                    
                    self.code.append(f"{start_label}:")
                    if isinstance(node[1], (list, tuple)) and len(node[1]) > 0:
                        cond = node[1][0]
                        body = node[1][1] if len(node[1]) > 1 else None
                    else:
                        cond = node[1]
                        body = node[2] if len(node) > 2 else None

                    cond_result = self.generate_expr(cond)
                    self.code.append(f"IFFALSE {cond_result} GOTO {end_label}")

                    if body is not None:
                        self.generate(body)
                    
                    self.code.append(f"GOTO {start_label}")
                    self.code.append(f"{end_label}:")
                
                elif node_type.startswith('If'):
                    else_label = self.new_label()
                    end_label = self.new_label()
                    if isinstance(node[1], (list, tuple)) and len(node[1]) > 0:
                        cond = node[1][0]
                        then_block = node[1][1] if len(node[1]) > 1 else None
                        else_block = node[1][2] if len(node[1]) > 2 else None
                    else:
                        cond = node[1]
                        then_block = node[2] if len(node) > 2 else None
                        else_block = node[3] if len(node) > 3 else None

                    cond_result = self.generate_expr(cond)
                    self.code.append(f"IFFALSE {cond_result} GOTO {else_label}")

                    if then_block is not None:
                        self.generate(then_block)
                    self.code.append(f"GOTO {end_label}")

                    self.code.append(f"{else_label}:")
                    if else_block is not None:
                        self.generate(else_block)

                    self.code.append(f"{end_label}:")
                
                elif node_type.startswith('Print'):
                    expr_node = node[1][0] if isinstance(node[1], (list, tuple)) and len(node[1])>0 else (node[1] if len(node)>1 else None)
                    result = self.generate_expr(expr_node)
                    self.code.append(f"PRINT {result}")
                
                elif node_type == 'Program':
                    for stmt in node[1]:
                        self.generate(stmt)
                
                elif node_type in ['Body', 'Then', 'Else']:
                    for stmt in node[1]:
                        self.generate(stmt)
            
            elif isinstance(node, list):
                for item in node:
                    self.generate(item)
        
        def generate_expr(self, expr):
            if isinstance(expr, tuple):
                expr_type = expr[0]
                
                if expr_type.startswith('Const:'):
                    return expr_type.split(': ')[1]
                
                elif expr_type.startswith('Var:'):
                    var_name = expr_type.split(': ')[1]
                    temp = self.new_temp()
                    self.code.append(f"LOAD {var_name}, {temp}")
                    return temp
                
                elif expr_type.startswith('Expr:'):
                    op = expr_type.split(': ')[1]
                    
                    if op == '!':
                        operand = self.generate_expr(expr[1][0])
                        temp = self.new_temp()
                        self.code.append(f"NOT {operand}, {temp}")
                        return temp
                    else:
                        left = self.generate_expr(expr[1][0])
                        right = self.generate_expr(expr[1][1])
                        temp = self.new_temp()
                        
                        op_map = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV',
                                  '<': 'LT', '>': 'GT', '<=': 'LTE', '>=': 'GTE',
                                  '==': 'EQ', '!=': 'NEQ', '&&': 'AND', '||': 'OR'}
                        
                        tac_op = op_map.get(op, op)
                        self.code.append(f"{tac_op} {left}, {right}, {temp}")
                        return temp
            
            return str(expr)

    tac_gen = TACGenerator()
    tac_gen.generate(ast_semantic)

    print("\n=== Code Intermédiaire (TAC) ===")
    for line in tac_gen.code:
        print(line)

    def execute(ast, symbol_table):
        runtime = {var: 0 for var in symbol_table.keys()}
        
        def eval_expr(expr):
            if isinstance(expr, tuple):
                expr_type = expr[0]
                data = expr[1] if len(expr) > 1 else None
            elif isinstance(expr, str):
                expr_type = expr
                data = None
            elif isinstance(expr, (list,)) and len(expr) > 0:
                return eval_expr(expr[0])
            else:
                return 0

            if expr_type.startswith('Const:'):
                return int(expr_type.split(': ')[1])
            elif expr_type.startswith('Var:'):
                var_name = expr_type.split(': ')[1]
                return runtime.get(var_name, 0)
            elif expr_type.startswith('Expr:'):
                op = expr_type.split(': ')[1]
                if op == '!':
                    operand = eval_expr(data[0])
                    return not operand
                left = eval_expr(data[0])
                right = eval_expr(data[1])

                if op == '+':
                    return left + right
                elif op == '-':
                    return left - right
                elif op == '*':
                    return left * right
                elif op == '/':
                    return left // right if right != 0 else 0
                elif op == '<':
                    return left < right
                elif op == '>':
                    return left > right
                elif op == '<=':
                    return left <= right
                elif op == '>=':
                    return left >= right
                elif op == '==':
                    return left == right
                elif op == '!=':
                    return left != right
                elif op == '&&':
                    return left and right
                elif op == '||':
                    return left or right

            return 0
        
        def exec_stmt(stmt):
            if isinstance(stmt, tuple):
                stmt_type = stmt[0]
                
                if stmt_type.startswith('Assign'):
                    if len(stmt) > 2:
                        var = stmt[1][0].split(': ')[1]
                        expr_node = stmt[2]
                    else:
                        var = stmt[1][0].split(': ')[1]
                        expr_node = stmt[1][1] if len(stmt[1]) > 1 else None

                    value = eval_expr(expr_node) if expr_node is not None else 0
                    runtime[var] = value
                
                elif stmt_type.startswith('While'):
                    if isinstance(stmt[1], (list, tuple)) and len(stmt[1])>0:
                        cond = stmt[1][0]
                        body = stmt[1][1] if len(stmt[1])>1 else None
                    else:
                        cond = stmt[1]
                        body = stmt[2] if len(stmt)>2 else None

                    while eval_expr(cond):
                        if body is not None:
                            exec_stmt(body)
                
                elif stmt_type.startswith('If'):
                    if isinstance(stmt[1], (list, tuple)) and len(stmt[1])>0:
                        cond = stmt[1][0]
                        then_b = stmt[1][1] if len(stmt[1])>1 else None
                        else_b = stmt[1][2] if len(stmt[1])>2 else None
                    else:
                        cond = stmt[1]
                        then_b = stmt[2] if len(stmt)>2 else None
                        else_b = stmt[3] if len(stmt)>3 else None

                    if eval_expr(cond):
                        if then_b is not None:
                            exec_stmt(then_b)
                    elif else_b is not None:
                        exec_stmt(else_b)
                
                elif stmt_type.startswith('Print'):
                    expr_node = stmt[1][0] if isinstance(stmt[1], (list, tuple)) and len(stmt[1])>0 else (stmt[1] if len(stmt)>1 else None)
                    value = eval_expr(expr_node)
                    print(value)
                
                elif stmt_type in ['Body', 'Then', 'Else']:
                    for s in stmt[1]:
                        exec_stmt(s)
                
                elif stmt_type == 'Program':
                    for s in stmt[1]:
                        exec_stmt(s)
        
        exec_stmt(ast)

    print("\n=== Exécution MiniPython ===")
    try:
        execute(ast_semantic, symbol_table)
        print("\nExécution terminée avec succès!")
    except Exception as e:
        print(f"\n Erreur d'exécution: {e}")



def main():
    filename = sys.argv[1]
    
    try:
        run_minipython_file(filename)
    except Exception as e:
        print(f"\n Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()