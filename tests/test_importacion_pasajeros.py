
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import app as aplicacion


def pasajero(nombre, habitacion, ingreso, egreso, id_estadia=""):
    return {
        "Nro. habitación": str(habitacion),
        "Fecha de ingreso": ingreso.strftime("%d/%m/%Y"),
        "Fecha de egreso": egreso.strftime("%d/%m/%Y"),
        "Apellido y nombre": nombre,
        "Servicios": "DESAYUNO",
        "Voucher": f"TEST-{habitacion}",
        "Estado": "Activo",
        "id_estadia": id_estadia,
    }


def csv_subida(filas, incluir_id=True):
    df = pd.DataFrame(filas)

    if not incluir_id and "id_estadia" in df.columns:
        df = df.drop(columns=["id_estadia"])

    return io.BytesIO(df.to_csv(index=False).encode("utf-8"))


class TestImportacionPasajeros(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.csv_real = str(Path(self.tmp.name) / "pasajeros.csv")

        hoy = date.today()

        # Padrón sintético inicial.
        pd.DataFrame([
            pasajero(
                "HUESPED A",
                101,
                hoy,
                hoy + timedelta(days=3),
                "ESTADIA-A",
            ),
            pasajero(
                "HUESPED B",
                102,
                hoy,
                hoy + timedelta(days=5),
                "ESTADIA-B",
            ),
        ]).to_csv(self.csv_real, index=False)

        self.cliente = aplicacion.app.test_client()

        self.patch_db = patch.object(
            aplicacion,
            "DB_PASAJEROS",
            self.csv_real,
        )
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)

        # Evita copiar el CSV temporal al directorio real de backups.
        self.patch_backup = patch("shutil.copy")
        self.patch_backup.start()
        self.addCleanup(self.patch_backup.stop)

    def subir(self, filas, modo="agregar", incluir_id=True):
        archivo = csv_subida(filas, incluir_id)

        return self.cliente.post(
            "/subir-pasajeros",
            data={
                "archivo": (archivo, "prueba.csv"),
                "modo_carga": modo,
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

    def leer(self):
        return pd.read_csv(
            self.csv_real,
            dtype={"Nro. habitación": str, "id_estadia": str},
        )

    def test_agregar_habitacion_nueva_conserva_las_anteriores(self):
        hoy = date.today()

        respuesta = self.subir([
            pasajero(
                "HUESPED C",
                103,
                hoy,
                hoy + timedelta(days=3),
                "ESTADIA-C",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer()
        nombres = set(df["Apellido y nombre"])

        self.assertEqual(
            nombres,
            {"HUESPED A", "HUESPED B", "HUESPED C"},
        )

        ids = df.set_index("Apellido y nombre")["id_estadia"]
        self.assertEqual(ids["HUESPED A"], "ESTADIA-A")
        self.assertEqual(ids["HUESPED B"], "ESTADIA-B")
        self.assertEqual(ids["HUESPED C"], "ESTADIA-C")

    def test_agregar_misma_habitacion_reemplaza_registro_anterior(self):
        hoy = date.today()

        respuesta = self.subir([
            pasajero(
                "NUEVO HUESPED 101",
                101,
                hoy + timedelta(days=10),
                hoy + timedelta(days=13),
                "ESTADIA-NUEVA",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer()
        hab101 = df[df["Nro. habitación"] == "101"]

        # Documenta el comportamiento actual: reemplaza por habitación,
        # aunque las fechas de la reserva sean distintas.
        self.assertEqual(len(hab101), 1)
        self.assertEqual(
            hab101.iloc[0]["Apellido y nombre"],
            "NUEVO HUESPED 101",
        )

        # La otra habitación permanece.
        self.assertIn("HUESPED B", df["Apellido y nombre"].tolist())

    def test_csv_sin_id_estadia_deja_id_vacio_en_nuevo_registro(self):
        hoy = date.today()

        respuesta = self.subir(
            [
                {
                    "Nro. habitación": "103",
                    "Fecha de ingreso": hoy.strftime("%d/%m/%Y"),
                    "Fecha de egreso": (
                        hoy + timedelta(days=2)
                    ).strftime("%d/%m/%Y"),
                    "Apellido y nombre": "HUESPED SIN ID",
                    "Servicios": "DESAYUNO",
                }
            ],
            incluir_id=False,
        )

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer()
        nuevo = df[df["Apellido y nombre"] == "HUESPED SIN ID"]

        self.assertEqual(len(nuevo), 1)
        self.assertTrue(pd.isna(nuevo.iloc[0]["id_estadia"]))

    def test_reemplazar_deja_solo_las_filas_del_nuevo_csv(self):
        hoy = date.today()

        respuesta = self.subir(
            [
                pasajero(
                    "SOLO NUEVO",
                    104,
                    hoy,
                    hoy + timedelta(days=2),
                    "ESTADIA-104",
                )
            ],
            modo="reemplazar",
        )

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer()
        self.assertEqual(len(df), 1)
        self.assertEqual(
            df.iloc[0]["Apellido y nombre"],
            "SOLO NUEVO",
        )

    def test_csv_sin_columna_requerida_no_reemplaza_el_padron(self):
        antes = Path(self.csv_real).read_bytes()

        archivo = io.BytesIO(
            b"Nro. habitacion,Apellido y nombre\n"
            b"105,HUESPED INVALIDO\n"
        )

        respuesta = self.cliente.post(
            "/subir-pasajeros",
            data={
                "archivo": (archivo, "invalido.csv"),
                "modo_carga": "reemplazar",
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Path(self.csv_real).read_bytes(), antes)


if __name__ == "__main__":
    unittest.main()
