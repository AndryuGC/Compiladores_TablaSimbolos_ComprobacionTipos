# =========================================
# Proyecto.py
# MiniLang - Analizador Léxico
# =========================================

import os

KEYWORDS = {
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "while": "WHILE",

    "int": "INT_TYPE",
    "float": "FLOAT_TYPE",
    "bool": "BOOL_TYPE",
    "string": "STRING_TYPE",

    "Read": "READ",
    "read": "READ",
    "Write": "WRITE",
    "write": "WRITE",
    "print": "WRITE",

    "return": "RETURN",

    "func": "FUNC",
    "def": "FUNC",

    "and": "AND",
    "or": "OR",
    "not": "NOT",

    "true": "BOOL",
    "false": "BOOL"
}

OPERATORS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULT",
    "/": "DIV",
    "%": "MOD",
    ">": "GT",
    "<": "LT",
    "=": "ASSIGN",
    "==": "EQ",
    "!=": "NEQ",
    ">=": "GTE",
    "<=": "LTE"
}

SYMBOLS = {
    "(": "LPAREN",
    ")": "RPAREN",
    ":": "COLON",
    ",": "COMMA",
    ";": "SEMICOLON"
}


class Token:
    def __init__(self, type_, value, line, col_start, col_end):
        self.type = type_
        self.value = value
        self.line = line
        self.col_start = col_start
        self.col_end = col_end

    def __str__(self):
        if self.value is not None:
            return f"{self.type}({self.value}) [{self.line}:{self.col_start}-{self.col_end}]"
        return f"{self.type} [{self.line}:{self.col_start}-{self.col_end}]"


def format_lex_error(line, col, symbol, message):
    return f"Línea {line}, columna {col}, símbolo '{symbol}': Error léxico: {message}"


class Lexer:
    def __init__(self, text):
        self.lines = text.splitlines()
        self.line_num = 0
        self.tokens = []
        self.errors = []
        self.indent_stack = [0]
        self.max_indent_levels = 5

    def tokenize(self):
        for raw_line in self.lines:
            self.line_num += 1
            self.process_line(raw_line)

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token("DEDENT", None, self.line_num, 1, 1))

        self.tokens.append(Token("EOF", None, self.line_num, 1, 1))
        return self.tokens

    def process_line(self, raw_line):
        i = 0
        indent = 0

        # Contar indentación inicial: espacio = 1, tab = 4.
        while i < len(raw_line) and raw_line[i] in (" ", "\t"):
            if raw_line[i] == " ":
                indent += 1
            else:
                indent += 4
            i += 1

        # Línea vacía o comentario completo.
        if i >= len(raw_line) or raw_line[i] == "#":
            return

        self.handle_indentation(indent)

        col = indent + 1
        line_has_tokens = False
        last_token_end_col = col - 1

        while i < len(raw_line):
            ch = raw_line[i]

            # Comentario desde aquí hasta fin de línea.
            if ch == "#":
                break

            if ch in (" ", "\t"):
                if ch == " ":
                    col += 1
                else:
                    col += 4
                i += 1
                continue

            start_col = col

            # IDENTIFICADORES / PALABRAS RESERVADAS.
            if ch.isalpha() or ch == "_":
                lex = ""
                while i < len(raw_line) and (raw_line[i].isalnum() or raw_line[i] == "_"):
                    lex += raw_line[i]
                    i += 1
                    col += 1

                if len(lex) > 31:
                    self.errors.append(
                        format_lex_error(self.line_num, start_col, lex, "identificador muy largo")
                    )
                    # No se trunca el identificador, porque truncarlo puede crear nombres falsos.

                token_type = KEYWORDS.get(lex, "ID")
                self.tokens.append(Token(token_type, lex, self.line_num, start_col, col - 1))
                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # NÚMEROS.
            if ch.isdigit():
                num = ""
                dot_count = 0

                while i < len(raw_line) and (raw_line[i].isdigit() or raw_line[i] == "."):
                    if raw_line[i] == ".":
                        dot_count += 1
                    num += raw_line[i]
                    i += 1
                    col += 1

                if dot_count > 1:
                    self.errors.append(
                        format_lex_error(self.line_num, start_col, num, "número mal formado")
                    )
                    # Se agrega como FLOAT para permitir que el parser continúe sin cascada.
                    self.tokens.append(Token("FLOAT", num, self.line_num, start_col, col - 1))
                else:
                    token_type = "FLOAT" if dot_count == 1 else "INT"
                    self.tokens.append(Token(token_type, num, self.line_num, start_col, col - 1))

                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # STRINGS.
            if ch == '"':
                i += 1
                col += 1
                value = ""

                while i < len(raw_line) and raw_line[i] != '"':
                    value += raw_line[i]
                    i += 1
                    col += 1

                if i >= len(raw_line):
                    self.errors.append(
                        format_lex_error(self.line_num, start_col, '"' + value, "cadena sin cerrar")
                    )
                    # Se agrega STRING de recuperación para evitar errores sintácticos en cascada.
                    self.tokens.append(Token("STRING", value, self.line_num, start_col, col - 1))
                    line_has_tokens = True
                    last_token_end_col = col - 1
                    break

                i += 1
                col += 1
                self.tokens.append(Token("STRING", value, self.line_num, start_col, col - 1))
                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # OPERADORES DE 2 CARACTERES.
            two = raw_line[i:i + 2]
            if two in OPERATORS:
                self.tokens.append(Token(OPERATORS[two], two, self.line_num, col, col + 1))
                i += 2
                col += 2
                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # OPERADORES DE 1 CARACTER.
            if ch in OPERATORS:
                self.tokens.append(Token(OPERATORS[ch], ch, self.line_num, col, col))
                i += 1
                col += 1
                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # SÍMBOLOS.
            if ch in SYMBOLS:
                self.tokens.append(Token(SYMBOLS[ch], ch, self.line_num, col, col))
                i += 1
                col += 1
                line_has_tokens = True
                last_token_end_col = col - 1
                continue

            # ERROR: carácter inesperado.
            self.errors.append(
                format_lex_error(self.line_num, col, ch, "carácter inesperado")
            )
            i += 1
            col += 1

        if line_has_tokens:
            newline_col = max(last_token_end_col, 1)
            self.tokens.append(Token("NEWLINE", None, self.line_num, newline_col, newline_col))

    def handle_indentation(self, spaces):
        current = self.indent_stack[-1]

        if spaces > current:
            if len(self.indent_stack) >= self.max_indent_levels + 1:
                self.errors.append(
                    format_lex_error(self.line_num, 1, "INDENT", "excede máximo de niveles de indentación")
                )
                return

            self.indent_stack.append(spaces)
            self.tokens.append(Token("INDENT", None, self.line_num, 1, spaces))
            return

        if spaces < current:
            original_stack = self.indent_stack[:]

            while len(self.indent_stack) > 1 and spaces < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token("DEDENT", None, self.line_num, 1, max(spaces, 1)))

            if self.indent_stack[-1] != spaces:
                self.errors.append(
                    format_lex_error(self.line_num, 1, "INDENT", "indentación inválida")
                )

                lower_levels = [lvl for lvl in original_stack if lvl < spaces]
                target = max(lower_levels) if lower_levels else 0

                while len(self.indent_stack) > 1 and self.indent_stack[-1] > target:
                    self.indent_stack.pop()

        # Si spaces == current, no se genera token.


def summarize_tokens(tokens, errors):
    summary = {
        "KEYWORDS": 0,
        "ID": 0,
        "INT": 0,
        "FLOAT": 0,
        "STRING": 0,
        "BOOL": 0,
        "OPERATORS": 0,
        "SYMBOLS": 0,
        "INDENT": 0,
        "DEDENT": 0,
        "NEWLINE": 0,
        "EOF": 0,
    }

    keyword_types = set(KEYWORDS.values()) - {"BOOL"}
    operator_types = set(OPERATORS.values())
    symbol_types = set(SYMBOLS.values())

    for t in tokens:
        if t.type == "ID":
            summary["ID"] += 1
        elif t.type == "INT":
            summary["INT"] += 1
        elif t.type == "FLOAT":
            summary["FLOAT"] += 1
        elif t.type == "STRING":
            summary["STRING"] += 1
        elif t.type == "BOOL":
            summary["BOOL"] += 1
        elif t.type in keyword_types:
            summary["KEYWORDS"] += 1
        elif t.type in operator_types:
            summary["OPERATORS"] += 1
        elif t.type in symbol_types:
            summary["SYMBOLS"] += 1
        elif t.type == "INDENT":
            summary["INDENT"] += 1
        elif t.type == "DEDENT":
            summary["DEDENT"] += 1
        elif t.type == "NEWLINE":
            summary["NEWLINE"] += 1
        elif t.type == "EOF":
            summary["EOF"] += 1

    total_tokens = len(tokens)
    return summary, total_tokens, len(errors)


def main():
    print("Proyecto - Fase 2 - MiniLang")
    print("Analizador Léxico")
    print("------------------------------\n")

    files = [f for f in os.listdir() if f.endswith(".mlng")]

    if not files:
        print("No se encontraron archivos .mlng en la carpeta.")
        return

    for filename in files:
        print(f"Procesando {filename}...")

        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error al leer {filename}: {e}")
            continue

        lexer = Lexer(text)
        tokens = lexer.tokenize()

        summary, total, err_count = summarize_tokens(tokens, lexer.errors)

        summary_parts = [f"Total={total}"]
        summary_parts += [f"{k}={v}" for k, v in summary.items()]
        summary_parts.append(f"ERRORES={err_count}")
        summary_line = "Resumen: " + " | ".join(summary_parts)

        out_file = filename.replace(".mlng", ".out")

        try:
            with open(out_file, "w", encoding="utf-8") as f:
                for t in tokens:
                    f.write(str(t) + "\n")
                f.write(summary_line + "\n")
        except Exception as e:
            print(f"Error al escribir {out_file}: {e}")
            continue

        if lexer.errors:
            print("  → errores encontrados:")
            for e in lexer.errors:
                print("    ", e)
        else:
            print("  → análisis completado")

        print("  → " + summary_line)

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()