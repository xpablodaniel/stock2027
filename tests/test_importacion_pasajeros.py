
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import app as aplicacion


def pasajero(nombre, habitacion, ingreso, egreso, dni, id_estadia=""):
    return {
        "Nro. habitación": str(habitacion),
        "Fecha de ingreso": ingreso.strftime("%d/%m/%Y"),
        "Fecha de egreso": egreso.strftime("%d/%m/%Y"),
        "Apellido y nombre": nombre,
        "Nro. doc.": dni,
        "Voucher": f"TEST-{dni}",
        "Servicios": "DESAYUNO",
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

        self.directorio = Path(self.tmp.name)
        self.csv_pasajeros = self.directorio / "pasajeros.csv"
        self.csv_consumos = self.directorio / "consumos_diarios.csv"

        hoy = date.today()

        self.fecha_ingreso = hoy
        self.fecha_egreso = hoy + timedelta(days=3)

        # Padrón inicial ficticio.
        self.df_inicial = pd.DataFrame([
            pasajero(
                "HUESPED A",
                101,
                self.fecha_ingreso,
                self.fecha_egreso,
                "11111111",
                "ESTADIA-A",
            ),
            pasajero(
                "HUESPED B",
                102,
                self.fecha_ingreso,
                hoy + timedelta(days=5),
                "22222222",
                "ESTADIA-B",
            ),
        ])

        self.df_inicial.to_csv(
            self.csv_pasajeros,
            index=False,
        )

        # Archivo ficticio de consumos: debe permanecer intacto.
        self.contenido_consumos = (
            "id_consumo,id_estadia,habitacion,importe\n"
            "C001,ESTADIA-A,101,1500\n"
        )

        self.csv_consumos.write_text(
            self.contenido_consumos,
            encoding="utf-8",
        )

        self.cliente = aplicacion.app.test_client()

        # Redirigimos los archivos de la aplicación al directorio temporal.
        self.patch_pasajeros = patch.object(
            aplicacion,
            "DB_PASAJEROS",
            str(self.csv_pasajeros),
        )
        self.patch_pasajeros.start()
        self.addCleanup(self.patch_pasajeros.stop)

        self.patch_consumos = patch.object(
            aplicacion,
            "DB_CONSUMOS",
            str(self.csv_consumos),
        )
        self.patch_consumos.start()
        self.addCleanup(self.patch_consumos.stop)

        # El backup también debe quedar dentro del directorio temporal.
        # Esta ruta corresponde a la implementación que usa
        # DB_PASAJEROS/data de forma relativa.


    def copiar_backup(self, origen, destino):
        destino = Path(destino)

        destino.parent.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copyfile(origen, destino)

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

    def leer_padron(self):
        return pd.read_csv(
            self.csv_pasajeros,
            dtype={
                "Nro. habitación": str,
                "id_estadia": str,
            },
        )

    def verificar_consumos_intactos(self):
        contenido = self.csv_consumos.read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            contenido,
            self.contenido_consumos,
        )

    def test_agregar_conserva_estadias_anteriores(self):
        hoy = date.today()

        respuesta = self.subir([
            pasajero(
                "HUESPED C",
                103,
                hoy,
                hoy + timedelta(days=3),
                "33333333",
                "ESTADIA-C",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        self.assertEqual(
            set(df["Apellido y nombre"]),
            {"HUESPED A", "HUESPED B", "HUESPED C"},
        )

        ids = df.set_index("Apellido y nombre")["id_estadia"]

        self.assertEqual(ids["HUESPED A"], "ESTADIA-A")
        self.assertEqual(ids["HUESPED B"], "ESTADIA-B")

        # La nueva estadía debe recibir un UUID generado por el sistema.
        id_nuevo = ids["HUESPED C"]

        self.assertTrue(isinstance(id_nuevo, str))
        self.assertEqual(len(id_nuevo), 32)
        self.assertNotEqual(id_nuevo, "ESTADIA-C")

        self.verificar_consumos_intactos()

    def test_agregar_no_elimina_estadia_anterior_de_misma_habitacion(self):
        hoy = date.today()

        respuesta = self.subir([
            pasajero(
                "HUESPED NUEVO",
                101,
                hoy + timedelta(days=10),
                hoy + timedelta(days=13),
                "44444444",
                "ESTADIA-NUEVA",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        nombres = set(df["Apellido y nombre"])

        self.assertIn("HUESPED A", nombres)
        self.assertIn("HUESPED NUEVO", nombres)

        self.verificar_consumos_intactos()

    def test_csv_sin_id_genera_uuid(self):
        hoy = date.today()

        respuesta = self.subir(
            [
                pasajero(
                    "HUESPED SIN ID",
                    103,
                    hoy,
                    hoy + timedelta(days=2),
                    "55555555",
                )
            ],
            incluir_id=False,
        )

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        nuevo = df[
            df["Apellido y nombre"] == "HUESPED SIN ID"
        ]

        self.assertEqual(len(nuevo), 1)

        id_generado = nuevo.iloc[0]["id_estadia"]

        self.assertTrue(isinstance(id_generado, str))
        self.assertEqual(len(id_generado), 32)

        self.verificar_consumos_intactos()

    def test_reemplazar_conserva_id_de_estadia_reconocida(self):
        hoy = date.today()

        respuesta = self.subir(
            [
                pasajero(
                    "HUESPED A",
                    105,
                    self.fecha_ingreso,
                    self.fecha_egreso,
                    "11111111",
                ),
                pasajero(
                    "HUESPED NUEVO",
                    106,
                    hoy,
                    hoy + timedelta(days=2),
                    "66666666",
                ),
            ],
            modo="reemplazar",
        )

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        self.assertEqual(len(df), 2)

        ids = df.set_index("Apellido y nombre")["id_estadia"]

        self.assertEqual(ids["HUESPED A"], "ESTADIA-A")
        self.assertEqual(len(ids["HUESPED NUEVO"]), 32)

        self.assertNotIn("HUESPED B", df["Apellido y nombre"].tolist())

        self.verificar_consumos_intactos()

    def test_csv_invalido_no_modifica_padron(self):
        antes = self.csv_pasajeros.read_bytes()

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
        self.assertEqual(
            self.csv_pasajeros.read_bytes(),
            antes,
        )

        self.verificar_consumos_intactos()

    def test_importacion_no_duplica_id_estadia(self):
        hoy = date.today()

        respuesta = self.subir([
            pasajero(
                "HUESPED A",
                110,
                self.fecha_ingreso,
                self.fecha_egreso,
                "11111111",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        self.assertEqual(
            df["id_estadia"].duplicated().sum(),
            0,
        )

        self.verificar_consumos_intactos()

    def test_importacion_crea_backup_del_padron_anterior(self):
        contenido_anterior = self.csv_pasajeros.read_bytes()

        respuesta = self.subir([
            pasajero(
                "HUESPED BACKUP",
                111,
                self.fecha_ingreso,
                self.fecha_egreso,
                "99999999",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)


        backups = list(
            (self.directorio / "backups").glob(
                "pasajeros_backup_*.csv"
            )
        )
        self.assertEqual(len(backups), 1)
        self.assertEqual(
            backups[0].read_bytes(),
            contenido_anterior,
        )

        self.verificar_consumos_intactos()

    def test_csv_no_puede_imponer_un_id_estadia_arbitrario(self):
        hoy = date.today()
        id_falso = "ID-IMPOSTOR-123"

        respuesta = self.subir([
            pasajero(
                "HUESPED NUEVO",
                107,
                hoy,
                hoy + timedelta(days=3),
                "77777777",
                id_falso,
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()
        nuevo = df[
            df["Apellido y nombre"] == "HUESPED NUEVO"
        ]

        self.assertEqual(len(nuevo), 1)

        id_real = nuevo.iloc[0]["id_estadia"]

        self.assertNotEqual(id_real, id_falso)
        self.assertEqual(len(id_real), 32)

        self.verificar_consumos_intactos()

    def test_coincidencia_ambigua_no_asigna_un_id_existente(self):
        fila_a = pasajero(
            "HUESPED AMBIGUO",
            108,
            self.fecha_ingreso,
            self.fecha_egreso,
            "88888888",
            "ESTADIA-AMBIGUA-A",
        )

        fila_b = pasajero(
            "HUESPED AMBIGUO",
            109,
            self.fecha_ingreso,
            self.fecha_egreso,
            "88888888",
            "ESTADIA-AMBIGUA-B",
        )

        pd.DataFrame([fila_a, fila_b]).to_csv(
            self.csv_pasajeros,
            index=False,
        )

        respuesta = self.subir([
            pasajero(
                "HUESPED AMBIGUO",
                110,
                self.fecha_ingreso,
                self.fecha_egreso,
                "88888888",
            )
        ])

        self.assertEqual(respuesta.status_code, 302)

        df = self.leer_padron()

        coincidencias = df[
            df["Apellido y nombre"] == "HUESPED AMBIGUO"
        ]

        self.assertEqual(len(coincidencias), 3)

        ids = set(coincidencias["id_estadia"])

        self.assertIn("ESTADIA-AMBIGUA-A", ids)
        self.assertIn("ESTADIA-AMBIGUA-B", ids)

        ids_nuevos = ids - {
            "ESTADIA-AMBIGUA-A",
            "ESTADIA-AMBIGUA-B",
        }

        self.assertEqual(len(ids_nuevos), 1)

        id_nuevo = ids_nuevos.pop()

        self.assertEqual(len(id_nuevo), 32)

        self.verificar_consumos_intactos()


if __name__ == "__main__":
    unittest.main()
