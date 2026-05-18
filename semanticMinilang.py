# =========================================
# semanticMinilang.py
# MiniLang - Fase 3: Tabla de símbolos y comprobación de tipos
# =========================================

#Se agrego
from dataclasses import dataclass, field
import os
import sys


# =========================================
#Se agrego
# MODELOS DE TABLA DE SÍMBOLOS
# =========================================

#Se agrego
@dataclass
class Symbol:
    name: str
    category: str
    data_type: str
    scope: str
    line: int | str | None = None
    col: int | str | None = None
    value: object = None
    is_const: bool = False
    assigned: bool = False
    params: list = field(default_factory=list)
    return_type: str | None = None


#Se agrego
class SymbolTable:
    """
    Maneja símbolos por ámbitos.
    Permite insertar variables, constantes, funciones y parámetros.
    """

    def __init__(self):
        #Se agrego
        self.scope_stack = ["global"]
        self.symbols = []
        self.index = {}
        self.scope_counter = 0

    #Se agrego
    def current_scope(self):
        return self.scope_stack[-1]

    #Se agrego
    def enter_scope(self, scope_name):
        self.scope_stack.append(scope_name)

    #Se agrego
    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    #Se agrego
    def new_scope_name(self, prefix):
        self.scope_counter += 1
        return f"{prefix}:{self.scope_counter}"

    #Se agrego
    def insert(self, symbol):
        key = (symbol.scope, symbol.name)
        if key in self.index:
            return False

        self.index[key] = symbol
        self.symbols.append(symbol)
        return True

    #Se agrego
    def lookup_current(self, name):
        return self.index.get((self.current_scope(), name))

    #Se agrego
    def lookup(self, name):
        for scope in reversed(self.scope_stack):
            found = self.index.get((scope, name))
            if found is not None:
                return found

        return self.index.get(("global", name))

    #Se agrego
    def format_value(self, value):
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    #Se agrego
    def format_params(self, params):
        if not params:
            return "-"
        return ", ".join(f"{p.get('data_type', '?')} {p.get('name', '?')}" for p in params)

    #Se agrego
    def to_text(self):
        lines = []
        lines.append("TABLA DE SÍMBOLOS - MINILANG")
        lines.append("=" * 110)
        lines.append(
            f"{'Nombre':<20} {'Categoría':<12} {'Tipo':<10} {'Valor':<18} "
            f"{'Ámbito':<18} {'Línea':<8} {'Columna':<8} {'Parámetros'}"
        )
        lines.append("-" * 110)

        for sym in self.symbols:
            tipo = sym.return_type if sym.category == "funcion" else sym.data_type
            lines.append(
                f"{sym.name:<20} "
                f"{sym.category:<12} "
                f"{tipo:<10} "
                f"{self.format_value(sym.value):<18} "
                f"{sym.scope:<18} "
                f"{str(sym.line):<8} "
                f"{str(sym.col):<8} "
                f"{self.format_params(sym.params)}"
            )

        return "\n".join(lines) + "\n"


# =========================================
#Se agrego
# ANALIZADOR SEMÁNTICO
# =========================================

#Se agrego
class SemanticAnalyzer:
    """
    Recorre el AST generado por parserMinilang.py.
    Valida declaraciones, asignaciones, tipos, funciones, parámetros y retornos.
    """

    def __init__(self):
        #Se agrego
        self.table = SymbolTable()
        self.errors = []
        self.error_keys = set()
        self.current_function = None
        self.current_return_type = None
        self.current_function_has_return = False

    #Se agrego
    def add_error(self, node, message):
        line = node.get("line", "?") if isinstance(node, dict) else "?"
        col = node.get("col", "?") if isinstance(node, dict) else "?"
        key = (line, col, message)

        if key in self.error_keys:
            return

        self.error_keys.add(key)
        self.errors.append(f"Línea {line}, columna {col}: Error semántico: {message}")

    #Se agrego
    def analyze(self, ast):
        if ast is None:
            self.errors.append("Línea ?, columna ?: Error semántico: no se recibió AST para analizar")
            return self.errors, self.table

        if ast.get("node") != "Program":
            self.errors.append("Línea ?, columna ?: Error semántico: nodo raíz inválido")
            return self.errors, self.table

        statements = ast.get("statements", [])

        # Primero se registran funciones globales para permitir llamadas posteriores.
        self.register_global_functions(statements)

        # Luego se analizan las instrucciones en orden.
        for stmt in statements:
            self.analyze_statement(stmt)

        return self.errors, self.table

    #Se agrego
    def register_global_functions(self, statements):
        for stmt in statements:
            if not isinstance(stmt, dict):
                continue

            if stmt.get("node") != "FunctionDef":
                continue

            name = stmt.get("name")
            params = stmt.get("params", [])
            return_type = stmt.get("return_type")

            symbol = Symbol(
                name=name,
                category="funcion",
                data_type=return_type,
                return_type=return_type,
                scope="global",
                line=stmt.get("line"),
                col=stmt.get("col"),
                params=params,
                assigned=True,
            )

            if not self.table.insert(symbol):
                self.add_error(stmt, f"la función '{name}' ya fue declarada en este ámbito")

    #Se agrego
    def analyze_statement(self, stmt):
        if not isinstance(stmt, dict):
            return

        node = stmt.get("node")

        if node == "Declaration":
            self.analyze_declaration(stmt)
        elif node == "Assignment":
            self.analyze_assignment(stmt)
        elif node == "Write":
            self.analyze_write(stmt)
        elif node == "Read":
            self.analyze_read(stmt)
        elif node == "If":
            self.analyze_if(stmt)
        elif node == "While":
            self.analyze_while(stmt)
        elif node == "FunctionDef":
            self.analyze_function_def(stmt)
        elif node == "Return":
            self.analyze_return(stmt)
        elif node == "FunctionCall":
            self.evaluate_expression(stmt)

    #Se agrego
    def analyze_block(self, statements, scope_prefix=None):
        if scope_prefix is not None:
            scope_name = self.table.new_scope_name(scope_prefix)
            self.table.enter_scope(scope_name)

        for stmt in statements or []:
            self.analyze_statement(stmt)

        if scope_prefix is not None:
            self.table.exit_scope()

    #Se agrego
    def analyze_declaration(self, node):
        data_type = node.get("data_type")
        is_const = bool(node.get("is_const", False))
        category = "constante" if is_const else "variable"

        for item in node.get("items", []):
            name = item.get("name")
            value_node = item.get("value")

            symbol = Symbol(
                name=name,
                category=category,
                data_type=data_type,
                scope=self.table.current_scope(),
                line=item.get("line"),
                col=item.get("col"),
                value=None,
                is_const=is_const,
                assigned=False,
            )

            if not self.table.insert(symbol):
                self.add_error(item, f"el identificador '{name}' ya fue declarado en este ámbito")
                continue

            if value_node is not None:
                expr_type, expr_value = self.evaluate_expression(value_node)

                if not self.is_assignable(data_type, expr_type):
                    self.add_error(
                        item,
                        f"no se puede asignar {expr_type} a {data_type} en '{name}'"
                    )
                    continue

                symbol.value = self.coerce_value(data_type, expr_type, expr_value)
                symbol.assigned = True

    #Se agrego
    def analyze_assignment(self, node):
        name = node.get("name")
        symbol = self.table.lookup(name)

        if symbol is None or symbol.category == "funcion":
            self.add_error(node, f"variable '{name}' no declarada")
            self.evaluate_expression(node.get("value"))
            return

        if symbol.is_const and symbol.assigned:
            self.add_error(node, f"no se puede reasignar la constante '{name}'")
            self.evaluate_expression(node.get("value"))
            return

        expr_type, expr_value = self.evaluate_expression(node.get("value"))

        if not self.is_assignable(symbol.data_type, expr_type):
            self.add_error(
                node,
                f"no se puede asignar {expr_type} a {symbol.data_type} en '{name}'"
            )
            return

        symbol.value = self.coerce_value(symbol.data_type, expr_type, expr_value)
        symbol.assigned = True

    #Se agrego
    def analyze_write(self, node):
        for arg in node.get("args", []):
            self.evaluate_expression(arg)

    #Se agrego
    def analyze_read(self, node):
        for arg in node.get("args", []):
            if arg.get("node") == "Literal":
                continue

            if arg.get("node") == "Identifier":
                name = arg.get("name")
                symbol = self.table.lookup(name)

                if symbol is None or symbol.category == "funcion":
                    self.add_error(arg, f"variable '{name}' no declarada para lectura")
                    continue

                if symbol.is_const:
                    self.add_error(arg, f"no se puede leer un valor sobre la constante '{name}'")
                    continue

                symbol.assigned = True
                symbol.value = None
                continue

            self.add_error(arg, "argumento inválido en Read")

    #Se agrego
    def analyze_if(self, node):
        cond_type, _ = self.evaluate_expression(node.get("condition"))

        if cond_type != "bool" and cond_type != "unknown":
            self.add_error(node, "la condición del if debe ser bool")

        self.analyze_block(node.get("then_body", []), "if")

        for elif_node in node.get("elifs", []):
            elif_type, _ = self.evaluate_expression(elif_node.get("condition"))
            if elif_type != "bool" and elif_type != "unknown":
                self.add_error(elif_node, "la condición del elif debe ser bool")
            self.analyze_block(elif_node.get("body", []), "elif")

        if node.get("else_body"):
            self.analyze_block(node.get("else_body", []), "else")

    #Se agrego
    def analyze_while(self, node):
        cond_type, _ = self.evaluate_expression(node.get("condition"))

        if cond_type != "bool" and cond_type != "unknown":
            self.add_error(node, "la condición del while debe ser bool")

        self.analyze_block(node.get("body", []), "while")

    #Se agrego
    def analyze_function_def(self, node):
        previous_function = self.current_function
        previous_return_type = self.current_return_type
        previous_has_return = self.current_function_has_return

        self.current_function = node.get("name")
        self.current_return_type = node.get("return_type")
        self.current_function_has_return = False

        scope_name = f"func:{self.current_function}"
        self.table.enter_scope(scope_name)

        for param in node.get("params", []):
            param_symbol = Symbol(
                name=param.get("name"),
                category="parametro",
                data_type=param.get("data_type"),
                scope=scope_name,
                line=param.get("line"),
                col=param.get("col"),
                value=None,
                assigned=True,
            )

            if not self.table.insert(param_symbol):
                self.add_error(param, f"el parámetro '{param.get('name')}' ya fue declarado")

        for stmt in node.get("body", []):
            self.analyze_statement(stmt)

        if not self.current_function_has_return:
            self.add_error(node, f"la función '{self.current_function}' debe retornar {self.current_return_type}")

        self.table.exit_scope()

        self.current_function = previous_function
        self.current_return_type = previous_return_type
        self.current_function_has_return = previous_has_return

    #Se agrego
    def analyze_return(self, node):
        if self.current_function is None:
            self.add_error(node, "return fuera de una función")
            self.evaluate_expression(node.get("value"))
            return

        expr_type, _ = self.evaluate_expression(node.get("value"))
        self.current_function_has_return = True

        if not self.is_assignable(self.current_return_type, expr_type):
            self.add_error(
                node,
                f"la función '{self.current_function}' debe retornar {self.current_return_type}, pero retorna {expr_type}"
            )

    #Se agrego
    def evaluate_expression(self, node):
        if not isinstance(node, dict):
            return "unknown", None

        kind = node.get("node")

        if kind == "Literal":
            return node.get("data_type", "unknown"), node.get("value")

        if kind == "Identifier":
            return self.evaluate_identifier(node)

        if kind == "BinaryOp":
            return self.evaluate_binary_op(node)

        if kind == "UnaryOp":
            return self.evaluate_unary_op(node)

        if kind == "FunctionCall":
            return self.evaluate_function_call(node)

        return "unknown", None

    #Se agrego
    def evaluate_identifier(self, node):
        name = node.get("name")
        symbol = self.table.lookup(name)

        if symbol is None or symbol.category == "funcion":
            self.add_error(node, f"variable '{name}' no declarada")
            return "unknown", None

        return symbol.data_type, symbol.value

    #Se agrego
    def evaluate_binary_op(self, node):
        op = node.get("op")
        left_type, left_value = self.evaluate_expression(node.get("left"))
        right_type, right_value = self.evaluate_expression(node.get("right"))

        if "unknown" in (left_type, right_type):
            return "unknown", None

        if op in ("+", "-", "*", "/"):
            return self.evaluate_arithmetic(node, op, left_type, left_value, right_type, right_value)

        if op == "%":
            return self.evaluate_mod(node, left_type, left_value, right_type, right_value)

        if op in (">", "<", ">=", "<="):
            return self.evaluate_order_comparison(node, op, left_type, left_value, right_type, right_value)

        if op in ("==", "!="):
            return self.evaluate_equality(node, op, left_type, left_value, right_type, right_value)

        if op in ("and", "or"):
            return self.evaluate_logical(node, op, left_type, left_value, right_type, right_value)

        return "unknown", None

    #Se agrego
    def evaluate_arithmetic(self, node, op, left_type, left_value, right_type, right_value):
        if op == "+" and left_type == "string" and right_type == "string":
            value = None
            if left_value is not None and right_value is not None:
                value = str(left_value) + str(right_value)
            return "string", value

        if not self.is_numeric(left_type) or not self.is_numeric(right_type):
            self.add_error(node, f"no se puede operar {left_type} y {right_type} con '{op}'")
            return "unknown", None

        result_type = "float" if "float" in (left_type, right_type) or op == "/" else "int"
        value = self.compute_arithmetic(node, op, left_value, right_value)
        return result_type, value

    #Se agrego
    def evaluate_mod(self, node, left_type, left_value, right_type, right_value):
        if left_type != "int" or right_type != "int":
            self.add_error(node, "el operador '%' solo permite int con int")
            return "unknown", None

        if right_value == 0:
            self.add_error(node, "división entre cero en operación '%' ")
            return "int", None

        if left_value is not None and right_value is not None:
            return "int", left_value % right_value

        return "int", None

    #Se agrego
    def evaluate_order_comparison(self, node, op, left_type, left_value, right_type, right_value):
        if not self.is_numeric(left_type) or not self.is_numeric(right_type):
            self.add_error(node, f"no se puede comparar {left_type} y {right_type} con '{op}'")
            return "unknown", None

        value = None
        if left_value is not None and right_value is not None:
            if op == ">":
                value = left_value > right_value
            elif op == "<":
                value = left_value < right_value
            elif op == ">=":
                value = left_value >= right_value
            elif op == "<=":
                value = left_value <= right_value

        return "bool", value

    #Se agrego
    def evaluate_equality(self, node, op, left_type, left_value, right_type, right_value):
        compatible = left_type == right_type or (self.is_numeric(left_type) and self.is_numeric(right_type))

        if not compatible:
            self.add_error(node, f"no se puede comparar {left_type} y {right_type} con '{op}'")
            return "unknown", None

        value = None
        if left_value is not None and right_value is not None:
            value = left_value == right_value if op == "==" else left_value != right_value

        return "bool", value

    #Se agrego
    def evaluate_logical(self, node, op, left_type, left_value, right_type, right_value):
        if left_type != "bool" or right_type != "bool":
            self.add_error(node, f"el operador '{op}' solo permite bool con bool")
            return "unknown", None

        value = None
        if left_value is not None and right_value is not None:
            value = left_value and right_value if op == "and" else left_value or right_value

        return "bool", value

    #Se agrego
    def evaluate_unary_op(self, node):
        op = node.get("op")
        operand_type, operand_value = self.evaluate_expression(node.get("operand"))

        if operand_type == "unknown":
            return "unknown", None

        if op == "not":
            if operand_type != "bool":
                self.add_error(node, "el operador 'not' solo permite bool")
                return "unknown", None
            return "bool", None if operand_value is None else not operand_value

        if op == "-":
            if not self.is_numeric(operand_type):
                self.add_error(node, "el menos unario solo permite int o float")
                return "unknown", None
            return operand_type, None if operand_value is None else -operand_value

        return "unknown", None

    #Se agrego
    def evaluate_function_call(self, node):
        name = node.get("name")
        symbol = self.table.index.get(("global", name))

        if symbol is None or symbol.category != "funcion":
            self.add_error(node, f"función '{name}' no declarada")
            for arg in node.get("args", []):
                self.evaluate_expression(arg)
            return "unknown", None

        expected_params = symbol.params or []
        received_args = node.get("args", [])

        if len(expected_params) != len(received_args):
            self.add_error(
                node,
                f"la función '{name}' espera {len(expected_params)} argumentos, pero recibió {len(received_args)}"
            )

        for i, arg in enumerate(received_args):
            arg_type, _ = self.evaluate_expression(arg)

            if i >= len(expected_params):
                continue

            expected_type = expected_params[i].get("data_type")
            if not self.is_assignable(expected_type, arg_type):
                self.add_error(
                    arg,
                    f"el argumento {i + 1} de '{name}' debe ser {expected_type}, se recibió {arg_type}"
                )

        return symbol.return_type, None

    #Se agrego
    def compute_arithmetic(self, node, op, left_value, right_value):
        if left_value is None or right_value is None:
            return None

        try:
            if op == "+":
                return left_value + right_value
            if op == "-":
                return left_value - right_value
            if op == "*":
                return left_value * right_value
            if op == "/":
                if right_value == 0:
                    self.add_error(node, "división entre cero")
                    return None
                return left_value / right_value
        except Exception:
            return None

        return None

    #Se agrego
    def is_numeric(self, data_type):
        return data_type in ("int", "float")

    #Se agrego
    def is_assignable(self, target_type, source_type):
        if target_type == "unknown" or source_type == "unknown":
            return True

        if target_type == source_type:
            return True

        # Coerción permitida: int hacia float.
        if target_type == "float" and source_type == "int":
            return True

        return False

    #Se agrego
    def coerce_value(self, target_type, source_type, value):
        if value is None:
            return None

        if target_type == "float" and source_type == "int":
            return float(value)

        return value


# =========================================
#Se agrego
# FUNCIONES PÚBLICAS PARA INTEGRAR CON minilang.py
# =========================================

#Se agrego
def run_semantic_analysis(ast):
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(ast)


#Se agrego
def output_paths(filename):
    if filename.endswith(".mlng"):
        base = filename[:-5]
    else:
        base = filename

    return base + ".semantic.out", base + ".symbols.out"


#Se agrego
def write_semantic_output(filename, semantic_errors):
    semantic_file, _ = output_paths(filename)

    with open(semantic_file, "w", encoding="utf-8") as f:
        if semantic_errors:
            for err in semantic_errors:
                f.write(err + "\n")
        else:
            f.write("OK\n")

    return semantic_file


#Se agrego
def write_symbol_table_output(filename, symbol_table):
    _, symbols_file = output_paths(filename)

    with open(symbols_file, "w", encoding="utf-8") as f:
        f.write(symbol_table.to_text())

    return symbols_file


#Se agrego
def analyze_ast_and_write_outputs(ast, filename):
    semantic_errors, symbol_table = run_semantic_analysis(ast)
    semantic_file = write_semantic_output(filename, semantic_errors)
    symbols_file = write_symbol_table_output(filename, symbol_table)
    return semantic_errors, symbol_table, semantic_file, symbols_file


# =========================================
#Se agrego
# MODO DE PRUEBA INDEPENDIENTE
# Permite probar Fase 3 antes de modificar minilang.py.
# =========================================

#Se agrego
def analyze_file(filename):
    from parserMinilang import run_parser

    if not os.path.exists(filename):
        print(f"[ERROR] El archivo '{filename}' no existe.")
        return

    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    lex_errors, syn_errors, ast = run_parser(text, include_ast=True)
    previous_errors = lex_errors + syn_errors

    if previous_errors:
        print("No se ejecutó análisis semántico porque hay errores léxicos o sintácticos:")
        for err in previous_errors:
            print("  " + err)
        return

    semantic_errors, symbol_table, semantic_file, symbols_file = analyze_ast_and_write_outputs(ast, filename)

    if semantic_errors:
        print("Resultado: Se encontraron errores semánticos:")
        for err in semantic_errors:
            print("  " + err)
    else:
        print("Resultado semántico: OK")

    print(f"Archivo semántico generado: {semantic_file}")
    print(f"Tabla de símbolos generada: {symbols_file}")


#Se agrego
def main():
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
    else:
        filename = input("Ingrese el nombre del archivo .mlng: ").strip()
        analyze_file(filename)


#Se agrego
if __name__ == "__main__":
    main()
