import pandas as pd
from src.limpieza import limpiar


def fila(**cambios):
    base = dict(id_linea_venta="L1", id_pedido="O1", fecha_venta="2024-01-05", id_cliente="C1",
                id_producto="P1", producto="Mouse", categoria="Tecnología", region=" Metropolitana ",
                canal_venta="online ", cantidad=2, precio_unitario=1000, costo_unitario=500,
                descuento_pct=.1, estado_pedido="completado")
    return {**base, **cambios}


def test_duplicados_fecha_normalizacion_e_idempotencia():
    limpio, audit = limpiar(pd.DataFrame([fila(), fila()]))
    assert len(limpio) == 1 and audit["duplicados_eliminados"] == 1
    assert limpio.iloc[0]["region"] == "Metropolitana"
    assert limpio.iloc[0]["canal_venta"] == "Online"
    assert str(limpio.iloc[0]["fecha_venta"].date()) == "2024-01-05"
    segunda, _ = limpiar(limpio)
    pd.testing.assert_frame_equal(limpio, segunda)


def test_invalidos_y_recuperacion_catalogo():
    df = pd.DataFrame([fila(), fila(id_linea_venta="L2", id_pedido="O2", categoria=None),
                       fila(id_linea_venta="L3", id_pedido="O3", cantidad=0),
                       fila(id_linea_venta="L4", id_pedido="O4", fecha_venta="mal"),
                       fila(id_linea_venta="L5", id_pedido="O5", descuento_pct=1.5)])
    limpio, audit = limpiar(df)
    assert len(limpio) == 2
    assert audit["campos_catalogo_recuperados"]["categoria"] == 1
    assert audit["registros_descartados"] == 3
