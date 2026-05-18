# =========================================
# parserMinilang.py
# MiniLang - Analizador Sintáctico Ascendente con PLY
# =========================================

import os
import sys
import ply.yacc as yacc
from Proyecto import Lexer

# =========================================
# TOKENS: deben coincidir con Proyecto.py
# =========================================

tokens = (
    'IF', 'ELIF', 'ELSE', 'WHILE',
    'INT_TYPE', 'FLOAT_TYPE', 'BOOL_TYPE', 'STRING_TYPE',
    'READ', 'WRITE', 'RETURN', 'FUNC',
    'BOOL', 'ID', 'INT', 'FLOAT', 'STRING',
    'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD',
    'GT', 'LT', 'ASSIGN', 'EQ', 'NEQ', 'GTE', 'LTE',
    'LPAREN', 'RPAREN', 'COLON', 'COMMA', 'SEMICOLON',
    'AND', 'OR', 'NOT',
    'INDENT', 'DEDENT', 'NEWLINE'
)

# =========================================
# PRECEDENCIA Y ASOCIATIVIDAD
# De menor a mayor:
# or, and, not, comparaciones, +/-, */%/, menos unario
# =========================================

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('nonassoc', 'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV', 'MOD'),
    ('right', 'UMINUS'),
)

# =========================================
# ADAPTADOR DE TOKENS DEL LEXER ORIGINAL A PLY
# =========================================

class PlyTokenAdapter:
    """
    Convierte los Token de Proyecto.py al formato que espera PLY.
    EOF se ignora porque PLY usa None para fin de entrada.

    PLY, cuando se usa tracking=True, consulta atributos como
    lexer.lineno y lexer.lexpos. Por eso este adaptador también
    guarda esos valores en el objeto, no solo en cada token.
    """
    def __init__(self, tokens_list):
        self.tokens = [t for t in tokens_list if t.type != 'EOF']
        self.index = 0

        # Atributos que PLY necesita cuando se usa tracking=True
        self.lineno = 1
        self.lexpos = 0

    def token(self):
        if self.index >= len(self.tokens):
            return None

        src = self.tokens[self.index]
        self.index += 1

        tok = yacc.YaccSymbol()
        tok.type = src.type
        tok.value = src.value if src.value is not None else src.type
        tok.lineno = src.line
        tok.lexpos = src.col_start
        tok.col_start = src.col_start
        tok.col_end = src.col_end

        # Actualizar posición actual del lexer adaptado
        self.lineno = tok.lineno
        self.lexpos = tok.lexpos

        return tok


# =========================================
# REGISTRO DE ERRORES SINTÁCTICOS
# =========================================

syntax_errors = []
syntax_error_keys = set()
syntax_error_lines = set()
lex_error_lines = set()


def token_value(tok):
    if tok is None:
        return "EOF"
    return tok.value if getattr(tok, "value", None) is not None else tok.type


def token_col(tok):
    if tok is None:
        return "?"
    return getattr(tok, "col_start", getattr(tok, "lexpos", "?"))


def format_syntax_error(line, col, symbol, message):
    return f"Línea {line}, columna {col}, símbolo '{symbol}': Error sintáctico: {message}"


def add_syntax_error(message, tok=None, line=None, col=None, symbol=None):
    """
    Agrega errores sin duplicarlos. Se usa tanto para validaciones de recuperación
    como para errores reportados por PLY.
    """
    if tok is not None:
        line = getattr(tok, "line", getattr(tok, "lineno", line))
        col = token_col(tok)
        symbol = token_value(tok)

    if line is None:
        line = "?"
    if col is None:
        col = "?"
    if symbol is None:
        symbol = "EOF"

    key = (line, col, symbol, message)
    if key in syntax_error_keys:
        return

    syntax_error_keys.add(key)
    if isinstance(line, int):
        syntax_error_lines.add(line)
    syntax_errors.append(format_syntax_error(line, col, symbol, message))


# =========================================
# VALIDACIONES SINTÁCTICAS DE RECUPERACIÓN
# Estas validaciones ayudan a reportar varios errores claros en una sola corrida,
# evitando que PLY genere demasiados errores en cascada.
# =========================================

SIMPLE_STARTERS = {
    'INT_TYPE', 'FLOAT_TYPE', 'BOOL_TYPE', 'STRING_TYPE',
    'ID', 'WRITE', 'READ', 'RETURN'
}

COMPOUND_STARTERS = {'IF', 'ELIF', 'ELSE', 'WHILE', 'FUNC'}
BINARY_OPERATORS = {
    'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD',
    'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ',
    'AND', 'OR', 'ASSIGN', 'COMMA'
}


def get_lex_error_lines(errors):
    lines = set()
    for err in errors:
        # Formato esperado: Línea X, columna Y, ...
        try:
            prefix = err.split(",", 1)[0]
            line = int(prefix.replace("Línea", "").strip())
            lines.add(line)
        except Exception:
            pass
    return lines


def group_tokens_by_line(tokens_list):
    groups = []
    current = []

    for tok in tokens_list:
        if tok.type == 'EOF':
            break

        current.append(tok)

        if tok.type == 'NEWLINE':
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    return groups


def real_tokens(line_tokens):
    return [t for t in line_tokens if t.type not in ('INDENT', 'DEDENT', 'NEWLINE')]


def first_real_token(line_tokens):
    rt = real_tokens(line_tokens)
    return rt[0] if rt else None


def last_real_token(line_tokens):
    rt = real_tokens(line_tokens)
    return rt[-1] if rt else None


def line_has_type(line_tokens, token_type):
    return any(t.type == token_type for t in line_tokens)


def find_newline(line_tokens):
    for tok in line_tokens:
        if tok.type == 'NEWLINE':
            return tok
    return last_real_token(line_tokens)


def has_unbalanced_parentheses(line_tokens):
    rt = real_tokens(line_tokens)
    opens = sum(1 for t in rt if t.type == 'LPAREN')
    closes = sum(1 for t in rt if t.type == 'RPAREN')
    return opens != closes


def get_token_before_semicolon_or_newline(line_tokens):
    rt = real_tokens(line_tokens)
    for i, tok in enumerate(rt):
        if tok.type == 'SEMICOLON':
            return rt[i - 1] if i > 0 else tok, tok
    nl = find_newline(line_tokens)
    return (rt[-1] if rt else nl), nl


def next_significant_token_after_line(tokens_list, newline_token):
    try:
        index = tokens_list.index(newline_token) + 1
    except ValueError:
        return None

    while index < len(tokens_list):
        tok = tokens_list[index]
        if tok.type == 'EOF':
            return None
        if tok.type == 'NEWLINE':
            index += 1
            continue
        # Si aparece DEDENT antes de un token real, se busca el token real de esa línea
        # para reportar un mensaje más claro.
        if tok.type == 'DEDENT':
            j = index + 1
            while j < len(tokens_list) and tokens_list[j].type in ('DEDENT', 'NEWLINE'):
                j += 1
            return tokens_list[j] if j < len(tokens_list) and tokens_list[j].type != 'EOF' else tok
        return tok
    return None


def precheck_syntax(tokens_list, lexer_errors):
    """
    Detecta casos de error que normalmente causan cascada en un parser LR:
    - falta de punto y coma
    - paréntesis no cerrado en llamadas
    - expresión incompleta
    - falta de ':' en encabezados
    - falta de indentación de bloque
    """
    global lex_error_lines
    lex_error_lines = get_lex_error_lines(lexer_errors)

    groups = group_tokens_by_line(tokens_list)

    for line_tokens in groups:
        first = first_real_token(line_tokens)
        last = last_real_token(line_tokens)
        newline = find_newline(line_tokens)

        if first is None:
            continue

        # 1. Falta de ':' en encabezados de bloque.
        if first.type in ('IF', 'ELIF', 'WHILE', 'FUNC') and not line_has_type(line_tokens, 'COLON'):
            add_syntax_error("falta ':' al final del encabezado del bloque", newline)
            continue

        if first.type == 'ELSE' and not line_has_type(line_tokens, 'COLON'):
            add_syntax_error("falta ':' después de else", newline)
            continue

        # 2. Paréntesis no cerrado.
        if has_unbalanced_parentheses(line_tokens):
            add_syntax_error("paréntesis no cerrado", newline)
            continue

        # 3. Return sin valor.
        if first.type == 'RETURN':
            before_end, end_tok = get_token_before_semicolon_or_newline(line_tokens)
            if before_end.type == 'RETURN':
                add_syntax_error("return requiere una expresión de retorno", end_tok)
                continue

        # 4. Expresión incompleta antes de ; o NEWLINE.
        before_end, end_tok = get_token_before_semicolon_or_newline(line_tokens)
        if before_end and before_end.type in BINARY_OPERATORS:
            # En declaraciones/asignaciones esto detecta casos como: z = x + ;
            add_syntax_error("expresión incompleta", end_tok)
            continue

        # 5. Falta de punto y coma en instrucciones simples.
        # Si la línea ya tiene error léxico, se evita agregar un segundo error en cascada.
        if first.type in SIMPLE_STARTERS and first.line not in lex_error_lines:
            if last is not None and last.type != 'SEMICOLON':
                add_syntax_error("falta ';' al final de la instrucción", newline)
                continue

    # 6. Falta de INDENT después de encabezado con ':'
    for line_tokens in groups:
        first = first_real_token(line_tokens)
        newline = find_newline(line_tokens)

        if first is None:
            continue

        if first.type in COMPOUND_STARTERS and line_has_type(line_tokens, 'COLON'):
            # No se valida indentación si esa misma línea ya tenía error.
            if first.line in syntax_error_lines:
                continue

            nxt = next_significant_token_after_line(tokens_list, newline)
            if nxt is not None and nxt.type != 'INDENT':
                add_syntax_error("se esperaba indentación del bloque", nxt)


# =========================================
# GRAMÁTICA
# =========================================

def p_program(p):
    'program : opt_newlines stmt_list opt_newlines'
    pass


def p_opt_newlines(p):
    '''opt_newlines : opt_newlines NEWLINE
                    | empty'''
    pass


def p_stmt_list_multi(p):
    'stmt_list : stmt_list statement'
    pass


def p_stmt_list_single(p):
    'stmt_list : statement'
    pass


def p_statement_simple(p):
    '''statement : declaration stmt_end
                 | assignment stmt_end
                 | write_stmt stmt_end
                 | read_stmt stmt_end
                 | return_stmt stmt_end
                 | func_call stmt_end'''
    pass


def p_statement_compound(p):
    '''statement : if_stmt
                 | while_stmt
                 | func_def'''
    pass


def p_statement_blank(p):
    'statement : NEWLINE'
    pass


# Reglas de recuperación para líneas con errores comunes.
def p_statement_recover_write_missing_rparen(p):
    'statement : WRITE LPAREN args_opt NEWLINE'
    pass


def p_statement_recover_read_missing_rparen(p):
    'statement : READ LPAREN read_args_opt NEWLINE'
    pass


def p_statement_recover_assignment_incomplete(p):
    '''statement : ID ASSIGN expression binary_operator SEMICOLON NEWLINE
                 | type ID ASSIGN expression binary_operator SEMICOLON NEWLINE
                 | RETURN SEMICOLON NEWLINE'''
    pass


def p_stmt_end(p):
    '''stmt_end : SEMICOLON NEWLINE
                | NEWLINE'''
    # NEWLINE sin ; se permite únicamente como recuperación; el error se agrega en precheck_syntax.
    pass


# =========================
# DECLARACIONES
# =========================

def p_declaration(p):
    'declaration : type decl_list'
    pass


def p_decl_list_single(p):
    'decl_list : decl_item'
    pass


def p_decl_list_multi(p):
    'decl_list : decl_item COMMA decl_list'
    pass


def p_decl_item_id(p):
    'decl_item : ID'
    pass


def p_decl_item_assign(p):
    'decl_item : ID ASSIGN expression'
    pass


def p_type(p):
    '''type : INT_TYPE
            | FLOAT_TYPE
            | BOOL_TYPE
            | STRING_TYPE'''
    pass


# =========================
# ASIGNACIÓN
# =========================

def p_assignment(p):
    'assignment : ID ASSIGN expression'
    pass


# =========================
# WRITE / READ / RETURN
# =========================

def p_write_stmt(p):
    'write_stmt : WRITE LPAREN args_opt RPAREN'
    pass


def p_read_stmt(p):
    'read_stmt : READ LPAREN read_args_opt RPAREN'
    pass


def p_return_stmt(p):
    'return_stmt : RETURN expression'
    # Importante: no se permite return vacío.
    pass


def p_args_opt(p):
    '''args_opt : args
                | empty'''
    pass


def p_args_single(p):
    'args : expression'
    pass


def p_args_multi(p):
    'args : expression COMMA args'
    pass


def p_read_args_opt(p):
    '''read_args_opt : read_args
                     | empty'''
    pass


def p_read_args_single_string(p):
    'read_args : STRING'
    pass


def p_read_args_single_id(p):
    'read_args : ID'
    pass


def p_read_args_prompt_and_id(p):
    'read_args : STRING COMMA ID'
    pass


# =========================
# FUNCIONES
# =========================

# Se exige tipo de retorno para evitar ambigüedad en Fase 3.
def p_func_def(p):
    'func_def : FUNC type ID LPAREN params_opt RPAREN COLON NEWLINE INDENT block DEDENT'
    pass


def p_params_opt(p):
    '''params_opt : params
                  | empty'''
    pass


def p_params_single(p):
    'params : param'
    pass


def p_params_multi(p):
    'params : param COMMA params'
    pass


# Se exigen parámetros tipados para facilitar comprobación posterior de tipos.
def p_param_typed(p):
    'param : type ID'
    pass


def p_func_call(p):
    'func_call : ID LPAREN args_opt RPAREN'
    pass


# =========================
# IF / ELIF / ELSE
# =========================

def p_if_stmt(p):
    'if_stmt : IF expression COLON NEWLINE INDENT block DEDENT elif_list else_opt'
    pass


def p_elif_list_multi(p):
    'elif_list : elif_list elif_item'
    pass


def p_elif_list_empty(p):
    'elif_list : empty'
    pass


def p_elif_item(p):
    'elif_item : ELIF expression COLON NEWLINE INDENT block DEDENT'
    pass


def p_else_opt_block(p):
    'else_opt : ELSE COLON NEWLINE INDENT block DEDENT'
    pass


# Recuperación: else sin ':' para continuar el análisis.
def p_else_opt_missing_colon(p):
    'else_opt : ELSE NEWLINE INDENT block DEDENT'
    pass


def p_else_opt_empty(p):
    'else_opt : empty'
    pass


# =========================
# WHILE
# =========================

def p_while_stmt(p):
    'while_stmt : WHILE expression COLON NEWLINE INDENT block DEDENT'
    pass


# =========================
# BLOQUES
# =========================

def p_block_multi(p):
    'block : block statement'
    pass


def p_block_single(p):
    'block : statement'
    pass


# =========================
# EXPRESIONES
# =========================

def p_expression_or(p):
    'expression : expression OR expression'
    pass


def p_expression_and(p):
    'expression : expression AND expression'
    pass


def p_expression_not(p):
    'expression : NOT expression'
    pass


def p_expression_compare(p):
    '''expression : expression GT expression
                  | expression LT expression
                  | expression GTE expression
                  | expression LTE expression
                  | expression EQ expression
                  | expression NEQ expression'''
    pass


def p_expression_arith(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULT expression
                  | expression DIV expression
                  | expression MOD expression'''
    pass


def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    pass


def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    pass


def p_expression_func_call(p):
    'expression : func_call'
    pass


def p_expression_id(p):
    'expression : ID'
    pass


def p_expression_literals(p):
    '''expression : INT
                  | FLOAT
                  | STRING
                  | BOOL'''
    pass


def p_binary_operator(p):
    '''binary_operator : PLUS
                       | MINUS
                       | MULT
                       | DIV
                       | MOD
                       | GT
                       | LT
                       | GTE
                       | LTE
                       | EQ
                       | NEQ
                       | AND
                       | OR'''
    pass


# =========================
# VACÍO
# =========================

def p_empty(p):
    'empty :'
    pass


# =========================
# ERRORES DE PLY
# =========================

def p_error(p):
    if p:
        line = getattr(p, 'lineno', '?')
        # Evitar duplicar errores que ya fueron reportados por recuperación o por el lexer.
        if isinstance(line, int) and (line in syntax_error_lines or line in lex_error_lines):
            return
        add_syntax_error("error sintáctico", p)
    else:
        add_syntax_error("sintaxis incompleta al final del archivo", line="?", col="?", symbol="EOF")


# =========================================
# EJECUCIÓN
# =========================================

_parser = None


def get_parser():
    global _parser
    if _parser is None:
        _parser = yacc.yacc(start='program', write_tables=False, debug=False)
    return _parser


def run_parser(text):
    global syntax_errors, syntax_error_keys, syntax_error_lines, lex_error_lines

    syntax_errors = []
    syntax_error_keys = set()
    syntax_error_lines = set()
    lex_error_lines = set()

    lexer = Lexer(text)
    tokens_list = lexer.tokenize()

    precheck_syntax(tokens_list, lexer.errors)

    adapter = PlyTokenAdapter(tokens_list)
    parser = get_parser()
    parser.parse(lexer=adapter, tracking=True)

    return lexer.errors, syntax_errors


def process_file(filename):
    if not filename.endswith(".mlng"):
        print(f"  Error: el archivo '{filename}' no tiene extensión .mlng")
        return

    print(f"Procesando {filename}...")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"  Error al leer {filename}: {e}")
        return

    lex_errors, syn_errors = run_parser(text)
    all_errors = lex_errors + syn_errors

    out_file = filename.replace(".mlng", ".parserMinilang.out")

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            if not all_errors:
                f.write("OK\n")
            else:
                for err in all_errors:
                    f.write(err + "\n")
    except Exception as e:
        print(f"  Error al escribir {out_file}: {e}")
        return

    if not all_errors:
        print("  OK")
    else:
        print("  → errores encontrados:")
        for err in all_errors:
            print("    ", err)

    print(f"  → salida generada: {out_file}")


def process_all_files():
    files = sorted(f for f in os.listdir() if f.endswith(".mlng"))

    if not files:
        print("No se encontraron archivos .mlng en la carpeta.")
        return

    for filename in files:
        process_file(filename)


def main():
    print("Proyecto - Fase 2 - Analizador Sintáctico Ascendente MiniLang")
    print("-------------------------------------------------------------\n")

    # Modos de uso:
    #   python parserMinilang.py archivo.mlng
    #   python parserMinilang.py --all
    #   python parserMinilang.py    -> solicita archivo
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            process_all_files()
        else:
            process_file(arg)
    else:
        filename = input("Ingrese el nombre del archivo .mlng: ").strip()
        process_file(filename)

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()
