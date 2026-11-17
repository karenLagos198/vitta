"""Validaciones básicas de los datos que llegan desde el frontend."""
import math
import re
from datetime import date

PRIORIDADES = ("Alta", "Media", "Baja")
TIPOS = ("gasto", "ingreso")
CATEGORIAS = ("Comida", "Transporte", "Ocio", "Servicios", "Otros")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def texto(valor, campo, minimo=1, maximo=120):
    valor = (valor or "").strip() if isinstance(valor, str) else ""
    if len(valor) < minimo:
        raise ValueError(f"{campo} es obligatorio")
    if len(valor) > maximo:
        raise ValueError(f"{campo} no puede superar {maximo} caracteres")
    return valor


def fecha(valor, campo="La fecha", obligatoria=False):
    if not valor:
        if obligatoria:
            raise ValueError(f"{campo} es obligatoria")
        return None
    try:
        return date.fromisoformat(valor).isoformat()
    except (ValueError, TypeError):
        raise ValueError(f"{campo} no es válida (formato AAAA-MM-DD)")


def monto(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError("El monto debe ser un número")
    if math.isnan(numero) or numero <= 0 or numero > 1e12:
        raise ValueError("El monto debe ser mayor que 0")
    return round(numero, 2)


def opcion(valor, permitidos, campo):
    if valor not in permitidos:
        raise ValueError(f"{campo} no es válido")
    return valor


def email(valor):
    valor = texto(valor, "El correo", 3, 120).lower()
    if not EMAIL_RE.match(valor):
        raise ValueError("El correo no es válido")
    return valor


def clave(valor):
    if not isinstance(valor, str) or len(valor) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres")
    return valor
