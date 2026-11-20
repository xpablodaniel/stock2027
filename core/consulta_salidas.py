"""Preparación de una consulta compacta de consumos para las salidas del día.

La atribución y validación de consumos se delega en core.pase_caja para
mantener exactamente las reglas del pase de turno.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from core.pase_caja import (
    obtener_pasajeros_con_salida,
    vincular_consumos_bebidas,
    clave_cuenta,
)


def _decimal_seguro(valor):
    """Convierte un valor a Decimal finito; devuelve None si no es válido."""
    try:
        numero = Decimal(str(valor).strip())
        return numero if numero.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def _texto_decimal(valor):
    """Serializa importes como texto para no perder precisión monetaria."""
    texto = format(valor, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _orden_habitacion(valor):
    try:
        return (0, int(str(valor)))
    except (TypeError, ValueError):
        return (1, str(valor))


def generar_consulta_salidas(df_pasajeros, df_consumos, fecha_referencia=None):
    """Devuelve datos JSON-serializables para las cuentas que egresan ese día.

    Se incluyen todas las cuentas de salida, incluso si no tienen consumos.
    El resumen por producto considera únicamente operaciones confirmadas por
    vincular_consumos_bebidas. Se conserva el detalle de esas operaciones.
    """
    if fecha_referencia is None:
        fecha_referencia = date.today()
    elif isinstance(fecha_referencia, str):
        fecha_referencia = datetime.strptime(fecha_referencia, "%d/%m/%Y").date()
    elif isinstance(fecha_referencia, datetime):
        fecha_referencia = fecha_referencia.date()

    salidas = obtener_pasajeros_con_salida(df_pasajeros, fecha_referencia)
    validacion = vincular_consumos_bebidas(salidas, df_consumos)

    cuentas = {}
    for _, estadia in salidas.iterrows():
        habitacion, voucher = clave_cuenta(estadia)
        clave = (habitacion, voucher)
        cuenta = cuentas.setdefault(clave, {
            "habitacion": habitacion,
            "voucher": voucher,
            "titular": str(estadia.get("Apellido y nombre", "")).strip(),
            "pasajeros": [],
            "ids_estadia": [],
            "productos": {},
            "detalle": [],
            "_total": Decimal("0"),
        })
        nombre = str(estadia.get("Apellido y nombre", "")).strip()
        if nombre and nombre not in cuenta["pasajeros"]:
            cuenta["pasajeros"].append(nombre)
        id_estadia = str(estadia.get("id_estadia", "")).strip()
        if id_estadia:
            cuenta["ids_estadia"].append(id_estadia)

    detalle = validacion["detalle_confirmado"]
    if not detalle.empty:
        for registro in detalle.to_dict("records"):
            clave = (
                str(registro.get("habitacion", "")).strip(),
                "",
            )
            # El voucher se resuelve desde el padrón por id_estadia, nunca
            # solamente por habitación (puede haber dos cuentas en un cuarto).
            coincidencias = salidas.loc[
                salidas["id_estadia"].astype(str).str.strip()
                == str(registro.get("id_estadia", "")).strip()
            ]
            if coincidencias.empty:
                continue
            estadia = coincidencias.iloc[0]
            clave = clave_cuenta(estadia)
            cuenta = cuentas.get(clave)
            if cuenta is None:
                continue

            producto = str(registro.get("item", "")).strip() or "Sin producto"
            importe = registro.get("monto_confirmado", Decimal("0"))
            if not isinstance(importe, Decimal):
                importe = Decimal(str(importe))

            resumen = cuenta["productos"].setdefault(producto, {
                "_cantidad": Decimal("0"),
                "_cantidad_valida": True,
                "_importe": Decimal("0"),
                "operaciones": 0,
            })
            cantidad = _decimal_seguro(registro.get("cantidad", ""))
            if cantidad is None:
                resumen["_cantidad_valida"] = False
            else:
                resumen["_cantidad"] += cantidad
            resumen["_importe"] += importe
            resumen["operaciones"] += 1
            cuenta["_total"] += importe

            cuenta["detalle"].append({
                "id_consumo": str(registro.get("id_consumo", "")),
                "id_estadia": str(registro.get("id_estadia", "")),
                "pasajero": str(registro.get("pasajero", "")),
                "fecha": str(registro.get("fecha", "")),
                "producto": producto,
                "cantidad": str(registro.get("cantidad", "")),
                "precio_unitario": str(registro.get("precio_unitario", "")),
                "importe_confirmado": _texto_decimal(importe),
            })

    resultado_cuentas = []
    for cuenta in sorted(cuentas.values(), key=lambda c: _orden_habitacion(c["habitacion"])):
        productos = []
        for nombre, resumen in sorted(cuenta["productos"].items(), key=lambda par: par[0].casefold()):
            productos.append({
                "producto": nombre,
                "cantidad_total": (
                    _texto_decimal(resumen["_cantidad"])
                    if resumen["_cantidad_valida"] else None
                ),
                "cantidades_incompletas": not resumen["_cantidad_valida"],
                "operaciones": resumen["operaciones"],
                "importe_confirmado": _texto_decimal(resumen["_importe"]),
            })
        cuenta["productos"] = productos
        cuenta["total_confirmado"] = _texto_decimal(cuenta.pop("_total"))
        cuenta["detalle"].sort(key=lambda op: (op["fecha"], op["pasajero"], op["producto"]))
        resultado_cuentas.append(cuenta)

    fecha_texto = fecha_referencia.strftime("%d/%m/%Y")
    return {
        "fecha_salida": fecha_texto,
        "generado_en": datetime.now().astimezone().isoformat(timespec="seconds"),
        "criterio": "Consumos de bebidas vigentes, vinculados y validados por id_estadia",
        "resumen": {
            "cuentas": len(resultado_cuentas),
            "habitaciones": len({c["habitacion"] for c in resultado_cuentas}),
            "pasajeros": sum(len(c["pasajeros"]) for c in resultado_cuentas),
            "total_confirmado": _texto_decimal(
                sum((Decimal(c["total_confirmado"]) for c in resultado_cuentas), Decimal("0"))
            ),
        },
        "observaciones": {
            "consumos_sin_id": len(validacion["pendientes"]),
            "consumos_inconsistentes": len(validacion["inconsistencias"]),
            "estadias_duplicadas": len(validacion["estadias_duplicadas"]),
        },
        "cuentas": resultado_cuentas,
    }
