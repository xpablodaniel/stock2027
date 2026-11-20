"""Exportación de la consulta de salidas a una hoja de un libro XLSX existente."""

from decimal import Decimal, InvalidOperation

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


COLOR_TITULO = "245B78"
COLOR_CUENTA = "D9EAF2"
COLOR_PRODUCTO = "EAF2F8"
COLOR_TOTAL = "DDEBD7"


def _numero(valor):
    """Convierte importes/cantidades válidos a número de Excel."""
    if valor in (None, ""):
        return None
    try:
        numero = Decimal(str(valor))
        if numero.is_finite():
            return float(numero)
    except (InvalidOperation, ValueError, TypeError):
        pass
    return None


def _fila(hoja, valores):
    hoja.append(valores)
    for celda in hoja[hoja.max_row]:
        if isinstance(celda.value, str):
            # Evita que textos provenientes de los datos se interpreten como fórmulas.
            celda.data_type = "s"
    return hoja.max_row


def agregar_hoja_consulta_salidas(libro, consulta):
    """Agrega la hoja de consulta sin alterar las hojas ya existentes.

    Las filas de operaciones quedan agrupadas y ocultas debajo de cada
    resumen de producto; el usuario puede expandirlas desde el esquema de Excel.
    """
    nombre_hoja = "Consulta de salidas"
    if nombre_hoja in libro.sheetnames:
        del libro[nombre_hoja]

    hoja = libro.create_sheet(nombre_hoja)
    hoja.sheet_view.showGridLines = False
    hoja.sheet_properties.outlinePr.summaryBelow = True
    hoja.sheet_view.showOutlineSymbols = True

    _fila(hoja, ["CONSULTA DE CONSUMOS - PASAJEROS SALIENTES"])
    hoja.merge_cells("A1:F1")
    hoja["A1"].font = Font(bold=True, size=15, color="FFFFFF")
    hoja["A1"].fill = PatternFill("solid", fgColor=COLOR_TITULO)
    hoja["A1"].alignment = Alignment(horizontal="center")

    _fila(hoja, [f"Fecha de salida: {consulta.get('fecha_salida', '')}"])
    _fila(hoja, [consulta.get("criterio", "")])
    resumen = consulta.get("resumen", {})
    _fila(hoja, [
        f"Cuentas: {resumen.get('cuentas', 0)}",
        f"Habitaciones: {resumen.get('habitaciones', 0)}",
        f"Pasajeros: {resumen.get('pasajeros', 0)}",
        None,
        "Total confirmado",
        _numero(resumen.get("total_confirmado")) or 0,
    ])
    hoja["F4"].number_format = '"$" #,##0.00'
    _fila(hoja, [])
    encabezado = _fila(hoja, [
        "Fecha / referencia", "Pasajero / operaciones", "Producto",
        "Cantidad", "Precio unitario", "Importe confirmado",
    ])
    for celda in hoja[encabezado]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=COLOR_TITULO)
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    total_general = Decimal("0")
    cuentas = consulta.get("cuentas", [])

    for cuenta in cuentas:
        habitacion = str(cuenta.get("habitacion", ""))
        voucher = str(cuenta.get("voucher", ""))
        fila_cuenta = _fila(hoja, [
            f"HABITACIÓN {habitacion}  |  VOUCHER {voucher}", None, None, None, None, None
        ])
        hoja.merge_cells(start_row=fila_cuenta, start_column=1, end_row=fila_cuenta, end_column=6)
        celda = hoja.cell(fila_cuenta, 1)
        celda.font = Font(bold=True, color=COLOR_TITULO)
        celda.fill = PatternFill("solid", fgColor=COLOR_CUENTA)

        pasajeros = ", ".join(cuenta.get("pasajeros", []))
        fila_titular = _fila(hoja, [
            f"Titular: {cuenta.get('titular', '')}",
            f"Pasajeros: {pasajeros}", None, None, None, None
        ])
        hoja.merge_cells(start_row=fila_titular, start_column=2, end_row=fila_titular, end_column=6)
        hoja.cell(fila_titular, 1).font = Font(bold=True)
        hoja.cell(fila_titular, 2).alignment = Alignment(wrap_text=True)

        detalle_por_producto = {}
        for operacion in cuenta.get("detalle", []):
            detalle_por_producto.setdefault(operacion.get("producto", "Sin producto"), []).append(operacion)

        for producto in cuenta.get("productos", []):
            nombre_producto = producto.get("producto", "Sin producto")
            cantidad = _numero(producto.get("cantidad_total"))
            cantidad_texto = cantidad if cantidad is not None else "Cantidad incompleta"
            operaciones = int(producto.get("operaciones", 0) or 0)
            importe = _numero(producto.get("importe_confirmado")) or 0
            total_general += Decimal(str(importe))

            fila_producto = _fila(hoja, [
                "RESUMEN", f"{operaciones} operación(es)", nombre_producto,
                cantidad_texto, None, importe,
            ])
            for celda in hoja[fila_producto]:
                celda.font = Font(bold=True)
                celda.fill = PatternFill("solid", fgColor=COLOR_PRODUCTO)
            hoja.cell(fila_producto, 4).number_format = '#,##0.##'
            hoja.cell(fila_producto, 6).number_format = '"$" #,##0.00'

            operaciones_producto = detalle_por_producto.get(nombre_producto, [])
            if operaciones_producto:
                inicio_detalle = hoja.max_row + 1
                for operacion in operaciones_producto:
                    fila_detalle = _fila(hoja, [
                        operacion.get("fecha", ""),
                        operacion.get("pasajero", ""),
                        operacion.get("producto", ""),
                        _numero(operacion.get("cantidad")) if _numero(operacion.get("cantidad")) is not None else operacion.get("cantidad", ""),
                        _numero(operacion.get("precio_unitario")),
                        _numero(operacion.get("importe_confirmado")),
                    ])
                    hoja.cell(fila_detalle, 4).number_format = '#,##0.##'
                    hoja.cell(fila_detalle, 5).number_format = '"$" #,##0.00'
                    hoja.cell(fila_detalle, 6).number_format = '"$" #,##0.00'
                    for celda in hoja[fila_detalle]:
                        celda.font = Font(color="666666", size=10)
                fin_detalle = hoja.max_row
                hoja.row_dimensions.group(inicio_detalle, fin_detalle, outline_level=1, hidden=True)

        total_cuenta = _numero(cuenta.get("total_confirmado")) or 0
        fila_total_cuenta = _fila(hoja, [
            f"TOTAL HABITACIÓN {habitacion}", None, None, None, None, total_cuenta
        ])
        hoja.merge_cells(start_row=fila_total_cuenta, start_column=1, end_row=fila_total_cuenta, end_column=5)
        hoja.cell(fila_total_cuenta, 1).font = Font(bold=True)
        hoja.cell(fila_total_cuenta, 6).font = Font(bold=True)
        hoja.cell(fila_total_cuenta, 6).number_format = '"$" #,##0.00'
        for celda in hoja[fila_total_cuenta]:
            celda.fill = PatternFill("solid", fgColor=COLOR_TOTAL)

        _fila(hoja, [])

    fila_total = _fila(hoja, [
        "TOTAL GENERAL CONFIRMADO", None, None, None, None, float(total_general)
    ])
    hoja.merge_cells(start_row=fila_total, start_column=1, end_row=fila_total, end_column=5)
    for celda in hoja[fila_total]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=COLOR_TITULO)
        celda.border = Border(top=Side(style="thin", color=COLOR_TITULO))
    hoja.cell(fila_total, 6).number_format = '"$" #,##0.00'

    anchos = [22, 32, 34, 16, 19, 22]
    for indice, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(indice)].width = ancho
    hoja.freeze_panes = "A7"
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    hoja.page_setup.orientation = "landscape"
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.print_title_rows = "1:6"
    return hoja
