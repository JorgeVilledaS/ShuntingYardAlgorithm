
 SHUNTING YARD PARA EXPRESIONES REGULARES (infix -> postfix)
==============================================================================
 
EXPLICACION BREVE DEL ALGORITMO
--------------------------------
El algoritmo de Shunting Yard fue creado por Edsger Dijkstra (De mis programadores favoritos por su sencillez y tremendas frases) para convertir
expresiones matemáticas de notación infix (donde el operador va ENTRE los
operandos, ej. a+b) a notación postfix o "notación polaca inversa" (donde el
operador va DESPUES de los operandos, ej. ab+). Esta conversión es muy útil
porque una expresión en postfix se puede evaluar o construir (en nuestro caso,
construir un autómata con el algoritmo de Thompson visto en clase) usando una simple pila,
sin necesidad de preocuparse por paréntesis ni por reglas de precedencia.
 
El algoritmo recorre la expresión de izquierda a derecha usando dos
estructuras:
  1) Una PILA (stack) que guarda temporalmente los operadores y paréntesis.
  2) Una SALIDA (cola/lista) donde se va construyendo el resultado postfix.
 
La regla general es:
  - Si el símbolo leído es un OPERANDO (un carácter literal, una clase de
    caracteres [..], o un carácter escapado \\x), se agrega directamente a
    la salida.
  - Si el símbolo es un paréntesis izquierdo '(', se apila.
  - Si el símbolo es un paréntesis derecho ')', se desapilan operadores hacia
    la salida hasta encontrar el '(' correspondiente, el cual se descarta
    (ni el '(' ni el ')' aparecen jamás en el resultado postfix).
  - Si el símbolo es un OPERADOR (|, concatenación, *, +, ?, {m,n}), se
    desapilan de la pila todos los operadores con precedencia MAYOR O IGUAL
    a la del operador leído (porque deben aplicarse primero) y se agregan a
    la salida; luego se apila el operador leído.
  - Al terminar de leer toda la expresión, se desapila todo lo que quede en
    la pila y se agrega a la salida.
 
Para expresiones regulares se usan las siguientes precedencias (de menor a
mayor), siguiendo el pseudocódigo de referencia:
    '('                 -> 1  (marcador de agrupación)
    '|'  (unión / OR)   -> 2
    '.'  (concatenación)-> 3
    '?','*','+','{m,n}' -> 4  (cuantificadores, operadores unarios postfijos)
 
PROBLEMAS PARTICULARES DE LAS REGEX (y cómo los resolvimos)
-------------------------------------------------------------
1) Concatenación implícita: en regex "ab" significa "a concatenado con b",
   pero no existe un símbolo visible para la concatenación en la expresión
   original. El algoritmo necesita insertar un operador explícito de
   concatenación entre operandos/grupos consecutivos para poder aplicarle
   las reglas de precedencia igual que a cualquier otro operador binario.
 
2) El carácter '.' YA es un metacarácter válido en regex (significa
   "cualquier carácter"), por lo que NO se puede reutilizar el punto como
   símbolo de concatenación explícita (el pseudocódigo de referencia hace
   esto y por eso el enunciado advierte que "esto le dará problemas").
   SOLUCIÓN: usamos un símbolo interno distinto, '·' (punto medio, no es un
   carácter válido de regex), exclusivamente para representar la
   concatenación explícita. Así el '.' literal de la regex (por ejemplo en
   ^[aZ].com{5,30}) se mantiene intacto como OPERANDO y nunca se confunde
   con el operador de concatenación.
 
3) Caracteres escapados con '\\': un '\\' seguido de cualquier carácter
   (ej. \\. , \\( , \\* ) debe tratarse como UN SOLO operando literal, no
   como dos símbolos separados. Implementamos un "verificador de escape" en
   el tokenizador: al encontrar '\\' se consume junto con el siguiente
   carácter como un único token.
 
4) Clases de caracteres [..]: todo lo que está entre '[' y ']' (respetando
   escapes internos) se trata como UN SOLO operando (no se le inserta
   concatenación interna carácter por carácter).
 
5) Cuantificadores de repetición {m,n}: se tratan igual que '*'/'+'/'?',
   es decir, como operadores UNARIOS POSTFIJOS de alta precedencia (4), que
   se aplican al operando/grupo inmediatamente anterior y NUNCA disparan
   una concatenación antes de sí mismos.
 
6) Extensión '+' (una o más repeticiones) y '?' (cero o una repetición):
   se tratan exactamente igual que '*' para efectos de precedencia: son
   operadores unarios postfijos con precedencia 4, y por tanto NUNCA deben
   producir una concatenación insertada antes de ellos (p. ej. en "a+", no
   se debe insertar "a·+", debe quedar "a" seguido directamente de "+").

LINK AL VIDEO
==============================================================================
https://www.youtube.com/watch?v=suf_g164CGM 
