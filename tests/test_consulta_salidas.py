import json
import unittest
from datetime import date

import pandas as pd

from core.consulta_salidas import generar_consulta_salidas


class TestConsultaSalidas(unittest.TestCase):
    def setUp(self):
        self.pasajeros = pd.DataFrame([
            {
                "id_estadia": "E1", "Nro. habitación": "103",
                "Apellido y nombre": "PAX UNO", "Fecha de ingreso": "14/11/2026",
                "Fecha de egreso": "17/11/2026", "Voucher": "V1",
            },
            {
                "id_estadia": "E2", "Nro. habitación": "103",
                "Apellido y nombre": "PAX DOS", "Fecha de ingreso": "14/11/2026",
                "Fecha de egreso": "17/11/2026", "Voucher": "V1",
            },
            {
                "id_estadia": "ENTRA", "Nro. habitación": "103",
                "Apellido y nombre": "PAX ENTRANTE", "Fecha de ingreso": "17/11/2026",
                "Fecha de egreso": "20/11/2026", "Voucher": "V2",
            },
            {
                "id_estadia": "SIN-CONSUMOS", "Nro. habitación": "104",
                "Apellido y nombre": "PAX TRES", "Fecha de ingreso": "15/11/2026",
                "Fecha de egreso": "17/11/2026", "Voucher": "V3",
            },
        ])
        self.consumos = pd.DataFrame([
            self.consumo("C1", "E1", "Café", "2", "4000"),
            self.consumo("C2", "E2", "Café", "2", "4000"),
            self.consumo("C3", "E2", "Agua", "1", "1500"),
            self.consumo("C4", "E2", "Café", "1", "2000", estado="anulado"),
            self.consumo("C5", "ENTRA", "Café", "5", "10000"),
            self.consumo("C6", "E1", "Comida", "1", "9000", categoria="Comida"),
        ])

    @staticmethod
    def consumo(id_consumo, id_estadia, item, cantidad, monto,
                estado="vigente", categoria="Bebidas"):
        return {
            "id_consumo": id_consumo, "id_estadia": id_estadia,
            "fecha": "16/11/2026 12:00", "habitacion": "103",
            "pasajero": id_estadia, "categoria": categoria, "item": item,
            "cantidad": cantidad, "precio_unitario": monto,
            "monto": monto, "estado": estado,
            "fecha_anulacion": "", "motivo_anulacion": "",
        }

    def test_resumen_por_producto_y_detalle_confirmado(self):
        datos = generar_consulta_salidas(
            self.pasajeros, self.consumos, date(2026, 11, 17)
        )
        self.assertEqual(datos["resumen"]["cuentas"], 2)
        cuenta = datos["cuentas"][0]
        self.assertEqual(cuenta["habitacion"], "103")
        self.assertEqual(cuenta["voucher"], "V1")
        self.assertEqual(cuenta["titular"], "PAX UNO")
        self.assertEqual(cuenta["pasajeros"], ["PAX UNO", "PAX DOS"])
        productos = {p["producto"]: p for p in cuenta["productos"]}
        self.assertEqual(productos["Café"]["cantidad_total"], "4")
        self.assertEqual(productos["Café"]["importe_confirmado"], "8000")
        self.assertEqual(productos["Agua"]["importe_confirmado"], "1500")
        self.assertEqual(cuenta["total_confirmado"], "9500")
        self.assertEqual(len(cuenta["detalle"]), 3)
        self.assertEqual(datos["cuentas"][1]["habitacion"], "104")
        self.assertEqual(datos["cuentas"][1]["productos"], [])
        self.assertEqual(datos["cuentas"][1]["total_confirmado"], "0")

    def test_no_mezcla_estadia_entrante_en_misma_habitacion(self):
        datos = generar_consulta_salidas(
            self.pasajeros, self.consumos, "17/11/2026"
        )
        todos_ids = {
            operacion["id_estadia"]
            for cuenta in datos["cuentas"]
            for operacion in cuenta["detalle"]
        }
        self.assertNotIn("ENTRA", todos_ids)
        self.assertEqual(datos["resumen"]["total_confirmado"], "9500")

    def test_json_serializable_y_cantidades_invalidas_visibles(self):
        consumos = self.consumos.copy()
        consumos.loc[0, "cantidad"] = "s/d"
        datos = generar_consulta_salidas(
            self.pasajeros, consumos, date(2026, 11, 17)
        )
        json.dumps(datos, ensure_ascii=False)
        cafe = next(p for p in datos["cuentas"][0]["productos"] if p["producto"] == "Café")
        self.assertIsNone(cafe["cantidad_total"])
        self.assertTrue(cafe["cantidades_incompletas"])


if __name__ == "__main__":
    unittest.main()
