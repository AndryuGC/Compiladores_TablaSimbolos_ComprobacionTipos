# Proyecto Fase 2 - Analizador Sintáctico Ascendente (MiniLang)

**Curso:** Compiladores  
**Estudiante:** Andry González Cantoral  
**Fecha:** Abril 2026  

---

# Descripción

Este proyecto implementa un **compilador parcial para MiniLang**, específicamente:

- Fase 1: Analizador Léxico (Lexer)
- Fase 2: Analizador Sintáctico (Parser)

El sistema permite:

- Leer archivos `.mlng`
- Analizar tokens (lexer)
- Validar estructura del lenguaje (parser ascendente)
- Reportar errores léxicos y sintácticos
- Continuar análisis hasta el final del archivo (EOF)

---

## 📌 Instalación de PLY

Para ejecutar el parser ascendente es necesario instalar la librería **PLY (Python Lex-Yacc)**.

En Windows, se recomienda usar el comando:

**Terminal o Bash**
py -m pip install ply

---

# Cómo ejecutar

Ubicar todos los archivos en la misma carpeta y compilarlo con su IDE de confianza, las muestras técnicas serán con VS Code:

---

# Estructura del proyecto

Proyecto.py            → Analizador Léxico (Fase 1)
parserMinilang.py      → Analizador Sintáctico Ascendente con PLY (Fase 2)
*.mlng                 → Archivos de prueba
*.parser.out           → Resultados del parser

--- 

# Explicación de las Clases y Archivos del Código

## 📌 Archivo `Proyecto.py`

Este archivo corresponde a la **Fase 1** del proyecto y contiene la implementación del **analizador léxico (lexer)**.  
Su función principal es leer el código fuente escrito en MiniLang y convertirlo en una secuencia de **tokens** que posteriormente son utilizados por el parser de la Fase 2.

---

### 🔹 Diccionarios principales

Dentro del archivo se definen tres estructuras importantes:

- `KEYWORDS`: contiene las palabras reservadas del lenguaje, por ejemplo `if`, `else`, `while`, `int`, `float`, `bool`, `string`, `Read`, `Write`, `return`, `func`, `and`, `or`, `not`, `true`, `false`.
- `OPERATORS`: contiene los operadores del lenguaje, como `+`, `-`, `*`, `/`, `%`, `>`, `<`, `=`, `==`, `!=`, `>=`, `<=`.
- `SYMBOLS`: contiene símbolos de puntuación, como `(`, `)`, `:`, `,`, `;`.

Estas estructuras permiten clasificar rápidamente cada lexema encontrado durante el análisis.

---

### 🔹 Clase `Token`

La clase `Token` representa cada unidad léxica identificada en el programa.

Cada token almacena:

- `type`: tipo del token, por ejemplo `ID`, `INT`, `PLUS`, `IF`.
- `value`: valor asociado al token.
- `line`: línea donde aparece.
- `col_start`: columna inicial.
- `col_end`: columna final.

Esto permite que tanto el lexer como el parser puedan reportar errores con ubicación precisa.

---

### 🔹 Clase `Lexer`

La clase `Lexer` es la encargada de realizar el análisis léxico del archivo fuente.

#### Atributos principales
- `lines`: lista de líneas del archivo.
- `line_num`: contador de línea actual.
- `tokens`: lista de tokens generados.
- `errors`: lista de errores léxicos detectados.
- `indent_stack`: pila utilizada para controlar los niveles de indentación.
- `max_indent_levels`: límite máximo de niveles de indentación permitidos.

---

#### Método `tokenize()`

Este método recorre todas las líneas del archivo y llama a `process_line()` para analizarlas una por una.

Además:
- genera `DEDENT` al final si todavía quedan niveles abiertos,
- agrega el token `EOF` para indicar fin de archivo.

En otras palabras, este método produce la lista final de tokens que se utilizarán en el parser.

---

#### Método `process_line()`

Este método analiza cada línea individualmente.

Su trabajo incluye:
- contar la indentación inicial,
- ignorar líneas vacías o comentarios,
- reconocer identificadores y palabras reservadas,
- reconocer números enteros y flotantes,
- reconocer cadenas de texto,
- reconocer operadores y símbolos,
- generar errores léxicos cuando encuentra secuencias inválidas.

Aquí se generan tokens como:
- `ID`
- `INT`
- `FLOAT`
- `STRING`
- `IF`
- `WHILE`
- `PLUS`
- `SEMICOLON`
- entre otros.

También se agrega `NEWLINE` al final de cada línea con contenido.

---

#### Método `handle_indentation()`

Este método controla los bloques del lenguaje mediante indentación, de manera similar a Python.

Su función es:
- generar `INDENT` cuando la indentación aumenta,
- generar `DEDENT` cuando la indentación disminuye,
- detectar errores de indentación inválida.

Gracias a esto el lenguaje puede manejar estructuras como `if`, `while` y funciones con bloques internos.

---

### 🔹 Función `summarize_tokens()`

Esta función cuenta cuántos tokens de cada tipo fueron generados.

Por ejemplo:
- cuántas palabras reservadas hay,
- cuántos identificadores,
- cuántos enteros,
- cuántos strings,
- cuántos operadores,
- cuántos `INDENT`, `DEDENT`, `NEWLINE`, etc.

Su objetivo es generar un resumen estadístico del archivo analizado.

---

### 🔹 Función `main()` de `Proyecto.py`

La función principal de este archivo:

- busca archivos con extensión `.mlng`,
- los abre y analiza con el lexer,
- muestra errores léxicos en consola,
- genera un archivo `.out` con la lista de tokens,
- imprime un resumen del análisis.

Este archivo sirve como base léxica para todo el proyecto.

---

## 📌 Archivo `parserMinilang.py`

Este archivo corresponde a la **Fase 2** e implementa el **analizador sintáctico ascendente** del lenguaje MiniLang utilizando **PLY (Python Lex-Yacc)**.

Su función principal es tomar los tokens producidos por `Proyecto.py` y validar si la estructura del programa es correcta según la gramática del lenguaje.

---

### 🔹 Uso de `PLY`

PLY permite construir analizadores sintácticos mediante reglas gramaticales definidas como funciones de Python.

Por ejemplo, una regla como:

```python
def p_assignment(p):
<<<<<<< HEAD
    'assignment : ID ASSIGN expression'
=======
    'assignment : ID ASSIGN expression'
>>>>>>> c89bfed2ac03771229d311348be13a953c31050a
