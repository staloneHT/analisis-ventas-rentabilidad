import pandas as pd
import pytest
from src.kpis import enriquecer, resumen, agregado, margen


def muestra():
    return pd.DataFrame({"id_pedido": ["A", "A", "B", "C"], "id_cliente": ["1", "1", "2", "3"],
        "estado_pedido": ["Completado", "Completado", "Cancelado", "Devuelto"],
        "categoria": ["X", "X", "Y", "Y"], "cantidad": [2, 1, 1, 1],
        "precio_unitario": [100, 200, 500, 500], "costo_unitario": [60, 100, 100, 100],
        "descuento_pct": [.1, 0, 0, 0]})


def test_finanzas_pedidos_multilinea_y_estados():
    df = enriquecer(muestra()); k = resumen(df)
    assert df["venta_bruta"].sum() == 400
    assert df["descuento_monto"].sum() == 20
    assert k["ventas_netas_clp"] == 380
    assert k["utilidad_bruta_clp"] == 160
    assert k["margen_bruto_pct"] == 160 / 380 * 100
    assert k["pedidos_completados"] == 1
    assert k["ticket_promedio_clp"] == 380
    assert k["unidades_vendidas"] == 3
    assert k["tasa_cancelacion_pct"] == pytest.approx(100 / 3)
    assert k["tasa_devolucion_pct"] == pytest.approx(100 / 3)
    assert df.loc[2:, "venta_neta"].sum() == 0


def test_division_cero_y_agregaciones():
    assert margen(0, 0) == 0
    df = enriquecer(muestra())
    a = agregado(df, "categoria")
    assert a["ventas_netas"].sum() == df["venta_neta"].sum()
    assert a["utilidad_bruta"].sum() == df["utilidad_bruta"].sum()
    assert float(a.loc[a["categoria"].eq("Y"), "margen_pct"].iloc[0]) == 0
