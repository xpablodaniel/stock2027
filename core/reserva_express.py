"""
Gestión de reservas express (walk-ins).

Cada reserva nueva recibe un id_estadia único para que sus consumos puedan
asociarse a esa estadía y no solamente al número de habitación.
"""

from datetime import date, datetime, timedelta
import os
import uuid

import pandas as pd

DB_PASAJEROS = 'data/pasajeros.csv'
FORMATO_FECHA = '%d/%m/%Y'


def _normalizar_habitacion(valor):
    """Normaliza números de habitación leídos desde CSV (101, 101.0, '101')."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    try:
        numero = float(texto)
        if numero.is_integer():
            return int(numero)
    except (TypeError, ValueError):
        pass
    return texto.casefold()


def _parsear_fecha(valor):
    """Interpreta fechas del CSV en formato argentino; devuelve date o None."""
    if pd.isna(valor) or not str(valor).strip():
        return None
    texto = str(valor).strip()
    for formato in (FORMATO_FECHA, '%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _leer_pasajeros():
    if not os.path.exists(DB_PASAJEROS):
        return pd.DataFrame()
    try:
        return pd.read_csv(DB_PASAJEROS, dtype={'Nro. habitación': 'object'})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _buscar_conflicto_estadia(df, habitacion, ingreso, egreso):
    """
    Busca solapamientos para la misma habitación.

    Se interpreta el egreso como límite exclusivo: un huésped que egresa el
    día 28 libera la habitación para un nuevo ingreso el día 28.
    Si hay fechas incompletas/ilegibles para esa habitación, bloquea la
    asignación por seguridad en vez de asumir que está disponible.
    """
    columna_hab = 'Nro. habitación'
    if df.empty or columna_hab not in df.columns:
        return None

    objetivo = _normalizar_habitacion(habitacion)
    for _, fila in df.iterrows():
        if _normalizar_habitacion(fila.get(columna_hab)) != objetivo:
            continue

        fecha_ingreso = _parsear_fecha(fila.get('Fecha de ingreso'))
        fecha_egreso = _parsear_fecha(fila.get('Fecha de egreso'))

        if fecha_ingreso is None or fecha_egreso is None:
            return (
                'No se puede verificar la disponibilidad: existe un registro '
                'de esta habitación con fechas faltantes o inválidas. '
                'Revisá ese registro antes de crear la reserva.'
            )

        # Intervalos [ingreso, egreso): el día de egreso no cuenta como noche ocupada.
        if fecha_ingreso < egreso and fecha_egreso > ingreso:
            if fecha_ingreso <= ingreso < fecha_egreso:
                return f'La habitación {habitacion} ya está ocupada en la fecha de ingreso.'
            return (
                f'La habitación {habitacion} tiene una reserva que se superpone '
                f'con el período solicitado ({fecha_ingreso.strftime(FORMATO_FECHA)} '
                f'al {fecha_egreso.strftime(FORMATO_FECHA)}).'
            )
    return None


def obtener_habitaciones_disponibles():
    """Devuelve habitaciones sin una estadía vigente hoy, según el dashboard."""
    from core.dashboard import PISOS, obtener_habitaciones_ocupadas

    todas_habitaciones = []
    for piso_habs in PISOS.values():
        todas_habitaciones.extend(piso_habs)

    ocupadas = obtener_habitaciones_ocupadas()
    return sorted(h for h in todas_habitaciones if h not in ocupadas.keys())


def crear_reserva_express(
    habitacion,
    nombre='Huésped sin reserva',
    pax=1,
    servicios='DESAYUNO',
    noches=1
):
    """
    Crea una reserva express y le asigna un identificador estable id_estadia.

    Returns:
        tuple: (dict_reserva, mensaje). Si falla: (None, mensaje).
    """
    try:
        habitacion = int(habitacion)
    except (TypeError, ValueError):
        return None, 'Número de habitación inválido'

    try:
        pax = int(pax)
        if not 1 <= pax <= 4:
            return None, 'La cantidad de personas debe ser entre 1 y 4'
    except (TypeError, ValueError):
        return None, 'Cantidad de personas inválida'

    try:
        noches = int(noches)
        if not 1 <= noches <= 30:
            return None, 'La cantidad de noches debe ser entre 1 y 30'
    except (TypeError, ValueError):
        return None, 'La cantidad de noches debe ser entre 1 y 30'

    hoy = date.today()
    fecha_salida = hoy + timedelta(days=noches)

    df_existente = _leer_pasajeros()
    conflicto = _buscar_conflicto_estadia(df_existente, habitacion, hoy, fecha_salida)
    if conflicto:
        return None, conflicto

    nueva_reserva = {
        'Nro. habitación': habitacion,
        'Fecha de ingreso': hoy.strftime(FORMATO_FECHA),
        'Fecha de egreso': fecha_salida.strftime(FORMATO_FECHA),
        'Plazas ocupadas': pax,
        'Tipo documento': 'DNI',
        'Nro. doc.': '00000000',
        'Apellido y nombre': nombre.strip() if isinstance(nombre, str) else nombre,
        'Edad': 0,
        'Voucher': f'WALK-{habitacion}-{hoy.strftime("%d%m%Y")}-{uuid.uuid4().hex[:6].upper()}',
        'Servicios': servicios,
        'Estado': 'Activo',
        'Paquete': 'Walk-in Express',
        'Sede': 'Principal',
        'id_estadia': uuid.uuid4().hex,
    }

    try:
        df_nuevo = pd.DataFrame([nueva_reserva])
        if not df_existente.empty:
            # Conserva las columnas del CSV actual y agrega id_estadia si todavía no existe.
            if 'id_estadia' not in df_existente.columns:
                df_existente['id_estadia'] = ''
            for columna in df_existente.columns:
                if columna not in df_nuevo.columns:
                    df_nuevo[columna] = ''
            for columna in df_nuevo.columns:
                if columna not in df_existente.columns:
                    df_existente[columna] = ''
            df_nuevo = df_nuevo[df_existente.columns]
            df_nuevo = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_nuevo.to_csv(DB_PASAJEROS, index=False)
        return nueva_reserva, 'Reserva express creada exitosamente'
    except Exception as e:
        return None, f'Error al crear reserva: {e}'


def calcular_noches_maximas(habitacion):
    """Calcula los días hasta la próxima reserva válida de esa habitación."""
    df = _leer_pasajeros()
    if df.empty or 'Nro. habitación' not in df.columns:
        return 0

    objetivo = _normalizar_habitacion(habitacion)
    hoy = date.today()
    fechas_futuras = []
    for _, fila in df.iterrows():
        if _normalizar_habitacion(fila.get('Nro. habitación')) != objetivo:
            continue
        ingreso = _parsear_fecha(fila.get('Fecha de ingreso'))
        if ingreso and ingreso > hoy:
            fechas_futuras.append(ingreso)
    return max(0, (min(fechas_futuras) - hoy).days) if fechas_futuras else 0


def validar_datos_reserva(habitacion, nombre, pax):
    """Valida datos básicos de una reserva express."""
    try:
        habitacion = int(habitacion)
    except (TypeError, ValueError):
        return False, 'Número de habitación inválido'

    try:
        pax = int(pax)
        if not 1 <= pax <= 4:
            return False, 'La cantidad de personas debe estar entre 1 y 4'
    except (TypeError, ValueError):
        return False, 'Cantidad de personas inválida'

    if nombre and len(nombre.strip()) < 2:
        return False, 'El nombre debe tener al menos 2 caracteres'

    return True, ''
