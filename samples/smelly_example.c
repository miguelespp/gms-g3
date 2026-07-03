/* Ejemplo intencionalmente "sucio" para demostrar el detector de code smells.
 * Contiene: funciones peligrosas, números mágicos, anidamiento profundo,
 * función larga, código comentado, marcadores TODO/FIXME y delimitadores
 * desbalanceados.
 */
#include <stdio.h>
#include <string.h>

// TODO: refactorizar esta función, hace demasiado
// int old_helper(int a) { return a * 2; }   // código viejo comentado
int process(int mode, int value, char *name) {
    char buffer[64];
    strcpy(buffer, name);            // función peligrosa: strcpy
    int result = 0;

    if (mode == 1) {
        if (value > 100) {
            if (value < 9999) {
                for (int i = 0; i < 42; i++) {
                    if (i % 7 == 0) {
                        if (name[i] == 'X') {     // anidamiento profundo (nivel 6+)
                            result += value * 137;  // número mágico
                        }
                    }
                }
            }
        }
    } else if (mode == 2) {
        result = system(name);       // FIXME: nunca pasar entrada del usuario a system()
    } else {
        result = value + 3;
    }

    // Relleno para superar el umbral de "función larga" (>40 líneas).
    result += 1; result += 1; result += 1; result += 1;
    result += 1; result += 1; result += 1; result += 1;
    result += 1; result += 1; result += 1; result += 1;
    result += 1; result += 1; result += 1; result += 1;
    result += 1; result += 1; result += 1; result += 1;
    result += 1; result += 1; result += 1; result += 1;

    return result;
}

// Paréntesis de apertura sin cierre — delimitadores desbalanceados
int broken(int x) {
    return (x + 1;
}
