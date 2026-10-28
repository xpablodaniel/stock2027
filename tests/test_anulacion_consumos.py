import os
import tempfile
import unittest

import pandas as pd


from core.consumos import (
    obtener_total_consumos,
    anular_consumo_por_indice,
    agregar_consumo_detallado,
)


class TestAnulacionConsumos(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.archivo = os.path.join(
            self.tmp.name, "consumos_diarios.csv"
        )

        pd.DataFrame([
            {
                "fecha": "23/10/2026 10:00",
                "habitacion": 101,
                "pasajero": "PASAJERO PRUEBA",
                "categoria": "Bebidas",
                "item": "Nampe Malbec",
                "cantidad": 2,
                "precio_unitario": 6500,
                "monto": 13000,
            },
            {
                "fecha": "23/10/2026 10:05",
                "habitacion": 101,
                "pasajero": "PASAJERO PRUEBA",
                "categoria": "Bebidas",
                "item": "Agua sin gas",
                "cantidad": 1,
                "precio_unitario": 2000,
                "monto": 2000,
            },
        ]).to_csv(self.archivo, index=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_anular_conserva_registro_y_resta_del_total(self):
        total_inicial = obtener_total_consumos(
            101, self.archivo
        )["total"]
        self.assertEqual(total_inicial, 15000)

        resultado = anular_consumo_por_indice(
            101,
            0,
            "Carga duplicada",
            self.archivo,
        )
        self.assertTrue(resultado)

        df = pd.read_csv(self.archivo)

        # El registro original permanece completo.
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["item"], "Nampe Malbec")
        self.assertEqual(df.iloc[0]["cantidad"], 2)
        self.assertEqual(df.iloc[0]["precio_unitario"], 6500)
        self.assertEqual(df.iloc[0]["monto"], 13000)

        self.assertEqual(df.iloc[0]["estado"], "anulado")
        self.assertEqual(
            df.iloc[0]["motivo_anulacion"],
            "Carga duplicada",
        )
        self.assertTrue(
            str(df.iloc[0]["fecha_anulacion"]).strip()
        )

        total_final = obtener_total_consumos(
            101, self.archivo
        )["total"]
        self.assertEqual(total_final, 2000)

    def test_csv_antiguo_sin_estado_sigue_siendo_vigente(self):
        df = pd.read_csv(self.archivo)
        df.to_csv(self.archivo, index=False)

        total = obtener_total_consumos(
            101, self.archivo
        )["total"]

        self.assertEqual(total, 15000)

    def test_no_permite_anular_dos_veces_el_mismo_consumo(self):
        primera = anular_consumo_por_indice(
            101, 0, "Error de carga", self.archivo
        )
        segunda = anular_consumo_por_indice(
            101, 0, "Segundo intento", self.archivo
        )

        self.assertTrue(primera)
        self.assertFalse(segunda)

        df = pd.read_csv(self.archivo)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["estado"], "anulado")
        self.assertEqual(
            df.iloc[0]["motivo_anulacion"],
            "Error de carga",
        )

    def test_consumo_nuevo_tiene_identificador_unico_y_estado_vigente(self):
        primero = agregar_consumo_detallado(
            101, "Bebidas", 2000, "PASAJERO PRUEBA",
            item="Agua sin gas",
            cantidad=1,
            precio_unitario=2000,
            archivo_consumos=self.archivo,
        )
        segundo = agregar_consumo_detallado(
            101, "Bebidas", 6500, "PASAJERO PRUEBA",
            item="Nampe Malbec",
            cantidad=1,
            precio_unitario=6500,
            archivo_consumos=self.archivo,
        )

        self.assertTrue(primero)
        self.assertTrue(segundo)

        df = pd.read_csv(self.archivo)

        self.assertIn("id_consumo", df.columns)
        self.assertTrue(df["id_consumo"].notna().all())
        self.assertTrue(df["id_consumo"].is_unique)
        self.assertEqual(df.iloc[-1]["estado"], "vigente")
        self.assertEqual(df.iloc[-2]["estado"], "vigente")

    def test_identificadores_persisten_tras_guardar_y_releer(self):
        df = pd.read_csv(self.archivo)
        df["id_consumo"] = ["consumo-prueba-1", "consumo-prueba-2"]
        df.to_csv(self.archivo, index=False)

        primera_lectura = pd.read_csv(self.archivo)
        ids_originales = primera_lectura["id_consumo"].tolist()

        # Simula volver a abrir el CSV.
        segunda_lectura = pd.read_csv(self.archivo)

        self.assertEqual(
            segunda_lectura["id_consumo"].tolist(),
            ids_originales,
        )

    def test_anulacion_conserva_el_identificador(self):
        df = pd.read_csv(self.archivo)
        df["id_consumo"] = ["consumo-prueba-1", "consumo-prueba-2"]
        df.to_csv(self.archivo, index=False)

        resultado = anular_consumo_por_indice(
            101, 0, "Carga duplicada", self.archivo
        )

        self.assertTrue(resultado)

        df_final = pd.read_csv(self.archivo)

        self.assertEqual(
            df_final.iloc[0]["id_consumo"],
            "consumo-prueba-1",
        )
        self.assertEqual(df_final.iloc[0]["estado"], "anulado")
        self.assertEqual(df_final.iloc[0]["monto"], 13000)


if __name__ == "__main__":
    unittest.main()
