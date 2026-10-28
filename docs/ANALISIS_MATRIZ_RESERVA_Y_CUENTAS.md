# Matriz A (tipo de reserva) y Matriz B (cuentas) — validación contra CSV reales

Sin código de producción. Fuentes: `reservaIndividual.csv` (27 filas) y `pruebaGroup.csv` (47 filas).

## Matriz A — resultado sobre los CSV

| Señal | reservaIndividual | pruebaGroup |
|---|---|---|
| Paquete | `MDP ...` (100 %) | `PPJ MAR DEL PLATA 11/03 (13)` (100 %) |
| Transporte | `Sin Transporte` (100 %) | `PPJ MDQ BUS 2 - PPJ MDQ 2` (100 %) |
| Servicios | Desayuno / U.PROPIAS / Media pensión (**3 filas vacías**) | `PENSIÓN COMPLETA` (100 %) |
| Tipo habitación | DOBLE MATRIMONIAL / INDIVIDUALES | DOBLE / TRIPLE A COMPARTIR |
| Cód. alojamiento | `900` | `900 B` |
| Resultado | **INDIVIDUAL** (alta confianza) | **CONTINGENTE** (alta confianza) |

Ambos se clasifican correctamente solo con Paquete + Transporte (señales "muy alto"); el resto confirma.
`Servicios` vacío no debe penalizar: es una señal faltante, no contraria.

## Hallazgos que la matriz debe tolerar

1. **Habitación con sufijo de cama** en contingente: `227 A`, `227 B`. 47 filas = 47 "habitaciones" pero solo 24 físicas. El legacy usa la habitación como clave: hay que normalizar a `habitacion_base` + `cama`.
2. **Voucher en contingente**: 11 vouchers agrupan 2 pasajeros que están en la *misma habitación base* (parejas viajando juntas), el resto es 1 voucher por persona. En 12 de 24 habitaciones conviven vouchers distintos.
3. **`Cantidad plazas` vs `Plazas ocupadas`** no son confiables (hab. 119: 1 vs 2).
4. **Documentos repetidos** en individual: DNI 23265607 y 27707673 aparecen en hab. 103 (estado `T`) y 121 (estado `O`) con vouchers distintos = cambio de habitación en el rooming. Hay que filtrar por `Estado` (O = vigente) o tomar el último; no es duplicado real.
5. `Entidad` mezcla SUTEBA / PROMO / SIN CARGO / RESP; no sirve para clasificar. Hay menores (edad 2, 8).
6. Individual con voucher compartido entre 2 habitaciones (2 casos): familia en varias habitaciones.
7. DOBLE INDIVIDUALES (hab. 231, 224, 353) en reserva individual: dos personas en habitación doble que no necesariamente son pareja.

## Matriz B — ¿quién comparte cuenta?

`cuenta_id` es una entidad propia; **no es habitación ni voucher**. Una cuenta agrupa pasajeros; cada pasajero pertenece a una sola cuenta; la habitación es solo la ubicación actual.

| tipo_reserva | Regla de agrupación | Resultado en los CSV |
|---|---|---|
| INDIVIDUAL | Misma `Voucher` ⇒ misma cuenta (aunque estén en varias habitaciones) | 12 vouchers = 12 cuentas (27 pasajeros) |
| CONTINGENTE | Por defecto 1 cuenta por pasajero. Se fusiona solo si comparten voucher **y** habitación base | 36 cuentas (47 pasajeros): 25 individuales + 11 parejas |
| NO DETERMINADO | Sin cuentas automáticas: pedir confirmación a recepción | — |

Casos conceptuales:

| Caso | Tipo | Cuentas |
|---|---|---|
| Matrimonio | Individual | 1 |
| Dos jubilados desconocidos en `DOBLE A COMPARTIR` (voucher distinto) | Contingente | 2 |
| Familia en varias habitaciones (mismo voucher) | Individual | 1 |
| Grupo de jubilados | Contingente | 1 por persona (o pareja con voucher común) |
| Cambio parcial de habitación | — | El pasajero conserva su `cuenta_id`; solo cambia su ubicación |

## Decisiones confirmadas

1. **Pareja = cuenta compartida.** En individual por voucher común; en contingente, una pareja con voucher común también comparte.
2. **`DOBLE INDIVIDUALES`** es una habitación de dos camas. En reserva individual puede alojar padre/hijo, hermanas o hijos cuyos padres están en otra habitación: la cuenta la define el **voucher** (familia), no la habitación ni el tipo de habitación.
3. **Contingente:** pasajeros que comparten habitación sin voucher común = **cuentas separadas**, se conozcan o no.
4. Habitación y cuenta son independientes; el cambio de habitación no cambia la cuenta.

Regla resultante: `cuenta_id` = voucher (individual); en contingente, voucher + habitación base (pareja) o pasajero (resto).

## Relación con stock

Las cuentas solo identifican *quién consume*. El stock se descuenta por producto consumido, independiente de la cuenta; el informe por período agrega los consumos por producto y, opcionalmente, por tipo de reserva/contingente.
