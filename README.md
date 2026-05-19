# Proyecto Fase 3 - MiniLang

**Curso:** Compiladores  
**Estudiante:** Andry González Cantoral  
**Fecha:** Mayo 2026

## Descripción
Este proyecto implementa un compilador parcial para **MiniLang** dividido en tres fases:
- **Fase 1:** Analizador léxico.
- **Fase 2:** Analizador sintáctico ascendente con PLY.
- **Fase 3:** Tabla de símbolos y comprobación de tipos.

El sistema lee archivos `.mlng`, reconoce tokens, valida la gramática, construye un AST básico, genera una tabla de símbolos y reporta errores léxicos, sintácticos o semánticos.

## Instalación
Instalar PLY:

```bash
py -m pip install ply
```

O usando `requirements.txt`:

```bash
py -m pip install -r requirements.txt
```

## Ejecución
Ejecutar el programa principal:

```bash
py minilang.py
```

El menú permite:

```text
1. Ver archivos .mlng disponibles
2. Analizar archivo seleccionándolo por número
3. Analizar archivo escribiendo el nombre
4. Analizar todos los archivos .mlng
5. Salir
```

También se puede probar el parser con AST:

```bash
py parserMinilang.py --ast "Prueba9_OK_TodosCasosGrande.mlng"
```

O el semántico directamente:

```bash
py semanticMinilang.py "Prueba9_OK_TodosCasosGrande.mlng"
```

## Estructura del proyecto
```text
Proyecto.py              -> Analizador léxico
parserMinilang.py        -> Parser ascendente con PLY + AST
semanticMinilang.py      -> Tabla de símbolos y comprobación de tipos
minilang.py              -> Menú principal integrado
requirements.txt         -> Dependencias
*.mlng                   -> Pruebas
*.parserMinilang.out     -> Resultado léxico/sintáctico
*.semantic.out           -> Resultado semántico
*.symbols.out            -> Tabla de símbolos
```

## Flujo del compilador
```text
Archivo .mlng
   -> Lexer
   -> Parser ascendente
   -> AST
   -> Análisis semántico
   -> Tabla de símbolos y comprobación de tipos
   -> Archivos de salida
```

Si existen errores léxicos o sintácticos, no se ejecuta el análisis semántico porque este necesita un AST válido.

## Proyecto.py - Fase 1
`Proyecto.py` contiene el analizador léxico. Lee el código fuente y lo convierte en tokens.

Reconoce:
- Palabras reservadas: `if`, `elif`, `else`, `while`, `int`, `float`, `bool`, `string`, `Read`, `Write`, `return`, `func`, `def`, `and`, `or`, `not`, `true`, `false`.
- Identificadores, enteros, flotantes, cadenas y booleanos.
- Operadores: `+`, `-`, `*`, `/`, `%`, `>`, `<`, `=`, `==`, `!=`, `>=`, `<=`.
- Símbolos: `(`, `)`, `:`, `,`, `;`.
- Bloques mediante `INDENT`, `DEDENT` y `NEWLINE`.

Errores léxicos detectados:
- Número mal formado.
- Cadena sin cerrar.
- Carácter inesperado.
- Identificador demasiado largo.
- Indentación inválida.

### Agregado en Fase 3
```python
#Se agrego
"const": "CONST",
"double": "FLOAT_TYPE",
```

Esto permite reconocer constantes y usar `double` como alias de `float`.

## parserMinilang.py - Fase 2 y base de Fase 3
`parserMinilang.py` implementa el parser ascendente con PLY. Valida la estructura del programa y reporta errores sintácticos con línea, columna y símbolo.

Reconoce:
- Declaraciones de variables y constantes.
- Asignaciones.
- Expresiones aritméticas, lógicas y comparaciones.
- `Read`, `Write`, `if`, `elif`, `else`, `while`.
- Funciones con parámetros tipados.
- Llamadas a funciones.
- `return` con expresión obligatoria.

Precedencia aplicada, de menor a mayor:
```text
or, and, not, comparaciones, +/-, */%/, menos unario
```

### Agregado en Fase 3
El parser ahora también construye un AST básico con nodos como:

```text
Program, Declaration, Assignment, BinaryOp, UnaryOp, Literal, Identifier,
If, While, FunctionDef, FunctionCall, Return, Read, Write
```

También se agregó soporte sintáctico para:

```mlng
const int limite;
double radio;
```

La función `run_parser_with_ast()` devuelve errores léxicos, errores sintácticos y el AST.

## semanticMinilang.py - Fase 3
`semanticMinilang.py` realiza el análisis semántico usando el AST generado por el parser.

### Tabla de símbolos
La tabla guarda:
- Nombre.
- Categoría: variable, constante, función o parámetro.
- Tipo: `int`, `float`, `string`, `bool`.
- Valor calculado cuando es posible.
- Ámbito: `global` o `func:nombre`.
- Línea y columna.

La tabla se genera en un archivo `.symbols.out`.

### Comprobaciones semánticas
Detecta:
- Variable no declarada.
- Identificador duplicado en el mismo ámbito.
- Constante reasignada.
- Asignación incompatible.
- Operación inválida entre tipos.
- Condición de `if` o `while` que no sea `bool`.
- Función no declarada.
- Cantidad incorrecta de argumentos.
- Tipo incorrecto en argumentos.
- `return` fuera de función.
- Tipo de retorno incompatible.

### Reglas de tipos
| Caso | Resultado |
|---|---|
| `int + int` | `int` |
| `int + float` | `float` |
| `float + int` | `float` |
| `float + float` | `float` |
| `string + string` | `string` |
| `int + string` | Error |
| `bool + int` | Error |
| Comparaciones válidas | `bool` |
| Operadores lógicos | solo `bool` con `bool` |

Se permite coerción de `int` a `float`, pero no de `float` a `int`.

## minilang.py - Programa principal
`minilang.py` integra las tres fases:

```text
Lexer -> Parser -> AST -> Análisis semántico -> Tabla de símbolos
```

Si el archivo es correcto, imprime `OK`. Si hay errores, muestra la lista correspondiente. Además genera:

```text
archivo.parserMinilang.out
archivo.semantic.out
archivo.symbols.out
```

## Pruebas oficiales
| Archivo | Resultado esperado |
|---|---|
| `Prueba1_OK_HolaMundo.mlng` | OK |
| `Prueba2_OK_Aritmetica.mlng` | OK |
| `Prueba3_OK_InputIf.mlng` | OK |
| `Prueba4_OK_FuncionParametros.mlng` | OK |
| `Prueba5_OK_WhileEntradaSalida.mlng` | OK |
| `Prueba6_ErrorLexico.mlng` | Error léxico |
| `Prueba7_ErrorSintactico.mlng` | Error sintáctico |
| `Prueba8_ErrorSemantico.mlng` | Error semántico |
| `Prueba9_OK_TodosCasosGrande.mlng` | OK grande |
| `Prueba10_OK_ConstDouble.mlng` | OK con `const` y `double` |
| `Prueba11_ErrorConstante.mlng` | Error por reasignar constante |

## Ejemplo de error semántico
Código:

```mlng
int edad;
edad = true;
```

Salida esperada:

```text
Línea 2, columna 1: Error semántico: no se puede asignar bool a int en 'edad'
```

## Decisiones de diseño
- Se separaron las fases en archivos distintos para mantener claridad.
- El lexer no realiza validaciones semánticas.
- El parser valida estructura y construye AST.
- El semántico usa el AST para revisar tipos, funciones, constantes y símbolos.
- No se simulan completamente ciclos ni ejecución dinámica; solo se evalúan expresiones directas cuando es posible.
- Los errores léxicos o sintácticos detienen la fase semántica.

## Comandos útiles de Git
```bash
git add .
git commit -m "Actualiza fase 3 de MiniLang"
git push
```

## Estado final
El proyecto integra las tres fases solicitadas: análisis léxico, análisis sintáctico ascendente, tabla de símbolos y comprobación de tipos para MiniLang.
