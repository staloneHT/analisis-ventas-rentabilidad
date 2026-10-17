# Diccionario de datos y definiciones

**Fuente:** datos sintéticos generados con NumPy (`SEED = 20241017`). Ningún registro corresponde a una empresa real. Período: enero de 2024 a diciembre de 2025. Moneda: CLP nominales, sin ajuste por inflación.

| Campo | Tipo | Definición |
|---|---|---|
| `id_linea_venta` | texto | Identificador único de línea. |
| `id_pedido` | texto | Identificador de pedido; puede tener varias líneas. |
| `fecha_venta` | fecha | Fecha del pedido. |
| `id_cliente` | texto | Cliente sintético. |
| `id_producto` | texto | SKU sintético. |
| `producto` | texto | Nombre de producto. |
| `categoria` | texto | Familia comercial. |
| `region` | texto | Región de Chile. |
| `canal_venta` | texto | Online, Tienda Física o Marketplace. |
| `cantidad` | entero | Unidades en la línea. |
| `precio_unitario` | CLP | Precio antes de descuento por unidad. |
| `costo_unitario` | CLP | Costo de mercancía por unidad. |
| `descuento_pct` | proporción 0–1 | 0,10 representa 10%. |
| `estado_pedido` | texto | Completado, Cancelado o Devuelto; consistente en todo el pedido. |

## Política contable del caso

Solo pedidos **Completados** reconocen ventas y costo de productos vendidos. Cancelados y completamente devueltos generan cero venta, costo y utilidad reconocidos. Se incluyen en las tasas operacionales calculadas por **pedidos únicos**. No se modelan devoluciones parciales.

| Variable derivada | Fórmula por línea completada | Unidad |
|---|---|---|
| Venta bruta | `cantidad × precio_unitario` | CLP |
| Descuento | `venta_bruta × descuento_pct` | CLP |
| Venta neta | `venta_bruta − descuento` | CLP |
| Costo total | `cantidad × costo_unitario` | CLP |
| Utilidad bruta | `venta_neta − costo_total` | CLP |
| Margen bruto | `utilidad_bruta / venta_neta × 100` | % |

El margen agregado siempre es `SUM(utilidad_bruta) / SUM(venta_neta) × 100`; nunca el promedio simple de márgenes de línea. Si el denominador es cero, se informa 0% por convenio. **Utilidad bruta no equivale a utilidad neta empresarial:** no se incluyen gastos operativos, transporte, impuestos, intereses ni marketing.

## Catálogo de KPIs

Todos los KPIs cubren enero de 2024 a diciembre de 2025, salvo crecimiento mensual, que se refiere a cada mes y su predecesor. Los importes se expresan en CLP nominales.

| KPI | Definición y fórmula | Unidad | Interpretación empresarial |
|---|---|---|---|
| Ventas netas | Suma de `venta_neta` completada | CLP | Ingreso reconocido. |
| Utilidad bruta | Suma de `utilidad_bruta` completada | CLP | Contribución antes de otros gastos. |
| Margen bruto global | Suma utilidad / suma ventas × 100 | % | Rentabilidad de mercancía ponderada. |
| Pedidos completados | Conteo distinto de `id_pedido` completado | pedidos | Volumen de transacciones válidas. |
| Ticket promedio | Ventas netas / pedidos completados | CLP/pedido | Valor medio por compra. |
| Unidades vendidas | Suma de `cantidad` completada | unidades | Volumen físico vendido. |
| Clientes compradores | Conteo distinto de `id_cliente` completado | clientes | Alcance comercial. |
| Crecimiento mensual | (ventas mes / ventas mes anterior − 1) × 100 | % | Ritmo de crecimiento; primer mes no aplicable. |
| Ventas por región | Suma de ventas netas por región | CLP | Concentración geográfica. |
| Ventas y utilidad por categoría | Sumas de ventas y utilidad por categoría | CLP | Mezcla y contribución. |
| Top 10 productos por ventas | Diez SKU con mayor suma de venta neta | CLP | Productos de mayor facturación. |
| Top 10 productos por utilidad | Diez SKU con mayor suma de utilidad bruta | CLP | Productos de mayor contribución. |
| Top clientes por ventas | Clientes con mayor suma de venta neta | CLP | Concentración de compradores. |
| Tasa de cancelación | Pedidos cancelados únicos / pedidos totales únicos × 100 | % | Fricción antes de completar. |
| Tasa de devolución | Pedidos devueltos únicos / pedidos totales únicos × 100 | % | Fricción después de comprar. |
| Ventas por canal | Suma de venta neta por canal | CLP | Contribución comercial del canal. |

Las agregaciones por producto, región, categoría y canal incluyen las líneas no completadas con importes reconocidos cero. Para volumen y pedidos operativos, filtrar `estado_pedido` según el análisis requerido.

## Reglas de limpieza

Se eliminan duplicados exactos. Se normalizan espacios y capitalización de región, canal y estado. `producto` y `categoria` faltantes se recuperan solo desde otros registros del mismo `id_producto`. No se imputan fecha, región, cantidad, precio, costo ni descuento. Se descartan líneas con campos obligatorios faltantes, fecha fuera del período, cantidad no entera o no positiva, precio no positivo, costo negativo, descuento fuera de 0–1 o identificador de línea repetido. Pedidos con fecha, cliente, región, canal o estado contradictorios entre líneas se excluyen. Los conteos exactos se conservan en `data/processed/auditoria_limpieza.json`.
