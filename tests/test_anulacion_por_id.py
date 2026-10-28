import tempfile
import unittest
from pathlib import Path

import pandas as pd

from core.consumos import (
    anular_consumo_por_id,
    obtener_total_consumos,
    obtener_historial_consumos,
)


class TestAnulacionPorId(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        self.archivo = self.carpeta / "consumos_prueba.csv"

        pd.DataFrame([
            {
                "id_consumo": "consumo-001",
                "fecha": "27/10/2026 10:00",
                "habitacion": 101,
                "pasajero": "PASAJERO PRUEBA",
                "categoria": "Bebidas",
                "item": "Agua",
                "cantidad": 1,
                "precio_unitario": 2000,
                "monto": 2000,
                "estado": "vigente",
                "fecha_anulacion": "",
                "motivo_anulacion": "",
            },
            {
                "id_consumo": "consumo-002",
                "fecha": "27/10/2026 10:05",
                "habitacion": 101,
                "pasajero": "PASAJERO PRUEBA",
                "categoria": "Bebidas",
                "item": "Vino",
                "cantidad": 1,
                "precio_unitario": 6500,
                "monto": 6500,
                "estado": "vigente",
                "fecha_anulacion": "",
                "motivo_anulacion": "",
            },
        ]).to_csv(self.archivo, index=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_total_inicial(self):
        total = obtener_total_consumos(
            101, str(self.archivo)
        )["total"]
        self.assertEqual(total, 8500)

    def test_anular_por_id_conserva_registro(self):
        resultado = anular_consumo_por_id(
            101, "consumo-001",
            "Carga duplicada", str(self.archivo)
        )

        self.assertTrue(resultado)

        df = pd.read_csv(self.archivo, keep_default_na=False)
        fila = df.loc[
            df["id_consumo"] == "consumo-001"
        ].iloc[0]

        self.assertEqual(len(df), 2)
        self.assertEqual(fila["estado"], "anulado")
        self.assertEqual(fila["motivo_anulacion"], "Carga duplicada")
        self.assertTrue(fila["fecha_anulacion"])
        self.assertEqual(float(fila["monto"]), 2000)
        self.assertEqual(fila["id_consumo"], "consumo-001")

    def test_total_excluye_consumo_anulado(self):
        anular_consumo_por_id(
            101, "consumo-001",
            "Carga duplicada", str(self.archivo)
        )

        total = obtener_total_consumos(
            101, str(self.archivo)
        )["total"]

        self.assertEqual(total, 6500)

    def test_no_permite_anular_dos_veces(self):
        primera = anular_consumo_por_id(
            101, "consumo-001", "Primer motivo", str(self.archivo)
        )
        segunda = anular_consumo_por_id(
            101, "consumo-001", "Segundo motivo", str(self.archivo)
        )

        self.assertTrue(primera)
        self.assertFalse(segunda)

        df = pd.read_csv(self.archivo, keep_default_na=False)
        fila = df.loc[
            df["id_consumo"] == "consumo-001"
        ].iloc[0]

        self.assertEqual(fila["motivo_anulacion"], "Primer motivo")

    def test_rechaza_habitacion_incorrecta(self):
        resultado = anular_consumo_por_id(
            999, "consumo-002", "Prueba", str(self.archivo)
        )
        self.assertFalse(resultado)

    def test_rechaza_id_inexistente(self):
        resultado = anular_consumo_por_id(
            101, "no-existe", "Prueba", str(self.archivo)
        )
        self.assertFalse(resultado)

    def test_migra_registros_antiguos_y_persiste_ids(self):
        archivo_antiguo = self.carpeta / "consumos_antiguos.csv"

        pd.DataFrame([
            {
                "fecha": "27/10/2026 11:00",
                "habitacion": 102,
                "pasajero": "PASAJERO ANTIGUO",
                "categoria": "Bebidas",
                "item": "Agua",
                "cantidad": 1,
                "precio_unitario": 2000,
                "monto": 2000,
            },
            {
                "fecha": "27/10/2026 11:05",
                "habitacion": 102,
                "pasajero": "PASAJERO ANTIGUO",
                "categoria": "Bebidas",
                "item": "Vino",
                "cantidad": 1,
                "precio_unitario": 6500,
                "monto": 6500,
            },
        ]).to_csv(archivo_antiguo, index=False)

        historial = obtener_historial_consumos(str(archivo_antiguo))
        ids = historial["id_consumo"].astype(str).tolist()

        self.assertTrue(all(ids))
        self.assertEqual(len(set(ids)), 2)

        historial2 = obtener_historial_consumos(str(archivo_antiguo))
        ids2 = historial2["id_consumo"].astype(str).tolist()

        self.assertEqual(ids, ids2)


if __name__ == "__main__":
    unittest.main()