#!/usr/bin/env python3
"""
Script para gestionar reservas futuras
Permite eliminar y volver a cargar reservas de una fecha específica
"""

import pandas as pd
import sys
from datetime import datetime
import shutil

DB_PASAJEROS = 'data/pasajeros.csv'
BACKUP_DIR = 'data/backups'

def crear_backup():
    """Crea un backup del archivo de pasajeros"""
    import os
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{BACKUP_DIR}/pasajeros_backup_{timestamp}.csv'
    shutil.copy(DB_PASAJEROS, backup_file)
    print(f'✅ Backup creado: {backup_file}')
    return backup_file

def eliminar_reservas_por_fecha(fecha_ingreso):
    """
    Elimina todas las reservas con una fecha de ingreso específica
    
    Args:
        fecha_ingreso: Fecha en formato DD/MM/YYYY
    """
    # Crear backup primero
    crear_backup()
    
    # Leer archivo
    df = pd.read_csv(DB_PASAJEROS)
    registros_antes = len(df)
    
    # Filtrar (mantener todos EXCEPTO los de esa fecha)
    df_filtrado = df[df['Fecha de ingreso'] != fecha_ingreso]
    registros_despues = len(df_filtrado)
    eliminados = registros_antes - registros_despues
    
    # Guardar
    df_filtrado.to_csv(DB_PASAJEROS, index=False)
    
    print(f'\n📊 RESULTADO:')
    print(f'   Registros antes: {registros_antes}')
    print(f'   Registros después: {registros_despues}')
    print(f'   Eliminados: {eliminados}')
    print(f'\n✅ Reservas del {fecha_ingreso} eliminadas correctamente')

def agregar_reservas_desde_csv(archivo_csv):
    """
    Agrega reservas desde un archivo CSV externo
    
    Args:
        archivo_csv: Ruta al archivo CSV con las nuevas reservas
    """
    # Crear backup primero
    crear_backup()
    
    # Leer ambos archivos
    df_actual = pd.read_csv(DB_PASAJEROS)
    df_nuevas = pd.read_csv(archivo_csv)
    
    registros_antes = len(df_actual)
    
    # Combinar (append)
    df_combinado = pd.concat([df_actual, df_nuevas], ignore_index=True)
    registros_despues = len(df_combinado)
    agregados = registros_despues - registros_antes
    
    # Guardar
    df_combinado.to_csv(DB_PASAJEROS, index=False)
    
    print(f'\n📊 RESULTADO:')
    print(f'   Registros antes: {registros_antes}')
    print(f'   Registros después: {registros_despues}')
    print(f'   Agregados: {agregados}')
    print(f'\n✅ Reservas agregadas correctamente desde {archivo_csv}')

def mostrar_resumen():
    """Muestra un resumen de las reservas por fecha"""
    df = pd.read_csv(DB_PASAJEROS)
    
    print('\n📊 RESUMEN DE RESERVAS:')
    print(f'Total registros: {len(df)}\n')
    
    # Contar por fecha de ingreso
    ingresos = df.groupby('Fecha de ingreso').size().sort_index()
    print('Reservas por fecha de ingreso:')
    for fecha, count in ingresos.items():
        if '2026' in str(fecha):
            print(f'  {fecha}: {count} pasajeros')
    
    # Contar habitaciones únicas por fecha
    print('\nHabitaciones por fecha de ingreso:')
    habitaciones_por_fecha = df.groupby('Fecha de ingreso')['Nro. habitación'].nunique().sort_index()
    for fecha, count in habitaciones_por_fecha.items():
        if '2026' in str(fecha):
            print(f'  {fecha}: {count} habitaciones')

def menu_principal():
    """Menú interactivo para gestionar reservas"""
    print('\n' + '='*70)
    print('GESTIÓN DE RESERVAS FUTURAS')
    print('='*70)
    
    while True:
        print('\nOpciones:')
        print('1. Ver resumen de reservas')
        print('2. Eliminar reservas por fecha de ingreso')
        print('3. Agregar reservas desde archivo CSV')
        print('4. Salir')
        
        opcion = input('\nSelecciona una opción (1-4): ').strip()
        
        if opcion == '1':
            mostrar_resumen()
        
        elif opcion == '2':
            fecha = input('Fecha de ingreso a eliminar (DD/MM/YYYY): ').strip()
            confirmar = input(f'¿Confirmas eliminar todas las reservas del {fecha}? (s/n): ').strip().lower()
            if confirmar == 's':
                eliminar_reservas_por_fecha(fecha)
            else:
                print('❌ Operación cancelada')
        
        elif opcion == '3':
            archivo = input('Ruta al archivo CSV con las nuevas reservas: ').strip()
            try:
                agregar_reservas_desde_csv(archivo)
            except Exception as e:
                print(f'❌ Error: {e}')
        
        elif opcion == '4':
            print('\n👋 ¡Hasta luego!')
            break
        
        else:
            print('❌ Opción inválida')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo comando
        comando = sys.argv[1]
        
        if comando == 'resumen':
            mostrar_resumen()
        
        elif comando == 'eliminar' and len(sys.argv) > 2:
            fecha = sys.argv[2]
            eliminar_reservas_por_fecha(fecha)
        
        elif comando == 'agregar' and len(sys.argv) > 2:
            archivo = sys.argv[2]
            agregar_reservas_desde_csv(archivo)
        
        else:
            print('Uso:')
            print('  python3 gestionar_reservas_futuras.py resumen')
            print('  python3 gestionar_reservas_futuras.py eliminar DD/MM/YYYY')
            print('  python3 gestionar_reservas_futuras.py agregar archivo.csv')
    else:
        # Modo interactivo
        menu_principal()
