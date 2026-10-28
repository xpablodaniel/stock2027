
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from core import reserva_express


class TestReservaExpress(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.csv_pasajeros = str(
            Path(self.tmp.name) / "pasajeros.csv"
        )

        # Registro histórico de prueba, sin la columna id_estadia.
        pd.DataFrame([
            {
                "Nro. habitación": "999",
                "Fecha de ingreso": "01/01/2020",
                "Fecha de egreso": "02/01/2020",
                "Apellido y nombre": "PASAJERO HISTORICO",
                "Voucher": "TEST-HISTORICO",
            }
        ]).to_csv(self.csv_pasajeros, index=False)

        self.patch_db = patch.object(
            reserva_express,
            "DB_PASAJEROS",
            self.csv_pasajeros,
        )
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)

    def test_crea_reserva_y_persiste_id_estadia(self):
        reserva, mensaje = reserva_express.crear_reserva_express(
            habitacion=101,
            nombre="HUESPED DE PRUEBA",
            pax=2,
            noches=2,
        )

        self.assertIsNotNone(reserva, mensaje)
        self.assertEqual(
            mensaje,
            "Reserva express creada exitosamente",
        )
        self.assertTrue(reserva["id_estadia"])
        self.assertEqual(len(reserva["id_estadia"]), 32)

        guardados = pd.read_csv(
            self.csv_pasajeros,
            dtype={"id_estadia": "object"},
        )

        self.assertEqual(len(guardados), 2)
        self.assertIn("id_estadia", guardados.columns)

        nueva = guardados[
            guardados["Apellido y nombre"] == "HUESPED DE PRUEBA"
        ].iloc[0]

        self.assertEqual(
            nueva["id_estadia"],
            reserva["id_estadia"],
        )
        self.assertEqual(
            nueva["Fecha de egreso"],
            (
                reserva_express.date.today()
                + reserva_express.timedelta(days=2)
            ).strftime("%d/%m/%Y"),
        )

        historico = guardados[
            guardados["Apellido y nombre"] == "PASAJERO HISTORICO"
        ].iloc[0]

        self.assertEqual(
            historico["Voucher"],
            "TEST-HISTORICO",
        )
        self.assertTrue(pd.isna(historico["id_estadia"]))


    def test_rechaza_habitacion_con_estadia_superpuesta(self):
        hoy = reserva_express.date.today()

        pd.DataFrame([
            {
                "Nro. habitación": "101",
                "Fecha de ingreso": hoy.strftime("%d/%m/%Y"),
                "Fecha de egreso": (
                    hoy + reserva_express.timedelta(days=3)
                ).strftime("%d/%m/%Y"),
                "Apellido y nombre": "HUESPED EXISTENTE",
                "Voucher": "TEST-OCUPADA",
            }
        ]).to_csv(self.csv_pasajeros, index=False)

        contenido_anterior = Path(self.csv_pasajeros).read_bytes()

        reserva, mensaje = reserva_express.crear_reserva_express(
            habitacion=101,
            nombre="SEGUNDO HUESPED",
            pax=1,
            noches=1,
        )

        self.assertIsNone(reserva)
        self.assertIn("ocupada", mensaje.lower())
        self.assertEqual(
            Path(self.csv_pasajeros).read_bytes(),
            contenido_anterior,
        )

    def test_permite_ingreso_el_dia_del_egreso_anterior(self):
        hoy = reserva_express.date.today()

        pd.DataFrame([
            {
                "Nro. habitación": "101",
                "Fecha de ingreso": (
                    hoy - reserva_express.timedelta(days=2)
                ).strftime("%d/%m/%Y"),
                "Fecha de egreso": hoy.strftime("%d/%m/%Y"),
                "Apellido y nombre": "HUESPED QUE EGRESA HOY",
                "Voucher": "TEST-EGRESO",
            }
        ]).to_csv(self.csv_pasajeros, index=False)

        reserva, mensaje = reserva_express.crear_reserva_express(
            habitacion=101,
            nombre="NUEVO HUESPED",
            pax=1,
            noches=2,
        )

        self.assertIsNotNone(reserva, mensaje)
        self.assertEqual(
            mensaje,
            "Reserva express creada exitosamente",
        )

        guardados = pd.read_csv(self.csv_pasajeros)
        self.assertEqual(len(guardados), 2)

    def test_bloquea_habitacion_con_fechas_historicas_invalidas(self):
        pd.DataFrame([
            {
                "Nro. habitación": "101",
                "Fecha de ingreso": "",
                "Fecha de egreso": "",
                "Apellido y nombre": "REGISTRO HISTORICO INCOMPLETO",
                "Voucher": "TEST-FECHAS-INVALIDAS",
            }
        ]).to_csv(self.csv_pasajeros, index=False)

        contenido_anterior = Path(self.csv_pasajeros).read_bytes()

        reserva, mensaje = reserva_express.crear_reserva_express(
            habitacion=101,
            nombre="NUEVO HUESPED",
            pax=1,
            noches=1,
        )

        self.assertIsNone(reserva)
        self.assertIn("fechas faltantes o inválidas", mensaje.lower())
        self.assertEqual(
            Path(self.csv_pasajeros).read_bytes(),
            contenido_anterior,
        )

if __name__ == "__main__":
    unittest.main()
