
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from core.informe_consumos import generar_consolidado_productos


class TestInformeConsumos(unittest.TestCase):

    def test_consolida_productos_y_excluye_anulados(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "consumos_prueba.csv"

            datos = [
                {
                    "fecha": "10/11/2026 10:00",
                    "categoria": "Bebidas",
                    "item": "Coca-Cola",
                    "cantidad": 2,
                    "monto": 6000,
                    "estado": "vigente",
                },
                {
                    "fecha": "11/11/2026 12:00",
                    "categoria": "Bebidas",
                    "item": "Coca-Cola",
                    "cantidad": 1,
                    "monto": 3000,
                    "estado": "vigente",
                },
                {
                    "fecha": "12/11/2026 13:00",
                    "categoria": "Bebidas",
                    "item": "Coca-Cola",
                    "cantidad": 5,
                    "monto": 15000,
                    "estado": "anulado",
                },
                {
                    "fecha": "11/11/2026 14:00",
                    "categoria": "Bebidas",
                    "item": "Ficha de Café",
                    "cantidad": 2,
                    "monto": 6000,
                    "estado": "vigente",
                },
                {
                    "fecha": "11/11/2026 15:00",
                    "categoria": "Estadía",
                    "item": "Estadía",
                    "cantidad": 1,
                    "monto": 50000,
                    "estado": "vigente",
                },
                {
                    "fecha": "20/11/2026 15:00",
                    "categoria": "Bebidas",
                    "item": "Agua sin gas",
                    "cantidad": 1,
                    "monto": 2000,
                    "estado": "vigente",
                },
            ]

            pd.DataFrame(datos).to_csv(archivo, index=False)

            resultado = generar_consolidado_productos(
                "10/11/2026",
                "12/11/2026",
                archivo,
            )

            detalle = resultado["detalle"].set_index("Producto")

            self.assertEqual(detalle.loc["Coca-Cola", "Unidades"], 3)
            self.assertEqual(
                detalle.loc["Coca-Cola", "Importe total"], 9000
            )
            self.assertEqual(
                detalle.loc["Ficha de Café", "Unidades"], 2
            )
            self.assertNotIn("Estadía", detalle.index)
            self.assertNotIn("Agua sin gas", detalle.index)

            self.assertEqual(resultado["total_unidades"], 5)
            self.assertEqual(resultado["total_importe"], 15000)

    def test_rechaza_rango_invertido(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "consumos_prueba.csv"

            with self.assertRaises(ValueError):
                generar_consolidado_productos(
                    "12/11/2026",
                    "10/11/2026",
                    archivo,
                )


if __name__ == "__main__":
    unittest.main()
