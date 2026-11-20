import unittest

from openpyxl import Workbook, load_workbook
from io import BytesIO

from core.consulta_salidas_excel import agregar_hoja_consulta_salidas


class TestConsultaSalidasExcel(unittest.TestCase):
    def setUp(self):
        self.consulta = {
            "fecha_salida": "20/11/2026",
            "criterio": "Consumos de bebidas vigentes, vinculados y validados por id_estadia",
            "resumen": {
                "cuentas": 1, "habitaciones": 1, "pasajeros": 2,
                "total_confirmado": "81500",
            },
            "cuentas": [{
                "habitacion": "102",
                "voucher": "TEST-102",
                "titular": "PAX UNO",
                "pasajeros": ["PAX UNO", "PAX DOS"],
                "productos": [
                    {
                        "producto": "Ficha de café", "cantidad_total": "2",
                        "cantidades_incompletas": False, "operaciones": 2,
                        "importe_confirmado": "6000",
                    },
                    {
                        "producto": "Agua", "cantidad_total": "1",
                        "cantidades_incompletas": False, "operaciones": 1,
                        "importe_confirmado": "2000",
                    },
                ],
                "detalle": [
                    {
                        "fecha": "18/11/2026 09:00", "pasajero": "PAX UNO",
                        "producto": "Ficha de café", "cantidad": "1",
                        "precio_unitario": "3000", "importe_confirmado": "3000",
                    },
                    {
                        "fecha": "19/11/2026 09:00", "pasajero": "PAX DOS",
                        "producto": "Ficha de café", "cantidad": "1",
                        "precio_unitario": "3000", "importe_confirmado": "3000",
                    },
                    {
                        "fecha": "19/11/2026 10:00", "pasajero": "PAX UNO",
                        "producto": "Agua", "cantidad": "1",
                        "precio_unitario": "2000", "importe_confirmado": "2000",
                    },
                ],
                "total_confirmado": "8000",
            }],
        }

    def test_agrega_tercera_hoja_y_conserva_las_existentes(self):
        libro = Workbook()
        libro.active.title = "Resumen"
        libro.create_sheet("Detalle")

        hoja = agregar_hoja_consulta_salidas(libro, self.consulta)

        self.assertEqual(libro.sheetnames, ["Resumen", "Detalle", "Consulta de salidas"])
        self.assertEqual(hoja["A2"].value, "Fecha de salida: 20/11/2026")
        self.assertEqual(hoja["F4"].value, 81500)
        self.assertEqual(hoja["F15"].value, 8000)

    def test_operaciones_quedan_agrupadas_y_ocultas(self):
        libro = Workbook()
        hoja = agregar_hoja_consulta_salidas(libro, self.consulta)

        filas_ocultas = [
            numero for numero, dimension in hoja.row_dimensions.items()
            if dimension.hidden
        ]
        self.assertEqual(len(filas_ocultas), 3)
        self.assertTrue(all(hoja.row_dimensions[fila].outlineLevel == 1 for fila in filas_ocultas))

    def test_libro_se_puede_guardar_y_reabrir(self):
        libro = Workbook()
        agregar_hoja_consulta_salidas(libro, self.consulta)
        archivo = BytesIO()
        libro.save(archivo)
        archivo.seek(0)
        reabierto = load_workbook(archivo)
        self.assertIn("Consulta de salidas", reabierto.sheetnames)


if __name__ == "__main__":
    unittest.main()
