
import unittest
import pandas as pd

from core.identidad_estadias import procesar_identidades


class TestIdentidadEstadias(unittest.TestCase):

    def setUp(self):
        self.pasajero = {
            'Nro. habitación': '101',
            'Fecha de ingreso': '01/11/2026',
            'Fecha de egreso': '04/11/2026',
            'Apellido y nombre': 'PEREZ JUAN',
            'Nro. doc.': '12345678',
            'Voucher': 'VOUCHER-001',
            'Servicios': 'DESAYUNO',
            'id_estadia': 'UUID-ANTERIOR-001',
        }

    def dataframe(self, registros):
        return pd.DataFrame(registros)

    def test_conserva_id_misma_estadia_aunque_cambie_habitacion(self):
        existente = self.dataframe([self.pasajero])

        nuevo = self.pasajero.copy()
        nuevo['Nro. habitación'] = '205'

        resultado, resumen = procesar_identidades(
            existente, self.dataframe([nuevo]), 'agregar'
        )

        fila = resultado[
            resultado['Nro. habitación'] == '205'
        ].iloc[0]

        self.assertEqual(
            fila['id_estadia'],
            'UUID-ANTERIOR-001'
        )
        self.assertEqual(resumen['coincidencias'], 1)

    def test_nueva_estadia_genera_uuid_diferente(self):
        existente = self.dataframe([self.pasajero])

        nuevo = self.pasajero.copy()
        nuevo['Fecha de ingreso'] = '05/11/2026'
        nuevo['Fecha de egreso'] = '08/11/2026'

        resultado, resumen = procesar_identidades(
            existente, self.dataframe([nuevo]), 'agregar'
        )

        fila = resultado[
            resultado['Fecha de ingreso'] == '05/11/2026'
        ].iloc[0]

        self.assertTrue(fila['id_estadia'])
        self.assertNotEqual(
            fila['id_estadia'],
            'UUID-ANTERIOR-001'
        )
        self.assertEqual(resumen['nuevas_estadias'], 1)

    def test_dni_ficticio_no_se_usa_como_identidad(self):
        existente = self.pasajero.copy()
        existente['Nro. doc.'] = '00000000'

        nuevo = existente.copy()
        nuevo['Voucher'] = 'VOUCHER-NUEVO'

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'reemplazar'
        )

        self.assertNotEqual(
            resultado.iloc[0]['id_estadia'],
            'UUID-ANTERIOR-001'
        )
        self.assertEqual(resumen['nuevas_estadias'], 1)

    def test_reemplazar_conserva_id_reconocido(self):
        existente = self.dataframe([self.pasajero])

        nuevo = self.pasajero.copy()
        nuevo['Nro. habitación'] = '222'

        resultado, resumen = procesar_identidades(
            existente, self.dataframe([nuevo]), 'reemplazar'
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado.iloc[0]['id_estadia'],
            'UUID-ANTERIOR-001'
        )

    def test_agregar_conserva_registros_no_incluidos(self):
        otro = self.pasajero.copy()
        otro['Nro. habitación'] = '102'
        otro['Apellido y nombre'] = 'GOMEZ ANA'
        otro['Nro. doc.'] = '87654321'
        otro['Voucher'] = 'VOUCHER-002'
        otro['id_estadia'] = 'UUID-ANTERIOR-002'

        existente = self.dataframe([self.pasajero, otro])

        nuevo = self.pasajero.copy()
        nuevo['Servicios'] = 'MEDIA PENSION'

        resultado, resumen = procesar_identidades(
            existente, self.dataframe([nuevo]), 'agregar'
        )

        self.assertEqual(len(resultado), 2)

        ids = set(resultado['id_estadia'])

        self.assertIn('UUID-ANTERIOR-001', ids)
        self.assertIn('UUID-ANTERIOR-002', ids)

    def test_dos_coincidencias_ambiguas_generan_id_nuevo(self):
        duplicado = self.pasajero.copy()
        duplicado['id_estadia'] = 'UUID-ANTERIOR-002'

        existente = self.dataframe([
            self.pasajero,
            duplicado,
        ])

        nuevo = self.pasajero.copy()

        resultado, resumen = procesar_identidades(
            existente, self.dataframe([nuevo]), 'reemplazar'
        )

        nuevo_id = resultado.iloc[0]['id_estadia']

        self.assertNotEqual(
            nuevo_id,
            'UUID-ANTERIOR-001'
        )
        self.assertNotEqual(
            nuevo_id,
            'UUID-ANTERIOR-002'
        )
        self.assertEqual(resumen['coincidencias_ambiguas'], 1)

    def test_id_estadia_no_se_repite_en_nuevas_estadias(self):
        existente = self.dataframe([self.pasajero])

        nuevo1 = self.pasajero.copy()
        nuevo1['Nro. doc.'] = '11111111'
        nuevo1['Fecha de ingreso'] = '05/11/2026'
        nuevo1['Fecha de egreso'] = '08/11/2026'

        nuevo2 = self.pasajero.copy()
        nuevo2['Nro. doc.'] = '22222222'
        nuevo2['Fecha de ingreso'] = '05/11/2026'
        nuevo2['Fecha de egreso'] = '08/11/2026'

        resultado, resumen = procesar_identidades(
            existente,
            self.dataframe([nuevo1, nuevo2]),
            'agregar'
        )

        ids = resultado['id_estadia'].tolist()

        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(resumen['nuevas_estadias'], 2)

    def test_modo_invalido_genera_error(self):
        with self.assertRaises(ValueError):
            procesar_identidades(
                pd.DataFrame(),
                self.dataframe([self.pasajero]),
                'incorrecto'
            )


    def test_asigna_id_a_estadia_existente_sin_id(self):
        existente = self.pasajero.copy()
        existente['id_estadia'] = ''

        nuevo = existente.copy()
        nuevo['Servicios'] = 'MEDIA PENSION'

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'agregar'
        )

        self.assertEqual(len(resultado), 1)
        self.assertTrue(resultado.iloc[0]['id_estadia'])
        self.assertEqual(resumen['coincidencias'], 1)

    def test_no_duplica_estadia_existente_sin_id(self):
        existente = self.pasajero.copy()
        existente['id_estadia'] = ''

        nuevo = existente.copy()

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'agregar'
        )

        self.assertEqual(len(resultado), 1)

    def test_reemplazar_asigna_id_a_estadia_reconocida_sin_id(self):
        existente = self.pasajero.copy()
        existente['id_estadia'] = ''

        nuevo = existente.copy()
        nuevo['Nro. habitación'] = '205'

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'reemplazar'
        )

        self.assertEqual(len(resultado), 1)
        self.assertTrue(resultado.iloc[0]['id_estadia'])
        self.assertEqual(resumen['coincidencias'], 1)

    def test_agregar_asigna_id_a_registro_antiguo_no_incluido(self):
        existente = self.pasajero.copy()
        existente['id_estadia'] = ''

        otro = existente.copy()
        otro['Apellido y nombre'] = 'GOMEZ ANA'
        otro['Nro. doc.'] = '87654321'
        otro['Voucher'] = 'VOUCHER-002'

        nuevo = self.pasajero.copy()

        resultado, resumen = procesar_identidades(
            self.dataframe([existente, otro]),
            self.dataframe([nuevo]),
            'agregar'
        )

        self.assertEqual(len(resultado), 2)
        self.assertTrue(resultado['id_estadia'].notna().all())
        self.assertTrue(
            all(str(valor).strip() for valor in resultado['id_estadia'])
        )

    def test_duplicados_en_csv_nuevo_no_comparten_uuid(self):
        existente = self.dataframe([self.pasajero])

        nuevo1 = self.pasajero.copy()
        nuevo2 = self.pasajero.copy()

        resultado, resumen = procesar_identidades(
            existente,
            self.dataframe([nuevo1, nuevo2]),
            'agregar'
        )

        ids = resultado['id_estadia'].tolist()

        # Ninguna de las dos filas debe compartir UUID.
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)

    def test_dni_compartido_con_nombres_distintos_no_confunde(self):
        existente = self.pasajero.copy()

        nuevo = self.pasajero.copy()
        nuevo['Apellido y nombre'] = 'GOMEZ ANA'

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'reemplazar'
        )

        nuevo_id = resultado.iloc[0]['id_estadia']

        self.assertNotEqual(
            nuevo_id,
            'UUID-ANTERIOR-001'
        )
        self.assertEqual(resumen['coincidencias'], 0)
        self.assertEqual(resumen['nuevas_estadias'], 1)

    def test_fechas_invalidas_no_generan_coincidencias(self):
        existente = self.pasajero.copy()

        nuevo = self.pasajero.copy()
        nuevo['Fecha de ingreso'] = 'fecha incorrecta'

        resultado, resumen = procesar_identidades(
            self.dataframe([existente]),
            self.dataframe([nuevo]),
            'agregar'
        )

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resumen['coincidencias'], 0)

        ids = resultado['id_estadia'].tolist()

        self.assertEqual(len(set(ids)), 2)
        self.assertNotEqual(
            resultado.iloc[1]['id_estadia'],
            'UUID-ANTERIOR-001'
        )

if __name__ == '__main__':
    unittest.main()
