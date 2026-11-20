#!/usr/bin/env python3
"""Genera desde la CLI el JSON de consulta de consumos de las salidas."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pase_caja import COLUMNAS_PASAJEROS, COLUMNAS_CONSUMOS
from core.consulta_salidas import generar_consulta_salidas


def main():
    hoy = datetime.now().date()
    parser = argparse.ArgumentParser(
        description="Genera un resumen JSON de consumos confirmados para las salidas."
    )
    parser.add_argument(
        "--fecha", default=hoy.strftime("%d/%m/%Y"),
        help="Fecha de egreso en formato DD/MM/AAAA (por defecto: hoy)."
    )
    parser.add_argument("--pasajeros", type=Path, default=ROOT / "data/pasajeros.csv")
    parser.add_argument("--consumos", type=Path, default=ROOT / "data/consumos_diarios.csv")
    parser.add_argument(
        "--salida", type=Path,
        default=ROOT / "data/consultas_salidas" / f"consulta_salidas_{hoy:%Y%m%d}.json",
        help="Ruta del JSON de destino."
    )
    args = parser.parse_args()

    try:
        fecha = datetime.strptime(args.fecha, "%d/%m/%Y").date()
    except ValueError:
        parser.error("--fecha debe tener el formato DD/MM/AAAA")

    for archivo in (args.pasajeros, args.consumos):
        if not archivo.is_file():
            parser.error(f"No se encuentra el archivo requerido: {archivo}")

    try:
        pasajeros = pd.read_csv(args.pasajeros, dtype=str, keep_default_na=False, encoding="utf-8")
        consumos = pd.read_csv(args.consumos, dtype=str, keep_default_na=False, encoding="utf-8")
        for nombre, tabla, requeridas in (
            ("pasajeros", pasajeros, COLUMNAS_PASAJEROS),
            ("consumos", consumos, COLUMNAS_CONSUMOS),
        ):
            faltantes = set(requeridas) - set(tabla.columns)
            if faltantes:
                parser.error(
                    f"Faltan columnas en {nombre}: {', '.join(sorted(faltantes))}"
                )

        datos = generar_consulta_salidas(pasajeros, consumos, fecha)
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as error:
        parser.error(f"No se pudo generar la consulta: {error}")

    print(f"Consulta generada: {args.salida}")
    print(f"Fecha de salida: {datos['fecha_salida']}")
    print(f"Cuentas: {datos['resumen']['cuentas']}")
    print(f"Habitaciones: {datos['resumen']['habitaciones']}")
    print(f"Pasajeros: {datos['resumen']['pasajeros']}")
    print(f"Total confirmado: $ {datos['resumen']['total_confirmado']}")
    print(f"Observaciones: {sum(datos['observaciones'].values())}")


if __name__ == "__main__":
    main()
