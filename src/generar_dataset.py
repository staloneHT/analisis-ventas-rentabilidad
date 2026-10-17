"""Genera transacciones sintéticas reproducibles; no representa una empresa real."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEED = 20241017
REGIONES = ["Metropolitana", "Valparaíso", "Biobío", "Maule", "Coquimbo", "La Araucanía", "Los Lagos", "Antofagasta"]
CATEGORIAS = {
    "Tecnología": ["Audífonos", "Teclado", "Mouse", "Webcam", "Monitor", "Hub USB"],
    "Hogar": ["Lámpara", "Organizador", "Purificador", "Almohada", "Cafetera", "Aspiradora"],
    "Deportes": ["Botella", "Mancuernas", "Colchoneta", "Banda elástica", "Mochila", "Balón"],
    "Oficina": ["Silla", "Escritorio", "Cuaderno", "Lámpara escritorio", "Soporte notebook", "Archivador"],
    "Belleza": ["Secador", "Cepillo", "Espejo", "Crema", "Set manicure", "Rizador"],
    "Jardín": ["Macetero", "Regadera", "Herramientas", "Guantes", "Semillas", "Manguera"],
}


def generar_dataset(destino: Path = ROOT / "data/raw/ventas_raw.csv", semilla: int = SEED) -> pd.DataFrame:
    """Genera 24 meses completos, pedidos multilínea y anomalías controladas."""
    rng = np.random.default_rng(semilla)
    productos = [(f"P{i:03d}", nombre, categoria) for i, (categoria, nombre) in enumerate(((cat, nombre) for cat, nombres in CATEGORIAS.items() for nombre in nombres), 1)]
    catalogo = pd.DataFrame(productos, columns=["id_producto", "producto", "categoria"])
    catalogo["precio_base"] = rng.integers(12000, 180000, len(catalogo)) // 100 * 100
    catalogo["ratio_costo"] = rng.uniform(.49, .76, len(catalogo))
    catalogo.loc[catalogo.index[:3], "ratio_costo"] = [.87, .89, .86]  # Alta rotación, bajo margen.
    catalogo.loc[catalogo.index[-3:], "ratio_costo"] = [.42, .45, .40]  # Menor rotación, mejor margen.
    catalogo["peso"] = 1.0
    catalogo.loc[catalogo.index[:3], "peso"] = 3.4
    catalogo.loc[catalogo.index[-3:], "peso"] = .48
    periodos = pd.period_range("2024-01", "2025-12", freq="M")
    pesos_mes = np.array([.84, .82, .94, .97, 1.01, .96, 1.03, 1.04, 1.07, 1.11, 1.35, 1.48] * 2)
    pesos_mes[12:] *= 1.12
    n_pedidos = 10500
    meses = rng.choice(len(periodos), size=n_pedidos, p=pesos_mes / pesos_mes.sum())
    dias = rng.integers(1, 29, n_pedidos)
    fechas = pd.to_datetime([f"{periodos[m]}-{d:02d}" for m, d in zip(meses, dias)])
    clientes = rng.choice(np.arange(1, 1201), size=n_pedidos, p=(lambda w: w / w.sum())(rng.pareto(1.8, 1200) + .3))
    regiones = rng.choice(REGIONES, n_pedidos, p=[.40, .15, .13, .09, .07, .06, .06, .04])
    canales = rng.choice(["Online", "Tienda Física", "Marketplace"], n_pedidos, p=[.45, .35, .20])
    estados = rng.choice(["Completado", "Cancelado", "Devuelto"], n_pedidos, p=[.89, .07, .04])
    lineas = rng.choice([1, 2, 3], n_pedidos, p=[.57, .32, .11])
    pedido_idx = np.repeat(np.arange(n_pedidos), lineas)
    prod_idx = rng.choice(len(catalogo), len(pedido_idx), p=catalogo["peso"] / catalogo["peso"].sum())
    elegido = catalogo.iloc[prod_idx].reset_index(drop=True)
    cantidad = rng.choice([1, 2, 3, 4], len(pedido_idx), p=[.69, .22, .07, .02])
    precio = np.maximum(1000, (elegido["precio_base"].to_numpy() * rng.normal(1, .045, len(pedido_idx)) * (1 + .035 * (meses[pedido_idx] >= 12))).round(-2)).astype(int)
    costo = (elegido["precio_base"].to_numpy() * elegido["ratio_costo"].to_numpy() * rng.normal(1, .025, len(pedido_idx))).round(-2).astype(int)
    descuento = rng.choice([0, .05, .10, .15, .20, .30], len(pedido_idx), p=[.38, .25, .19, .10, .06, .02])
    df = pd.DataFrame({
        "id_linea_venta": [f"L{i:06d}" for i in range(1, len(pedido_idx) + 1)],
        "id_pedido": [f"O{i+1:06d}" for i in pedido_idx],
        "fecha_venta": fechas[pedido_idx].strftime("%Y-%m-%d"),
        "id_cliente": [f"C{i:04d}" for i in clientes[pedido_idx]],
        "id_producto": elegido["id_producto"], "producto": elegido["producto"],
        "categoria": elegido["categoria"], "region": regiones[pedido_idx],
        "canal_venta": canales[pedido_idx], "cantidad": cantidad,
        "precio_unitario": precio, "costo_unitario": costo,
        "descuento_pct": descuento, "estado_pedido": estados[pedido_idx],
    })
    # Inyecciones deliberadas y deterministas; índices disjuntos.
    df.loc[0:11, "region"] = " metropolitana "
    df.loc[12:23, "canal_venta"] = "online "
    df.loc[24:35, "estado_pedido"] = df.loc[24:35, "estado_pedido"].str.lower()
    df.loc[36:41, "categoria"] = None  # Recuperable desde catálogo del producto.
    df.loc[42:47, "producto"] = None
    df.loc[48:52, "region"] = None  # Región indispensable, descartar.
    df.loc[53:57, "cantidad"] = 0
    df.loc[58:62, "descuento_pct"] = 1.5
    df.loc[63:67, "precio_unitario"] = -100
    df.loc[68:72, "fecha_venta"] = "fecha-invalida"
    df.loc[73:77, "costo_unitario"] = -1
    df = pd.concat([df, df.iloc[100:115].copy()], ignore_index=True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    salida = generar_dataset()
    print(f"Generadas {len(salida):,} líneas sintéticas en {ROOT / 'data/raw/ventas_raw.csv'}")
