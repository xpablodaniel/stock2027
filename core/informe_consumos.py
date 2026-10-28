
"""Funciones para generar informes consolidados de productos consumidos."""

from pathlib import Path

import pandas as pd


COLUMNAS_REQUERIDAS = {
    "fecha",
    "categoria",
    "item",
    "cantidad",
    "monto",
    "estado",
}


def generar_consolidado_productos(fecha_desde, fecha_hasta, archivo_consumos):
    """
    Consolida productos consumidos dentro de un período, ambas fechas inclusive.

    Las fechas deben recibirse en formato dd/mm/aaaa.

    Devuelve un diccionario con:
        detalle: DataFrame con producto, unidades e importe total.
        total_unidades: suma de las unidades consumidas.
        total_importe: suma de los importes registrados.

    No modifica el CSV de origen.
    """

    desde = pd.to_datetime(
        fecha_desde, format="%d/%m/%Y", errors="raise"
    ).normalize()

    hasta = pd.to_datetime(
        fecha_hasta, format="%d/%m/%Y", errors="raise"
    ).normalize()

    if desde > hasta:
        raise ValueError(
            "La fecha inicial no puede ser posterior a la fecha final."
        )

    ruta = Path(archivo_consumos)

    columnas_salida = ["Producto", "Unidades", "Importe total"]

    if not ruta.exists() or ruta.stat().st_size == 0:
        return {
            "detalle": pd.DataFrame(columns=columnas_salida),
            "total_unidades": 0,
            "total_importe": 0.0,
        }

    df = pd.read_csv(ruta)

    if df.empty:
        return {
            "detalle": pd.DataFrame(columns=columnas_salida),
            "total_unidades": 0,
            "total_importe": 0.0,
        }

    faltantes = COLUMNAS_REQUERIDAS - set(df.columns)

    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el CSV: "
            + ", ".join(sorted(faltantes))
        )


# Interpretar los distintos formatos históricos del CSV.
# Primero probamos el formato argentino con hora.
    fechas_originales = df["fecha"].fillna("").astype(str).str.strip()

    fechas = pd.to_datetime(
        fechas_originales,
        format="%d/%m/%Y %H:%M",
        errors="coerce",
    )

    # Admitir fechas argentinas sin hora.
    pendientes = fechas.isna()
    fechas.loc[pendientes] = pd.to_datetime(
        fechas_originales.loc[pendientes],
        format="%d/%m/%Y",
        errors="coerce",
    )

    # Admitir fechas ISO: AAAA-MM-DD.
    pendientes = fechas.isna()
    fechas.loc[pendientes] = pd.to_datetime(
        fechas_originales.loc[pendientes],
        format="%Y-%m-%d",
        errors="coerce",
    )

    # Admitir también fechas ISO con hora y segundos.
    pendientes = fechas.isna()
    fechas.loc[pendientes] = pd.to_datetime(
        fechas_originales.loc[pendientes],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )


    # Filtrar el período y excluir anulados.
    estado = df["estado"].fillna("vigente").astype(str).str.strip().str.lower()
    categoria = df["categoria"].fillna("").astype(str).str.strip().str.lower()
    producto = df["item"].fillna("").astype(str).str.strip()

    mascara = (
        fechas.notna()
        & (fechas.dt.normalize() >= desde)
        & (fechas.dt.normalize() <= hasta)
        & (estado != "anulado")
        & (~categoria.isin(["estadía", "estadia", "map"]))
        & producto.ne("")
    )

    df = df.loc[mascara].copy()
    df["Producto"] = producto.loc[mascara]

        # Usar las cantidades e importes históricos guardados en cada registro.
    df["Unidades"] = pd.to_numeric(df["cantidad"], errors="coerce")
    df["Importe"] = pd.to_numeric(df["monto"], errors="coerce")

    # No generar resultados engañosos si hay datos inválidos.
    datos_invalidos = (
        df["Unidades"].isna()
        | df["Importe"].isna()
        | (df["Unidades"] <= 0)
        | (df["Importe"] < 0)
    )

    if datos_invalidos.any():
        filas = (df.index[datos_invalidos] + 2).tolist()
        raise ValueError(
            "Hay cantidades o importes inválidos en las filas del CSV: "
            + ", ".join(map(str, filas))
        )

    detalle = (
        df.groupby("Producto", as_index=False)
        .agg(
            Unidades=("Unidades", "sum"),
            **{"Importe total": ("Importe", "sum")},
        )
        .sort_values("Producto")
        .reset_index(drop=True)
    )

    suma_unidades = detalle["Unidades"].sum()

    total_unidades = (
        int(suma_unidades)
        if float(suma_unidades).is_integer()
        else float(suma_unidades)
    )
    total_importe = float(detalle["Importe total"].sum())

    # Presentar unidades enteras cuando todos los valores lo sean.
    if not detalle.empty and (detalle["Unidades"] % 1 == 0).all():
        detalle["Unidades"] = detalle["Unidades"].astype(int)

    return {
        "detalle": detalle,
        "total_unidades": total_unidades,
        "total_importe": total_importe,
    }
