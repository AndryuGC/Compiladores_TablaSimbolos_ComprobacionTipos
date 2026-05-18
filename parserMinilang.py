# =========================================
# parserMinilang.py
# MiniLang - Analizador Sintáctico Ascendente con PLY
# Fase 3: ahora también construye AST para análisis semántico
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
    #Se agrego
    'CONST',
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

        self.lineno = tok.lineno
        self.lexpos = tok.lexpos

        return tok


# =========================================
#Se agrego
# NODOS PARA AST
# El parser ahora devuelve una estructura del programa para Fase 3.
# =========================================

def make_node(node, line=None, col=None, **kwargs):
    data = {
        "node": node,
        "line": line,
        "col": col,
    }
    data.update(kwargs)
    return data


def token_line_col(p, index):
    """
    Obtiene línea y columna desde un símbolo terminal de PLY.
    Se usa para guardar ubicación en los nodos del AST.
    """
    try:
        tok = p.slice[index]
        line = getattr(tok, "lineno", p.lineno(index))
        col = getattr(tok, "col_start", getattr(tok, "lexpos", p.lexpos(index)))
        return line, col
    except Exception:
        return "?", "?"


def normalize_type(type_token):
    """
    Convierte tokens de tipo al nombre interno usado por el analizador semántico.
    """
    mapping = {
        "INT_TYPE": "int",
        "FLOAT_TYPE": "float",
        "BOOL_TYPE": "bool",
        "STRING_TYPE": "string",
    }
    return mapping.get(type_token, str(type_token))


def normalize_literal(token_type, value):
    """
    Convierte literales del lexer a valor Python y tipo MiniLang.
    """
    if token_type == "INT":
        try:
            return int(value), "int"
        except Exception:
            return value, "int"

    if token_type == "FLOAT":
        try:
            return float(value), "float"
        except Exception:
            return value, "float"

    if token_type == "STRING":
        return value, "string"

    if token_type == "BOOL":
        return str(value).lower() == "true", "bool"

    return value, "unknown"


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
    #Se agrego
    'CONST',
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

        if first.type in ('IF', 'ELIF', 'WHILE', 'FUNC') and not line_has_type(line_tokens, 'COLON'):
            add_syntax_error("falta ':' al final del encabezado del bloque", newline)
            continue

        if first.type == 'ELSE' and not line_has_type(line_tokens, 'COLON'):
            add_syntax_error("falta ':' después de else", newline)
            continue

        if has_unbalanced_parentheses(line_tokens):
            add_syntax_error("paréntesis no cerrado", newline)
            continue

        if first.type == 'RETURN':
            before_end, end_tok = get_token_before_semicolon_or_newline(line_tokens)
            if before_end.type == 'RETURN':
                add_syntax_error("return requiere una expresión de retorno", end_tok)
                continue

        before_end, end_tok = get_token_before_semicolon_or_newline(line_tokens)
        if before_end and before_end.type in BINARY_OPERATORS:
            add_syntax_error("expresión incompleta", end_tok)
            continue

        if first.type in SIMPLE_STARTERS and first.line not in lex_error_lines:
            if last is not None and last.type != 'SEMICOLON':
                add_syntax_error("falta ';' al final de la instrucción", newline)
                continue

    for line_tokens in groups:
        first = first_real_token(line_tokens)
        newline = find_newline(line_tokens)

        if first is None:
            continue

        if first.type in COMPOUND_STARTERS and line_has_type(line_tokens, 'COLON'):
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
    #Se agrego
    p[0] = make_node("Program", statements=p[2] if p[2] is not None else [])


def p_opt_newlines(p):
    '''opt_newlines : opt_newlines NEWLINE
                    | empty'''
    #Se agrego
    p[0] = None


def p_stmt_list_multi(p):
    'stmt_list : stmt_list statement'
    #Se agrego
    p[0] = list(p[1]) if p[1] is not None else []
    if p[2] is not None:
        p[0].append(p[2])


def p_stmt_list_single(p):
    'stmt_list : statement'
    #Se agrego
    p[0] = [] if p[1] is None else [p[1]]


def p_statement_simple(p):
    '''statement : declaration stmt_end
                 | const_declaration stmt_end
                 | assignment stmt_end
                 | write_stmt stmt_end
                 | read_stmt stmt_end
                 | return_stmt stmt_end
                 | func_call stmt_end'''
    #Se agrego
    p[0] = p[1]


def p_statement_compound(p):
    '''statement : if_stmt
                 | while_stmt
                 | func_def'''
    #Se agrego
    p[0] = p[1]


def p_statement_blank(p):
    'statement : NEWLINE'
    #Se agrego
    p[0] = None


# Reglas de recuperación para líneas con errores comunes.
def p_statement_recover_write_missing_rparen(p):
    'statement : WRITE LPAREN args_opt NEWLINE'
    #Se agrego
    p[0] = None


def p_statement_recover_read_missing_rparen(p):
    'statement : READ LPAREN read_args_opt NEWLINE'
    #Se agrego
    p[0] = None


def p_statement_recover_assignment_incomplete(p):
    '''statement : ID ASSIGN expression binary_operator SEMICOLON NEWLINE
                 | type ID ASSIGN expression binary_operator SEMICOLON NEWLINE
                 | RETURN SEMICOLON NEWLINE'''
    #Se agrego
    p[0] = None


def p_stmt_end(p):
    '''stmt_end : SEMICOLON NEWLINE
                | NEWLINE'''
    # NEWLINE sin ; se permite únicamente como recuperación; el error se agrega en precheck_syntax.
    #Se agrego
    p[0] = None


# =========================
# DECLARACIONES
# =========================

def p_declaration(p):
    'declaration : type decl_list'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Declaration", line=line, col=col, data_type=p[1], items=p[2], is_const=False)


#Se agrego
def p_const_declaration(p):
    'const_declaration : CONST type decl_list'
    line, col = token_line_col(p, 1)
    p[0] = make_node("Declaration", line=line, col=col, data_type=p[2], items=p[3], is_const=True)


def p_decl_list_single(p):
    'decl_list : decl_item'
    #Se agrego
    p[0] = [p[1]]


def p_decl_list_multi(p):
    'decl_list : decl_item COMMA decl_list'
    #Se agrego
    p[0] = [p[1]] + p[3]


def p_decl_item_id(p):
    'decl_item : ID'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Declarator", line=line, col=col, name=p[1], value=None)


def p_decl_item_assign(p):
    'decl_item : ID ASSIGN expression'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Declarator", line=line, col=col, name=p[1], value=p[3])


def p_type(p):
    '''type : INT_TYPE
            | FLOAT_TYPE
            | BOOL_TYPE
            | STRING_TYPE'''
    #Se agrego
    p[0] = normalize_type(p.slice[1].type)


# =========================
# ASIGNACIÓN
# =========================

def p_assignment(p):
    'assignment : ID ASSIGN expression'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Assignment", line=line, col=col, name=p[1], value=p[3])


# =========================
# WRITE / READ / RETURN
# =========================

def p_write_stmt(p):
    'write_stmt : WRITE LPAREN args_opt RPAREN'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Write", line=line, col=col, args=p[3])


def p_read_stmt(p):
    'read_stmt : READ LPAREN read_args_opt RPAREN'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Read", line=line, col=col, args=p[3])


def p_return_stmt(p):
    'return_stmt : RETURN expression'
    # Importante: no se permite return vacío.
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Return", line=line, col=col, value=p[2])


def p_args_opt(p):
    '''args_opt : args
                | empty'''
    #Se agrego
    p[0] = p[1] if p[1] is not None else []


def p_args_single(p):
    'args : expression'
    #Se agrego
    p[0] = [p[1]]


def p_args_multi(p):
    'args : expression COMMA args'
    #Se agrego
    p[0] = [p[1]] + p[3]


def p_read_args_opt(p):
    '''read_args_opt : read_args
                     | empty'''
    #Se agrego
    p[0] = p[1] if p[1] is not None else []


def p_read_args_single_string(p):
    'read_args : STRING'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = [make_node("Literal", line=line, col=col, value=p[1], data_type="string")]


def p_read_args_single_id(p):
    'read_args : ID'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = [make_node("Identifier", line=line, col=col, name=p[1])]


def p_read_args_prompt_and_id(p):
    'read_args : STRING COMMA ID'
    #Se agrego
    line1, col1 = token_line_col(p, 1)
    line3, col3 = token_line_col(p, 3)
    p[0] = [
        make_node("Literal", line=line1, col=col1, value=p[1], data_type="string"),
        make_node("Identifier", line=line3, col=col3, name=p[3])
    ]


# =========================
# FUNCIONES
# =========================

# Se exige tipo de retorno para evitar ambigüedad en Fase 3.
def p_func_def(p):
    'func_def : FUNC type ID LPAREN params_opt RPAREN COLON NEWLINE INDENT block DEDENT'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node(
        "FunctionDef",
        line=line,
        col=col,
        name=p[3],
        return_type=p[2],
        params=p[5],
        body=p[10]
    )


def p_params_opt(p):
    '''params_opt : params
                  | empty'''
    #Se agrego
    p[0] = p[1] if p[1] is not None else []


def p_params_single(p):
    'params : param'
    #Se agrego
    p[0] = [p[1]]


def p_params_multi(p):
    'params : param COMMA params'
    #Se agrego
    p[0] = [p[1]] + p[3]


# Se exigen parámetros tipados para facilitar comprobación posterior de tipos.
def p_param_typed(p):
    'param : type ID'
    #Se agrego
    line, col = token_line_col(p, 2)
    p[0] = make_node("Param", line=line, col=col, name=p[2], data_type=p[1])


def p_func_call(p):
    'func_call : ID LPAREN args_opt RPAREN'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("FunctionCall", line=line, col=col, name=p[1], args=p[3])


# =========================
# IF / ELIF / ELSE
# =========================

def p_if_stmt(p):
    'if_stmt : IF expression COLON NEWLINE INDENT block DEDENT elif_list else_opt'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node(
        "If",
        line=line,
        col=col,
        condition=p[2],
        then_body=p[6],
        elifs=p[8],
        else_body=p[9]
    )


def p_elif_list_multi(p):
    'elif_list : elif_list elif_item'
    #Se agrego
    p[0] = list(p[1]) if p[1] is not None else []
    if p[2] is not None:
        p[0].append(p[2])


def p_elif_list_empty(p):
    'elif_list : empty'
    #Se agrego
    p[0] = []


def p_elif_item(p):
    'elif_item : ELIF expression COLON NEWLINE INDENT block DEDENT'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Elif", line=line, col=col, condition=p[2], body=p[6])


def p_else_opt_block(p):
    'else_opt : ELSE COLON NEWLINE INDENT block DEDENT'
    #Se agrego
    p[0] = p[5]


# Recuperación: else sin ':' para continuar el análisis.
def p_else_opt_missing_colon(p):
    'else_opt : ELSE NEWLINE INDENT block DEDENT'
    #Se agrego
    p[0] = p[4]


def p_else_opt_empty(p):
    'else_opt : empty'
    #Se agrego
    p[0] = []


# =========================
# WHILE
# =========================

def p_while_stmt(p):
    'while_stmt : WHILE expression COLON NEWLINE INDENT block DEDENT'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("While", line=line, col=col, condition=p[2], body=p[6])


# =========================
# BLOQUES
# =========================

def p_block_multi(p):
    'block : block statement'
    #Se agrego
    p[0] = list(p[1]) if p[1] is not None else []
    if p[2] is not None:
        p[0].append(p[2])


def p_block_single(p):
    'block : statement'
    #Se agrego
    p[0] = [] if p[1] is None else [p[1]]


# =========================
# EXPRESIONES
# =========================

def p_expression_or(p):
    'expression : expression OR expression'
    #Se agrego
    line, col = token_line_col(p, 2)
    p[0] = make_node("BinaryOp", line=line, col=col, op="or", left=p[1], right=p[3])


def p_expression_and(p):
    'expression : expression AND expression'
    #Se agrego
    line, col = token_line_col(p, 2)
    p[0] = make_node("BinaryOp", line=line, col=col, op="and", left=p[1], right=p[3])


def p_expression_not(p):
    'expression : NOT expression'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("UnaryOp", line=line, col=col, op="not", operand=p[2])


def p_expression_compare(p):
    '''expression : expression GT expression
                  | expression LT expression
                  | expression GTE expression
                  | expression LTE expression
                  | expression EQ expression
                  | expression NEQ expression'''
    #Se agrego
    line, col = token_line_col(p, 2)
    p[0] = make_node("BinaryOp", line=line, col=col, op=p[2], left=p[1], right=p[3])


def p_expression_arith(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULT expression
                  | expression DIV expression
                  | expression MOD expression'''
    #Se agrego
    line, col = token_line_col(p, 2)
    p[0] = make_node("BinaryOp", line=line, col=col, op=p[2], left=p[1], right=p[3])


def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    #Se agrego
    p[0] = p[2]


def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("UnaryOp", line=line, col=col, op="-", operand=p[2])


def p_expression_func_call(p):
    'expression : func_call'
    #Se agrego
    p[0] = p[1]


def p_expression_id(p):
    'expression : ID'
    #Se agrego
    line, col = token_line_col(p, 1)
    p[0] = make_node("Identifier", line=line, col=col, name=p[1])


def p_expression_literals(p):
    '''expression : INT
                  | FLOAT
                  | STRING
                  | BOOL'''
    #Se agrego
    line, col = token_line_col(p, 1)
    value, data_type = normalize_literal(p.slice[1].type, p[1])
    p[0] = make_node("Literal", line=line, col=col, value=value, data_type=data_type)


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
    #Se agrego
    p[0] = p[1]


# =========================
# VACÍO
# =========================

def p_empty(p):
    'empty :'
    #Se agrego
    p[0] = None


# =========================
# ERRORES DE PLY
# =========================

def p_error(p):
    if p:
        line = getattr(p, 'lineno', '?')
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


#Se agrego
def run_parser_with_ast(text):
    """
    Ejecuta lexer + parser y devuelve también el AST.
    Esta función será usada por Fase 3.
    """
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
    ast = parser.parse(lexer=adapter, tracking=True)

    return lexer.errors, syntax_errors, ast


def run_parser(text, include_ast=False):
    """
    Ejecuta el parser.

    Por compatibilidad con el minilang.py actual, por defecto devuelve:
        lexer.errors, syntax_errors

    Para Fase 3 se puede usar:
        run_parser(text, include_ast=True)
    y devuelve:
        lexer.errors, syntax_errors, ast
    """
    #Se agrego
    lex_errors, syn_errors, ast = run_parser_with_ast(text)

    if include_ast:
        return lex_errors, syn_errors, ast

    return lex_errors, syn_errors


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


#Se agrego
def process_file_with_ast_debug(filename):
    """
    Utilidad opcional para revisar rápidamente si el AST se está construyendo.
    No es necesario usarla en la entrega final.
    """
    if not filename.endswith(".mlng"):
        print(f"  Error: el archivo '{filename}' no tiene extensión .mlng")
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"  Error al leer {filename}: {e}")
        return

    lex_errors, syn_errors, ast = run_parser(text, include_ast=True)

    if lex_errors or syn_errors:
        print("No se muestra AST porque hay errores léxicos o sintácticos.")
        for err in lex_errors + syn_errors:
            print(err)
        return

    print(ast)


def process_all_files():
    files = sorted(f for f in os.listdir() if f.endswith(".mlng"))

    if not files:
        print("No se encontraron archivos .mlng en la carpeta.")
        return

    for filename in files:
        process_file(filename)


def main():
    print("Proyecto - Fase 2/Fase 3 - Analizador Sintáctico Ascendente MiniLang")
    print("---------------------------------------------------------------------\n")

    # Modos de uso:
    #   python parserMinilang.py archivo.mlng
    #   python parserMinilang.py --all
    #   python parserMinilang.py --ast archivo.mlng
    #   python parserMinilang.py    -> solicita archivo
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            process_all_files()
        #Se agrego
        elif arg == "--ast" and len(sys.argv) > 2:
            process_file_with_ast_debug(sys.argv[2])
        else:
            process_file(arg)
    else:
        filename = input("Ingrese el nombre del archivo .mlng: ").strip()
        process_file(filename)

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()
