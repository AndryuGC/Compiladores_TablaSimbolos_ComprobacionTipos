import os
from parserMinilang import run_parser


# ============================================================
# MINILANG - PROGRAMA PRINCIPAL
# Este archivo funciona como menú para probar archivos .mlng
# Usa:
#   Proyecto.py        -> Lexer
#   parserMinilang.py -> Parser ascendente con PLY
# ============================================================


def obtener_archivos_mlng():
    """
    Busca todos los archivos .mlng en la carpeta actual.
    """
    return [f for f in os.listdir() if f.endswith(".mlng")]


def analizar_archivo(filename):
    """
    Lee un archivo .mlng, ejecuta el lexer y parser,
    muestra el resultado en pantalla y genera un archivo .parserMinilang.out.
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
        print(f"[ERROR] No se pudo escribir el archivo de salida: {e}\n")
        return

    if not all_errors:
        print("Resultado: OK")
    else:
        print("Resultado: Se encontraron errores:")
        for err in all_errors:
            print("  " + err)

    print(f"Archivo de salida generado: {out_file}\n")


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
        print("      MINILANG - FASE 2 PARSER")
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