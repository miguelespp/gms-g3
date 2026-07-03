"""
Módulo limpio de ejemplo.

Implementa una pequeña calculadora con funciones bien nombradas,
documentadas y sin lógica compleja anidada.
"""

from __future__ import annotations


def add(a: float, b: float) -> float:
    """Suma dos números."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Resta b de a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiplica dos números."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a entre b. Lanza ValueError si b es cero."""
    if b == 0:
        raise ValueError("División por cero no permitida.")
    return a / b


def factorial(n: int) -> int:
    """Calcula el factorial de n (n >= 0)."""
    if n < 0:
        raise ValueError("El factorial no está definido para negativos.")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def is_prime(n: int) -> bool:
    """Retorna True si n es primo."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
