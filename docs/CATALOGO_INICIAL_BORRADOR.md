# CATALOGO_INICIAL_BORRADOR

Estado: **borrador para validar con las comandas originales. No es definitivo.**
Sin código ni SQL. Complementa [PLAN_IMPLEMENTACION_v1.md](./PLAN_IMPLEMENTACION_v1.md) (insumo 1).

## 1. Fuente y límites

- **Fuente única usada:** lo que la auditoría compartida (chat) transcribió de la comanda 2025 (hojas `Comedor`, `Recepcion_2`, `precio vinos`) y de la comanda actual de la habitación 350.
- **No tuve acceso a los archivos originales de las comandas** en este entorno: todo lo de abajo debe contrastarse contra ellos antes de cargarse.
- **`BEBIDAS_CATALOGO` del legacy no se usa como catálogo.** Solo aparece como comparación de precios.
- **No inventé productos, presentaciones ni stock.** Lo que no está en la fuente figura como `¿?`.

## 2. Estructura de cada producto (a completar con Gerencia/Administración)

| Dato | Descripción |
|---|---|
| Categoría | Gaseosa, Agua, Saborizada, Cerveza, Vino, Espumante/Sidra, Cafetería |
| Producto (marca/sabor) | Una unidad comercial concreta; nunca "Gaseosa" genérica |
| Presentación | Tipo y tamaño de envase que compra el hotel (**sin confirmar en toda la lista**) |
| Precio vigente | Según comanda actual |
| Controla stock | Sí para bebidas y fichas en v1; no para comedor |
| Habilitado para la venta | Vigente / histórico |
| Punto de venta | Comedor / Recepción-lobby (ver §5) |

## 3. Productos vigentes según la comanda actual (habitación 350)

### Sin alcohol
| Categoría | Producto | Precio comanda actual | Presentación | Observación |
|---|---|---:|---|---|
| Gaseosa | Coca | $3.500 | ¿? | Precio por categoría en la comanda |
| Gaseosa | Coca Zero | $3.500 | ¿? | Aparece en la comanda actual, no en la de 2025 |
| Gaseosa | Sprite | $3.500 | ¿? | |
| Gaseosa | Fanta | $3.500 | ¿? | |
| Gaseosa | Tónica | $3.500 | ¿? | |
| Gaseosa | Schweppes | ¿? | ¿? | La auditoría lo ubicó como ítem aparte; confirmar precio y categoría |
| Agua | Agua sin gas | $2.000 | ¿? | |
| Agua | Agua con gas | $2.000 | ¿? | |
| Saborizada | Manzana | $3.600 | ¿? | |
| Saborizada | Pomelo | $3.600 | ¿? | La comanda 2025 también tenía Pera: confirmar si sigue |
| Cafetería | Ficha de café | ¿? (el legacy la registra a $2.000) | Unidad | Máquina expendedora, solo recepción/lobby |

### Con alcohol (comedor)
| Categoría | Producto | Precio comanda actual |
|---|---|---:|
| Cerveza | Cerveza (la comanda actual muestra un solo ítem) | $5.500 |
| Vino | Nampe Malbec | $6.500 |
| Vino | Chacabuco Chenin | $10.000 |
| Vino | Chacabuco Malbec | $7.800 |
| Vino | Los Haroldos Reserva Malbec | $14.800 |
| Vino | Los Haroldos Reserva Chardonnay | $14.800 |
| Vino | Los Haroldos Estate Malbec | $11.000 |
| Vino | Los Haroldos Estate Chardonnay | $11.000 |

## 4. Productos solo en la comanda 2025 (candidatos a "histórico")

No entran al catálogo vigente automáticamente. Hay que confirmar cuáles siguen vendiéndose.

- Cerveza: Rubia / Negra / Roja (la comanda actual muestra solo "Cerveza").
- Saborizada Pera.
- Espumantes y sidra: Champagne Chandon, Los Haroldos Extra Brut, Sidra Real.
- Vinos: Ruca Malen Chardonnay, Los Haroldos Estate Blend, Los Haroldos Estate Cabernet.

## 5. Diferencias de precio detectadas (legacy vs. comanda actual)

| Producto | Legacy | Comanda actual |
|---|---:|---:|
| Gaseosa | $3.400 | $3.500 |
| Agua | $3.000 | $2.000 |
| Saborizada | $3.500 | $3.600 |

Para la carga inicial vale **la comanda actual**, y el precio queda como primer registro del historial de precios (los consumos históricos del legacy no se tocan).

## 6. Decisiones y preguntas pendientes

1. **Punto de venta (comedor vs. recepción/lobby):** la comanda 2025 separa ambos. El modelo v1.1 **no tiene** ese dato. Si se necesita para informes o para mostrar solo los productos correspondientes, es una incorporación al modelo (nota de diseño N5, a resolver en la Etapa 3, sin rehacer lo aprobado).
2. **Presentación y unidad de compra** de cada producto (botella individual, lata, pack): hay que definirlas con las compras reales del hotel.
3. **Cerveza:** ¿se diferencia Rubia/Negra/Roja o es una sola?
4. **Schweppes y Tónica:** ¿son una misma cosa o dos productos?
5. **Ficha de café:** precio vigente y si se vende también en el comedor.
6. **Stock inicial:** se carga con el primer conteo físico, no se estima.
7. **Productos históricos** del §4: ¿se cargan como inactivos para conservar su nombre en informes?

## 7. Próximo paso

Contrastar este borrador con las comandas originales (archivos o fotos) y completar los `¿?`. Con eso queda cerrado el insumo 1.
