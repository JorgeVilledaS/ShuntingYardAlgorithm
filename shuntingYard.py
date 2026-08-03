from dataclasses import dataclass

SIMBOLO_CONCATENACION = '·'  # símbolo interno para la concatenación explícita
                              # (NUNCA aparece en una regex real, así se evita
                              # la colisión con el '.' literal de las regex)

CARACTERES_UNARIOS_POSTFIJOS = {'*', '+', '?'}


@dataclass
class Token:
    tipo: str    # 'OPERANDO' | 'OPERADOR' | 'PARENTESIS_IZQ' | 'PARENTESIS_DER'
    valor: str

    def __repr__(self):
        return self.valor


# ------------------------------------------------------------------------
# 1) TOKENIZADOR
# ------------------------------------------------------------------------
def tokenizar(expresion_regular):
    """
    Recorre la expresión regular carácter por carácter y la convierte en una
    lista de Tokens, agrupando en un solo token: los caracteres escapados
    (\\x), las clases de caracteres [..] y los cuantificadores {m,n}.
    """
    tokens = []
    indice = 0
    longitud = len(expresion_regular)

    while indice < longitud:
        caracter_actual = expresion_regular[indice]

        # --- espacios en blanco: se ignoran (limpieza de formato) ---
        if caracter_actual == ' ':
            indice += 1
            continue

        # --- verificador de caracteres escapados por \ ---
        if caracter_actual == '\\':
            if indice + 1 < longitud:
                literal_escapado = expresion_regular[indice:indice + 2]
                tokens.append(Token('OPERANDO', literal_escapado))
                indice += 2
            else:
                # backslash suelto al final de la cadena: se toma literal
                tokens.append(Token('OPERANDO', caracter_actual))
                indice += 1
            continue

        # --- clase de caracteres [ ... ] ---
        if caracter_actual == '[':
            fin = indice + 1
            if fin < longitud and expresion_regular[fin] == '^':
                fin += 1
            if fin < longitud and expresion_regular[fin] == ']':
                fin += 1  # ']' justo al inicio de la clase se toma literal
            while fin < longitud and expresion_regular[fin] != ']':
                if expresion_regular[fin] == '\\':
                    fin += 2
                else:
                    fin += 1
            fin = min(fin, longitud - 1)
            clase_de_caracteres = expresion_regular[indice:fin + 1]
            tokens.append(Token('OPERANDO', clase_de_caracteres))
            indice = fin + 1
            continue

        # --- cuantificador de repetición { m , n } ---
        if caracter_actual == '{':
            posicion_cierre = expresion_regular.find('}', indice)
            if posicion_cierre == -1:
                # no hay cierre: se trata como carácter literal suelto
                tokens.append(Token('OPERANDO', caracter_actual))
                indice += 1
            else:
                cuantificador = expresion_regular[indice:posicion_cierre + 1]
                tokens.append(Token('OPERADOR', cuantificador))
                indice = posicion_cierre + 1
            continue

        # --- paréntesis y operadores de un solo carácter ---
        if caracter_actual == '(':
            tokens.append(Token('PARENTESIS_IZQ', caracter_actual))
        elif caracter_actual == ')':
            tokens.append(Token('PARENTESIS_DER', caracter_actual))
        elif caracter_actual == '|':
            tokens.append(Token('OPERADOR', caracter_actual))
        elif caracter_actual in CARACTERES_UNARIOS_POSTFIJOS:
            tokens.append(Token('OPERADOR', caracter_actual))
        else:
            # cualquier otro carácter (letras, dígitos, '.', '^', '$', etc.)
            # se trata como un operando literal
            tokens.append(Token('OPERANDO', caracter_actual))

        indice += 1

    return tokens


def es_cuantificador_llaves(token):
    return token.tipo == 'OPERADOR' and token.valor.startswith('{')


def es_operador_unario_postfijo(token):
    return token.tipo == 'OPERADOR' and (
        token.valor in CARACTERES_UNARIOS_POSTFIJOS or es_cuantificador_llaves(token)
    )


# ------------------------------------------------------------------------
# 2) INSERCION DE CONCATENACION EXPLICITA
# ------------------------------------------------------------------------
def insertar_concatenacion_explicita(tokens):
    """
    Recorre la lista de tokens ya formada y agrega el operador interno de
    concatenación (SIMBOLO_CONCATENACION) entre dos tokens consecutivos
    cuando ambos deben "pegarse" (ej: entre dos letras, entre una letra y
    un '(', entre un ')' y una letra, etc.), siguiendo la misma idea del
    formatRegEx() del pseudocódigo de referencia, pero trabajando sobre
    TOKENS (no sobre caracteres sueltos) para no romper clases [..],
    escapes \\x ni cuantificadores {m,n}.
    """
    tokens_con_concatenacion = []

    for indice, token_actual in enumerate(tokens):
        tokens_con_concatenacion.append(token_actual)

        if indice + 1 >= len(tokens):
            break

        token_siguiente = tokens[indice + 1]

        no_concatenar_por_actual = (
            token_actual.tipo == 'PARENTESIS_IZQ' or
            token_actual.valor == '|'
        )
        no_concatenar_por_siguiente = (
            token_siguiente.tipo == 'PARENTESIS_DER' or
            token_siguiente.valor == '|' or
            es_operador_unario_postfijo(token_siguiente)
        )

        if not no_concatenar_por_actual and not no_concatenar_por_siguiente:
            tokens_con_concatenacion.append(Token('OPERADOR', SIMBOLO_CONCATENACION))

    return tokens_con_concatenacion


# ------------------------------------------------------------------------
# 3) PRECEDENCIA
# ------------------------------------------------------------------------
def obtener_precedencia(token):
    if token.tipo == 'PARENTESIS_IZQ':
        return 1
    if token.valor == '|':
        return 2
    if token.valor == SIMBOLO_CONCATENACION:
        return 3
    if es_operador_unario_postfijo(token):
        return 4
    return 0


# ------------------------------------------------------------------------
# 4) SHUNTING YARD: INFIX -> POSTFIX (con registro de pasos)
# ------------------------------------------------------------------------
def infix_a_postfix(expresion_original):
    """
    Aplica el algoritmo de Shunting Yard sobre la expresión regular dada y
    devuelve una tupla (texto_postfix, lista_de_pasos) donde cada paso es
    un diccionario con el símbolo leído, la acción tomada, y el estado de
    la pila y de la salida en ese momento (para poder imprimir la traza
    completa del algoritmo).
    """
    tokens_originales = tokenizar(expresion_original)
    tokens = insertar_concatenacion_explicita(tokens_originales)

    pila_operadores = []
    salida_postfix = []
    pasos = []

    def texto_pila():
        return ' '.join(t.valor for t in pila_operadores) if pila_operadores else '(vacía)'

    def texto_salida():
        return ' '.join(t.valor for t in salida_postfix) if salida_postfix else '(vacía)'

    def registrar_paso(simbolo_leido, accion):
        pasos.append({
            'simbolo': simbolo_leido,
            'accion': accion,
            'pila': texto_pila(),
            'salida': texto_salida(),
        })

    for token in tokens:

        if token.tipo == 'OPERANDO':
            salida_postfix.append(token)
            registrar_paso(token.valor, 'Operando -> se agrega directamente a la salida')

        elif token.tipo == 'PARENTESIS_IZQ':
            pila_operadores.append(token)
            registrar_paso(token.valor, "Paréntesis izquierdo -> se apila")

        elif token.tipo == 'PARENTESIS_DER':
            operadores_desapilados = []
            while pila_operadores and pila_operadores[-1].tipo != 'PARENTESIS_IZQ':
                operador_desapilado = pila_operadores.pop()
                salida_postfix.append(operador_desapilado)
                operadores_desapilados.append(operador_desapilado.valor)
            if pila_operadores:
                pila_operadores.pop()  # se descarta el '(' correspondiente
            detalle = ', '.join(operadores_desapilados) if operadores_desapilados else 'ninguno'
            registrar_paso(
                token.valor,
                f"Paréntesis derecho -> se desapilan operadores ({detalle}) hasta el "
                f"'(' correspondiente y se descartan ambos paréntesis"
            )

        else:  # OPERADOR: |, concatenación, *, +, ?, {m,n}
            precedencia_del_actual = obtener_precedencia(token)
            operadores_desapilados = []
            while (pila_operadores and
                   pila_operadores[-1].tipo != 'PARENTESIS_IZQ' and
                   obtener_precedencia(pila_operadores[-1]) >= precedencia_del_actual):
                operador_desapilado = pila_operadores.pop()
                salida_postfix.append(operador_desapilado)
                operadores_desapilados.append(operador_desapilado.valor)
            pila_operadores.append(token)
            detalle = ', '.join(operadores_desapilados) if operadores_desapilados else 'ninguno'
            registrar_paso(
                token.valor,
                f"Operador (precedencia {precedencia_del_actual}) -> se desapilan operadores "
                f"con precedencia >= a la suya ({detalle}) y luego se apila '{token.valor}'"
            )

    # al terminar, se vacía toda la pila hacia la salida
    while pila_operadores:
        operador_restante = pila_operadores.pop()
        salida_postfix.append(operador_restante)
        registrar_paso(
            '(fin de expresión)',
            f"Se desapila el operador restante '{operador_restante.valor}'"
        )

    texto_postfix = ' '.join(t.valor for t in salida_postfix)
    return texto_postfix, pasos


# ------------------------------------------------------------------------
# 5) PROCESAMIENTO DEL ARCHIVO DE EXPRESIONES Y REPORTE
# ------------------------------------------------------------------------
def procesar_archivo(ruta_archivo_entrada, ruta_archivo_salida):
    with open(ruta_archivo_entrada, 'r', encoding='utf-8') as archivo:
        lineas = [linea.strip() for linea in archivo if linea.strip()]

    bloques_de_reporte = []

    for numero_linea, expresion in enumerate(lineas, start=1):
        texto_postfix, pasos = infix_a_postfix(expresion)

        bloque = []
        bloque.append('=' * 78)
        bloque.append(f'EXPRESION #{numero_linea} (infix):   {expresion}')
        bloque.append('-' * 78)
        bloque.append(f'{"Símbolo":<20}{"Pila":<28}{"Salida (postfix parcial)"}')
        bloque.append('-' * 78)
        for paso in pasos:
            bloque.append(f'{paso["simbolo"]:<20}{paso["pila"]:<28}{paso["salida"]}')
        bloque.append('-' * 78)
        bloque.append(f'RESULTADO POSTFIX:   {texto_postfix}')
        bloque.append('=' * 78)
        bloque.append('')

        bloques_de_reporte.append('\n'.join(bloque))
        print('\n'.join(bloque))

    with open(ruta_archivo_salida, 'w', encoding='utf-8') as archivo_salida:
        archivo_salida.write('\n'.join(bloques_de_reporte))


if __name__ == '__main__':
    procesar_archivo('expresiones.txt', 'resultados_postfix.txt')
