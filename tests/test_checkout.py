import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import app as aplicacion


class TestCheckoutConservaConsumos(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.pasajeros = str(Path(self.tmp.name) / "pasajeros.csv")
        self.consumos = str(Path(self.tmp.name) / "consumos.csv")

        pd.DataFrame([
            {
                "Nro. habitación": "101",
                "Fecha de ingreso": "01/01/2020",
                "Fecha de egreso": "01/01/2020",
                "Apellido y nombre": "PASAJERO PRUEBA",
                "Servicios": "MAP",
                "Edad": 70,
                "Voucher": "TEST-1",
            },
            {
                "Nro. habitación": "102",
                "Fecha de ingreso": "01/01/2099",
                "Fecha de egreso": "01/01/2099",
                "Apellido y nombre": "OTRO PASAJERO",
                "Servicios": "MAP",
                "Edad": 65,
                "Voucher": "TEST-2",
            },
        ]).to_csv(self.pasajeros, index=False)

        pd.DataFrame([
            {
                "fecha": "01/01/2020 12:00",
                "habitacion": 101,
                "pasajero": "PASAJERO PRUEBA",
                "categoria": "Bebidas",
                "item": "Nampe Malbec",
                "cantidad": 2,
                "precio_unitario": 6500,
                "monto": 13000,
            },
            {
                "fecha": "01/01/2020 13:00",
                "habitacion": 102,
                "pasajero": "OTRO PASAJERO",
                "categoria": "Bebidas",
                "item": "Agua",
                "cantidad": 1,
                "precio_unitario": 2000,
                "monto": 2000,
            },
        ]).to_csv(self.consumos, index=False)

        self.cliente = aplicacion.app.test_client()

        self.patch_pasajeros = patch.object(
            aplicacion, "DB_PASAJEROS", self.pasajeros
        )
        self.patch_consumos = patch.object(
            aplicacion, "DB_CONSUMOS", self.consumos
        )
        self.patch_pasajeros.start()
        self.patch_consumos.start()
        self.addCleanup(self.patch_pasajeros.stop)
        self.addCleanup(self.patch_consumos.stop)

    def test_checkout_individual_conserva_todos_los_consumos(self):
        with patch.object(
            aplicacion,
            "obtener_habitaciones_ocupadas",
            return_value={101: {"pasajero": "PASAJERO PRUEBA"}},
        ):
            respuesta = self.cliente.post(
                "/checkout/101/confirmar",
                follow_redirects=False,
            )

        self.assertEqual(respuesta.status_code, 302)

        consumos = pd.read_csv(self.consumos)
        self.assertEqual(len(consumos), 2)
        self.assertEqual(consumos["monto"].tolist(), [13000, 2000])

        pasajeros = pd.read_csv(self.pasajeros)
        self.assertNotIn(101, pasajeros["Nro. habitación"].astype(str).tolist())
        self.assertIn("OTRO PASAJERO", pasajeros["Apellido y nombre"].tolist())

    def test_checkout_masivo_conserva_todos_los_consumos(self):
        with patch("core.dashboard.obtener_habitaciones_checkout_pendientes",
                   return_value={101: {}}):
            respuesta = self.cliente.post(
                "/checkout-masivo/confirmar",
                follow_redirects=False,
            )

        self.assertEqual(respuesta.status_code, 302)

        consumos = pd.read_csv(self.consumos)
        self.assertEqual(len(consumos), 2)
        self.assertEqual(consumos["monto"].tolist(), [13000, 2000])

        pasajeros = pd.read_csv(self.pasajeros)
        self.assertNotIn("PASAJERO PRUEBA", pasajeros["Apellido y nombre"].tolist())
        self.assertIn("OTRO PASAJERO", pasajeros["Apellido y nombre"].tolist())


if __name__ == "__main__":
    unittest.main()
