# =========================================
# minilang.py
# MiniLang - Programa principal Fase 3
# Integra análisis léxico, sintáctico y semántico
# =========================================

import os
from parserMinilang import run_parser

#Se agrego
from semanticMinilang import analyze_ast_and_write_outputs


# ============================================================
# MINILANG - PROGRAMA PRINCIPAL
# Este archivo funciona como menú para probar archivos .mlng
# Usa:
#   Proyecto.py          -> Lexer
#   parserMinilang.py   -> Parser ascendente con PLY + AST
#   semanticMinilang.py -> Tabla de símbolos y comprobación de tipos
# ============================================================


def obtener_archivos_mlng():
    """
    Busca todos los archivos .mlng en la carpeta actual.
    """
    return sorted(f for f in os.listdir() if f.endswith(".mlng"))


#Se agrego
def escribir_parser_output(filename, errores_parser):
    """
    Genera el archivo .parserMinilang.out con el resultado léxico/sintáctico.
    Si no hay errores, escribe OK.
    """
    out_file = filename.replace(".mlng", ".parserMinilang.out")

    with open(out_file, "w", encoding="utf-8") as f:
        if not errores_parser:
            f.write("OK\n")
        else:
            for err in errores_parser:
                f.write(err + "\n")

    return out_file


#Se agrego
def ejecutar_parser_con_ast(text):
    """
    Ejecuta el parser solicitando el AST para Fase 3.
    Se deja con respaldo por si el parser expone run_parser_with_ast.
    """
    try:
        return run_parser(text, include_ast=True)
    except TypeError:
        from parserMinilang import run_parser_with_ast
        return run_parser_with_ast(text)


def analizar_archivo(filename):
    """
    Lee un archivo .mlng, ejecuta lexer + parser + análisis semántico,
    muestra el resultado en pantalla y genera archivos de salida:
    - .parserMinilang.out
    - .semantic.out
    - .symbols.out
    """
    if not os.path.exists(filename):
        print(f"\n[ERROR] El archivo '{filename}' no existe.\n")
        return

    if not filename.endswith(".mlng"):
        print("\n[ERROR] El archivo debe tener extensión .mlng\n")
        return

    print(f"\nProcesando {filename}...")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}\n")
        return

    #Se agrego
    # Fase 1 y Fase 2: lexer + parser. Además se obtiene AST para Fase 3.
    try:
        lex_errors, syn_errors, ast = ejecutar_parser_con_ast(text)
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar el parser: {e}\n")
        return

    errores_parser = lex_errors + syn_errors

    try:
        parser_out_file = escribir_parser_output(filename, errores_parser)
    except Exception as e:
        print(f"[ERROR] No se pudo escribir el archivo del parser: {e}\n")
        return

    #Se agrego
    # Si hay errores léxicos o sintácticos, no se ejecuta semántica.
    if errores_parser:
        print("Resultado: Se encontraron errores léxicos o sintácticos:")
        for err in errores_parser:
            print("  " + err)

        print(f"Archivo parser generado: {parser_out_file}")
        print("No se ejecutó análisis semántico porque el archivo no pasó léxico/sintaxis.\n")
        return

    #Se agrego
    # Fase 3: análisis semántico + tabla de símbolos.
    try:
        semantic_errors, symbol_table, semantic_file, symbols_file = analyze_ast_and_write_outputs(ast, filename)
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar el análisis semántico: {e}\n")
        return

    if semantic_errors:
        print("Resultado: Se encontraron errores semánticos:")
        for err in semantic_errors:
            print("  " + err)
    else:
        print("Resultado: OK")

    print(f"Archivo parser generado: {parser_out_file}")
    print(f"Archivo semántico generado: {semantic_file}")
    print(f"Tabla de símbolos generada: {symbols_file}\n")


def mostrar_archivos():
    """
    Muestra los archivos .mlng disponibles en la carpeta.
    """
    archivos = obtener_archivos_mlng()

    if not archivos:
        print("\nNo se encontraron archivos .mlng en la carpeta actual.\n")
        return []

    print("\nArchivos .mlng disponibles:")
    for i, archivo in enumerate(archivos, start=1):
        print(f"{i}. {archivo}")

    print()
    return archivos


def analizar_por_numero():
    """
    Permite seleccionar un archivo .mlng por número desde una lista.
    """
    archivos = mostrar_archivos()

    if not archivos:
        return

    try:
        opcion = int(input("Ingrese el número del archivo que desea analizar: "))

        if opcion < 1 or opcion > len(archivos):
            print("\n[ERROR] Opción fuera de rango.\n")
            return

        archivo_seleccionado = archivos[opcion - 1]
        analizar_archivo(archivo_seleccionado)

    except ValueError:
        print("\n[ERROR] Debe ingresar un número válido.\n")


def analizar_por_nombre():
    """
    Permite escribir manualmente el nombre del archivo.
    """
    filename = input("\nIngrese el nombre del archivo .mlng: ").strip()
    analizar_archivo(filename)


def analizar_todos():
    """
    Analiza automáticamente todos los archivos .mlng de la carpeta.
    """
    archivos = obtener_archivos_mlng()

    if not archivos:
        print("\nNo se encontraron archivos .mlng en la carpeta actual.\n")
        return

    print("\nAnalizando todos los archivos .mlng...\n")

    for archivo in archivos:
        analizar_archivo(archivo)

    print("Análisis completo de todos los archivos.\n")


def menu():
    """
    Menú principal del analizador MiniLang.
    """
    while True:
        print("======================================")
        #Se agrego
        print("   MINILANG - FASE 3 SEMÁNTICA")
        print("======================================")
        print("1. Ver archivos .mlng disponibles")
        print("2. Analizar archivo seleccionándolo por número")
        print("3. Analizar archivo escribiendo el nombre")
        print("4. Analizar todos los archivos .mlng")
        print("5. Salir")
        print("======================================")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            mostrar_archivos()

        elif opcion == "2":
            analizar_por_numero()

        elif opcion == "3":
            analizar_por_nombre()

        elif opcion == "4":
            analizar_todos()

        elif opcion == "5":
            print("\nSaliendo del analizador MiniLang...")
            break

        else:
            print("\n[ERROR] Opción inválida. Intente de nuevo.\n")


if __name__ == "__main__":
    menu()
