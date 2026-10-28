import pandas as pd
import os

def generar_resumen_check_out():
    if not os.path.exists('consumos_diarios.csv'):
        print("No hay consumos registrados para exportar.")
        return

    # 1. Cargar los datos
    df = pd.read_csv('consumos_diarios.csv')

    # 2. Crear la tabla dinámica (Pivot Table)
    # Esto coloca las categorías como columnas, similar a salidas.ods 
    resumen = df.pivot_table(
        index=['habitacion', 'pasajero'], 
        columns='categoria', 
        values='monto', 
        aggfunc='sum', 
        fill_value=0
    )

    # 3. Calcular el total por habitación
    resumen['TOTAL_A_COBRAR'] = resumen.sum(axis=1)

    # 4. Exportar a CSV para abrir en Excel/LibreOffice
    resumen.to_csv('resumen_salidas_final.csv')
    
    # 5. Exportar a un formato HTML/PDF (opcional para impresión)
    resumen.to_html('resumen_impresion.html')
    
    print("Exportación completada: 'resumen_salidas_final.csv'")
    return resumen

if __name__ == "__main__":
    generar_resumen_check_out()