"""Métricas financieras; solo pedidos completados generan ingreso reconocido."""
import numpy as np
import pandas as pd


def enriquecer(datos: pd.DataFrame) -> pd.DataFrame:
    """Calcula importes por línea. descuento_pct se expresa entre 0 y 1."""
    df = datos.copy()
    reconocido = df["estado_pedido"].eq("Completado")
    df["venta_bruta"] = np.where(reconocido, df["cantidad"] * df["precio_unitario"], 0.0)
    df["descuento_monto"] = df["venta_bruta"] * df["descuento_pct"]
    df["venta_neta"] = df["venta_bruta"] - df["descuento_monto"]
    df["costo_total"] = np.where(reconocido, df["cantidad"] * df["costo_unitario"], 0.0)
    df["utilidad_bruta"] = df["venta_neta"] - df["costo_total"]
    df["margen_bruto_pct"] = np.where(df["venta_neta"].gt(0), df["utilidad_bruta"] / df["venta_neta"] * 100, 0.0)
    return df


def margen(utilidad: float, venta: float) -> float:
    return float(utilidad / venta * 100) if venta else 0.0


def resumen(df: pd.DataFrame) -> dict:
    pedidos = df[["id_pedido", "estado_pedido"]].drop_duplicates("id_pedido")
    completados = df[df["estado_pedido"].eq("Completado")]
    venta = float(df["venta_neta"].sum())
    utilidad = float(df["utilidad_bruta"].sum())
    n = int(pedidos["estado_pedido"].eq("Completado").sum())
    total = len(pedidos)
    return {"ventas_netas_clp": venta, "utilidad_bruta_clp": utilidad, "margen_bruto_pct": margen(utilidad, venta),
            "pedidos_completados": n, "ticket_promedio_clp": venta / n if n else 0.0,
            "unidades_vendidas": int(completados["cantidad"].sum()), "clientes_compradores": int(completados["id_cliente"].nunique()),
            "tasa_cancelacion_pct": float(pedidos["estado_pedido"].eq("Cancelado").mean() * 100) if total else 0.0,
            "tasa_devolucion_pct": float(pedidos["estado_pedido"].eq("Devuelto").mean() * 100) if total else 0.0,
            "pedidos_totales": total}


def agregado(df: pd.DataFrame, columnas: str | list[str]) -> pd.DataFrame:
    """Suma importes y calcula margen agregado ponderado por ingreso."""
    cols = [columnas] if isinstance(columnas, str) else columnas
    resultado = df.groupby(cols, observed=True, dropna=False).agg(
        ventas_netas=("venta_neta", "sum"), utilidad_bruta=("utilidad_bruta", "sum"),
        unidades=("cantidad", lambda s: int(s[df.loc[s.index, "estado_pedido"].eq("Completado")].sum())),
        pedidos=("id_pedido", "nunique")).reset_index()
    resultado["margen_pct"] = np.where(resultado["ventas_netas"].gt(0), resultado["utilidad_bruta"] / resultado["ventas_netas"] * 100, 0.0)
    return resultado


def mensual(df: pd.DataFrame) -> pd.DataFrame:
    datos = df.assign(mes=df["fecha_venta"].dt.to_period("M").astype(str))
    out = agregado(datos, "mes").sort_values("mes")
    out["crecimiento_mom_pct"] = out["ventas_netas"].pct_change() * 100
    out["anio"] = out["mes"].str[:4].astype(int)
    out["numero_mes"] = out["mes"].str[5:7].astype(int)
    return out


def tablas(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    clientes = df[df["estado_pedido"].eq("Completado")].groupby("id_cliente").agg(ventas_netas=("venta_neta", "sum"), pedidos=("id_pedido", "nunique")).reset_index()
    clientes["ticket_promedio"] = clientes["ventas_netas"] / clientes["pedidos"]
    desc = df[df["estado_pedido"].eq("Completado")].copy()
    desc["rango_descuento"] = pd.cut(desc["descuento_pct"], [-.001, 0, .10, .20, 1], labels=["0%", ">0–10%", ">10–20%", ">20%"])
    return {"mensual": mensual(df), "producto": agregado(df, ["id_producto", "producto", "categoria"]),
            "categoria": agregado(df, "categoria"), "region": agregado(df, "region"), "canal": agregado(df, "canal_venta"),
            "clientes": clientes, "descuentos": agregado(desc, "rango_descuento")}
