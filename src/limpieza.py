"""Limpieza auditable e idempotente de líneas de venta."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUMNAS = ["id_linea_venta", "id_pedido", "fecha_venta", "id_cliente", "id_producto", "producto", "categoria", "region", "canal_venta", "cantidad", "precio_unitario", "costo_unitario", "descuento_pct", "estado_pedido"]
REGIONES = {s.casefold(): s for s in ["Metropolitana", "Valparaíso", "Biobío", "Maule", "Coquimbo", "La Araucanía", "Los Lagos", "Antofagasta"]}
CANALES = {s.casefold(): s for s in ["Online", "Tienda Física", "Marketplace"]}
ESTADOS = {s.casefold(): s for s in ["Completado", "Cancelado", "Devuelto"]}


def limpiar(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Normaliza y valida sin imputar importes ni fechas; devuelve datos y auditoría."""
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Columnas faltantes: {sorted(faltantes)}")
    datos = df[COLUMNAS].copy()
    inicial = len(datos)
    categorias_corregidas = 0
    for col in ["region", "canal_venta", "estado_pedido"]:
        original = datos[col].astype("string")
        mapa = {"region": REGIONES, "canal_venta": CANALES, "estado_pedido": ESTADOS}[col]
        normal = original.str.strip().str.casefold().map(mapa).astype("string")
        categorias_corregidas += int((original.notna() & normal.notna() & original.ne(normal)).sum())
    nulos_antes = {k: int(v) for k, v in datos.isna().sum().items() if v}
    duplicados = int(datos.duplicated().sum())
    datos = datos.drop_duplicates().copy()
    for col in ["id_linea_venta", "id_pedido", "id_cliente", "id_producto", "producto", "categoria", "region", "canal_venta", "estado_pedido"]:
        datos[col] = datos[col].astype("string").str.strip()
        datos[col] = datos[col].replace("", pd.NA)
    for col, mapa in [("region", REGIONES), ("canal_venta", CANALES), ("estado_pedido", ESTADOS)]:
        datos[col] = datos[col].str.casefold().map(mapa).astype("string")
    # Solo se completan atributos de catálogo cuando el ID tiene un único valor conocido.
    recuperados = {}
    for col in ["producto", "categoria"]:
        referencia = datos.dropna(subset=["id_producto", col]).groupby("id_producto")[col].agg(lambda s: s.mode().iloc[0])
        mascara = datos[col].isna() & datos["id_producto"].isin(referencia.index)
        recuperados[col] = int(mascara.sum())
        datos.loc[mascara, col] = datos.loc[mascara, "id_producto"].map(referencia)
    datos["fecha_venta"] = pd.to_datetime(datos["fecha_venta"], errors="coerce")
    for col in ["cantidad", "precio_unitario", "costo_unitario", "descuento_pct"]:
        datos[col] = pd.to_numeric(datos[col], errors="coerce")
    obligatorias = COLUMNAS
    motivos = {
        "campos_obligatorios_o_fecha": datos[obligatorias].isna().any(axis=1),
        "cantidad_no_positiva": datos["cantidad"].le(0).fillna(False),
        "precio_no_positivo": datos["precio_unitario"].le(0).fillna(False),
        "costo_negativo": datos["costo_unitario"].lt(0).fillna(False),
        "descuento_fuera_0_1": (~datos["descuento_pct"].between(0, 1)).fillna(False),
        "fecha_fuera_periodo": (~datos["fecha_venta"].between("2024-01-01", "2025-12-31")).fillna(False),
        "cantidad_no_entera": datos["cantidad"].mod(1).ne(0).fillna(False),
        "id_linea_repetido": datos["id_linea_venta"].duplicated(keep="first"),
    }
    # Un pedido debe compartir fecha, cliente, región, canal y estado en todas sus líneas.
    for col in ["fecha_venta", "id_cliente", "region", "canal_venta", "estado_pedido"]:
        conflicto = datos.groupby("id_pedido", dropna=False)[col].transform("nunique").gt(1)
        motivos[f"pedido_inconsistente_{col}"] = conflicto.fillna(False)
    invalidas = pd.concat(motivos, axis=1).any(axis=1)
    datos = datos.loc[~invalidas].copy()
    datos["cantidad"] = datos["cantidad"].astype("int64")
    datos = datos.sort_values("id_linea_venta").reset_index(drop=True)
    auditoria = {"filas_iniciales": inicial, "filas_finales": len(datos), "duplicados_eliminados": duplicados,
                 "nulos_antes": nulos_antes, "campos_catalogo_recuperados": recuperados,
                 "categorias_normalizadas": categorias_corregidas, "registros_descartados": int(invalidas.sum()),
                 "motivos_descarte": {k: int(v.sum()) for k, v in motivos.items()}}
    return datos, auditoria


def ejecutar(origen: Path = ROOT / "data/raw/ventas_raw.csv", destino: Path = ROOT / "data/processed/ventas_clean.csv") -> tuple[pd.DataFrame, dict]:
    """Lee CSV, guarda el procesado y su auditoría."""
    datos, auditoria = limpiar(pd.read_csv(origen, encoding="utf-8-sig"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(destino, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    (destino.parent / "auditoria_limpieza.json").write_text(json.dumps(auditoria, ensure_ascii=False, indent=2), encoding="utf-8")
    return datos, auditoria


if __name__ == "__main__":
    _, auditoria = ejecutar()
    print(json.dumps(auditoria, ensure_ascii=False, indent=2))
