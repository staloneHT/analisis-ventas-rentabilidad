"""Gráficos estáticos listos para README e informe."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

AZUL, VERDE, NARANJA = "#183153", "#168a78", "#df8730"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 170})
CLP = FuncFormatter(lambda x, _: f"${x/1e6:,.0f} M")


def generar(t: dict[str, pd.DataFrame], destino: Path) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    archivos = []

    def guardar(nombre, titulo, ylabel="CLP"):
        ax = plt.gca()
        ax.set_title(titulo, loc="left", color=AZUL, weight="bold", pad=14)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=.18)
        if ylabel == "CLP": ax.yaxis.set_major_formatter(CLP)
        plt.tight_layout()
        ruta = destino / f"{nombre}.png"
        plt.savefig(ruta, bbox_inches="tight")
        plt.close()
        archivos.append(ruta)

    m = t["mensual"]
    plt.figure(figsize=(11, 4)); plt.plot(m["mes"], m["ventas_netas"], color=AZUL, marker="o", markersize=3)
    plt.xticks(rotation=55, ha="right"); guardar("01_ventas_mensuales", "Ventas netas mensuales")
    plt.figure(figsize=(11, 4)); plt.bar(m["mes"], m["utilidad_bruta"], color=VERDE)
    plt.xticks(rotation=55, ha="right"); guardar("02_utilidad_mensual", "Utilidad bruta mensual")
    p = t["producto"]
    for num, col, titulo in [(3, "ventas_netas", "Productos con mayores ventas"), (4, "utilidad_bruta", "Productos con mayor utilidad bruta")]:
        top = p.nlargest(10, col).sort_values(col)
        plt.figure(figsize=(9, 5)); plt.barh(top["producto"], top[col], color=AZUL if num == 3 else VERDE)
        plt.gca().xaxis.set_major_formatter(CLP); guardar(f"{num:02d}_top_productos_{'ventas' if num == 3 else 'utilidad'}", titulo, "")
    r = t["region"].sort_values("ventas_netas")
    plt.figure(figsize=(9, 4.5)); plt.barh(r["region"], r["ventas_netas"], color=AZUL)
    plt.gca().xaxis.set_major_formatter(CLP); guardar("05_ventas_region", "Ventas netas por región", "")
    c = t["categoria"].sort_values("margen_pct")
    plt.figure(figsize=(8, 4)); plt.barh(c["categoria"], c["margen_pct"], color=VERDE)
    guardar("06_margen_categoria", "Margen bruto por categoría", "Margen bruto (%)")
    canal = t["canal"].sort_values("ventas_netas")
    plt.figure(figsize=(7, 4)); plt.barh(canal["canal_venta"], canal["ventas_netas"], color=AZUL)
    plt.gca().xaxis.set_major_formatter(CLP); guardar("07_ventas_canal", "Ventas netas por canal", "")
    piv = m.pivot_table(index="numero_mes", columns="anio", values="ventas_netas")
    plt.figure(figsize=(9, 4));
    for anio, color in [(2024, AZUL), (2025, VERDE)]: plt.plot(piv.index, piv[anio], marker="o", label=str(anio), color=color)
    plt.xticks(np.arange(1, 13)); plt.legend(frameon=False); guardar("08_comparacion_anual", "Ventas mensuales: 2024 frente a 2025")
    d = t["descuentos"]
    plt.figure(figsize=(7, 4)); plt.bar(d["rango_descuento"].astype(str), d["margen_pct"], color=NARANJA)
    guardar("09_descuentos_margen", "Margen bruto por rango de descuento", "Margen bruto (%)")
    c = t["categoria"].sort_values("ventas_netas")
    y = np.arange(len(c)); plt.figure(figsize=(9, 4.5)); plt.barh(y-.2, c["ventas_netas"], height=.38, color=AZUL, label="Ventas netas")
    plt.barh(y+.2, c["utilidad_bruta"], height=.38, color=VERDE, label="Utilidad bruta")
    plt.yticks(y, c["categoria"]); plt.gca().xaxis.set_major_formatter(CLP); plt.legend(frameon=False)
    guardar("10_ventas_utilidad_categoria", "Ventas y utilidad por categoría", "")
    return archivos
