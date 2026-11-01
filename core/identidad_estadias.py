
"""
Gestión de identidad de estadías.

Asigna y conserva un UUID por pasajero y estadía.
No modifica archivos: procesa DataFrames en memoria.
"""

import re
import uuid
import unicodedata
from datetime import datetime

import pandas as pd


COLUMNA_ID = "id_estadia"

COLUMNAS_IDENTIDAD = [
    "Nro. doc.",
    "Apellido y nombre",
    "Voucher",
    "Fecha de ingreso",
    "Fecha de egreso",
]


def _normalizar_texto(valor):
    """Normaliza texto para comparar datos de pasajeros."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = re.sub(r"\s+", " ", texto)

    return texto


def _normalizar_documento(valor):
    """Devuelve DNI normalizado; descarta valores ficticios."""
    texto = _normalizar_texto(valor)

    if not texto:
        return ""

    digitos = re.sub(r"\D", "", texto)

    if not digitos or set(digitos) == {"0"}:
        return ""

    return digitos


def _normalizar_fecha(valor):
    """Normaliza fechas a AAAA-MM-DD."""
    if pd.isna(valor) or not str(valor).strip():
        return ""

    texto = str(valor).strip()

    for formato in (
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(texto, formato).strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            continue

    return ""



def _clave_identidad(fila):
    """
    Construye una clave conservadora.

    Prioridad:
    1. DNI + nombre + ingreso + egreso.
    2. Voucher + nombre + ingreso + egreso.

    La habitación no forma parte de la identidad.
    """
    ingreso = _normalizar_fecha(
        fila.get("Fecha de ingreso")
    )
    egreso = _normalizar_fecha(
        fila.get("Fecha de egreso")
    )

    if not ingreso or not egreso:
        return None

    # El nombre se normaliza antes de evaluar el DNI.
    nombre = _normalizar_texto(
        fila.get("Apellido y nombre")
    )

    if not nombre:
        return None

    documento = _normalizar_documento(
        fila.get("Nro. doc.")
    )

    if documento:
        return (
            "DNI",
            documento,
            nombre,
            ingreso,
            egreso
        )

    voucher = _normalizar_texto(
        fila.get("Voucher")
    )

    if voucher:
        return (
            "VOUCHER",
            voucher,
            nombre,
            ingreso,
            egreso
        )

    return None



def _generar_id():
    """Genera UUID hexadecimal independiente."""
    return uuid.uuid4().hex


def _preparar_dataframe(df):
    """Copia el DataFrame y asegura la columna id_estadia."""
    resultado = df.copy()

    if COLUMNA_ID not in resultado.columns:
        resultado[COLUMNA_ID] = ""

    resultado[COLUMNA_ID] = (
        resultado[COLUMNA_ID]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return resultado



def _indice_coincidencias(df):
    """
    Indexa filas existentes por clave de identidad.

    Incluye registros con y sin id_estadia.
    La asignación del UUID se resuelve al procesar
    cada coincidencia.
    """
    indice = {}

    for idx, fila in df.iterrows():
        clave = _clave_identidad(fila)

        if clave is None:
            continue

        identificador = fila[COLUMNA_ID]

        indice.setdefault(clave, []).append(
            (idx, identificador)
        )

    return indice



def procesar_identidades(
    df_existente,
    df_nuevo,
    modo="agregar",
):
    """
    Procesa un CSV nuevo y conserva UUID reconocibles.

    modo:
        agregar:
            Conserva registros anteriores no reemplazados.
            Actualiza estadías reconocidas.
            Incorpora nuevas estadías.

        reemplazar:
            Utiliza únicamente las filas del CSV nuevo,
            recuperando UUID cuando hay coincidencias únicas.

    Retorna:
        (DataFrame, resumen)
    """
    if modo not in ("agregar", "reemplazar"):
        raise ValueError("Modo de importación inválido.")

    existente = _preparar_dataframe(df_existente)
    nuevo = _preparar_dataframe(df_nuevo)

    for columna in COLUMNAS_IDENTIDAD:
        if columna not in nuevo.columns:
            raise ValueError(
                f"Falta columna para identificar estadías: {columna}"
            )

    if not existente.empty:
        for columna in COLUMNAS_IDENTIDAD:
            if columna not in existente.columns:
                existente[columna] = ""

    indice = _indice_coincidencias(existente)

    usados = set()
    filas_nuevas = []

    resumen = {
        "coincidencias": 0,
        "nuevas_estadias": 0,
        "coincidencias_ambiguas": 0,
    }

    for _, fila in nuevo.iterrows():
        registro = fila.to_dict()
        clave = _clave_identidad(fila)

        coincidencias = (
            indice.get(clave, [])
            if clave is not None
            else []
        )

        disponibles = [
            (idx, identificador)
            for idx, identificador in coincidencias
            if idx not in usados
        ]

        
        if len(disponibles) == 1:
            idx_existente, identificador = disponibles[0]

            # Si la estadía antigua no tenía UUID,
            # generamos uno nuevo para esta identidad reconocida.
            if not identificador:
                identificador = _generar_id()

            registro[COLUMNA_ID] = identificador
            usados.add(idx_existente)
            resumen["coincidencias"] += 1


        else:
            if len(disponibles) > 1:
                resumen["coincidencias_ambiguas"] += 1

            registro[COLUMNA_ID] = _generar_id()
            resumen["nuevas_estadias"] += 1

        filas_nuevas.append(registro)

    df_procesado = pd.DataFrame(filas_nuevas)

    if modo == "reemplazar":
        resultado = df_procesado

    else:
        # Se conservan las filas anteriores que no fueron
        # reconocidas ni actualizadas por el CSV nuevo.
        conservar = existente.loc[
            ~existente.index.isin(usados)
        ].copy()

        # Completar UUID faltantes de registros anteriores.
        for idx in conservar.index:
            if not conservar.at[idx, COLUMNA_ID]:
                conservar.at[idx, COLUMNA_ID] = _generar_id()

        # Unificar columnas sin perder información.
        columnas = list(dict.fromkeys(
            list(existente.columns)
            + list(df_procesado.columns)
        ))

        conservar = conservar.reindex(columns=columnas)
        df_procesado = df_procesado.reindex(columns=columnas)

        resultado = pd.concat(
            [conservar, df_procesado],
            ignore_index=True,
        )

    return resultado, resumen
