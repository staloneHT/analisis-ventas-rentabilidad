"""Orquesta cálculo, gráficos y reportes derivados del CSV procesado."""
from pathlib import Path
import json
import pandas as pd
from src.kpis import enriquecer, resumen, tablas
from src.visualizaciones import generar

ROOT = Path(__file__).resolve().parents[1]


def clp(x: float) -> str: return f"${x:,.0f}".replace(",", ".")
def pct(x: float) -> str: return f"{x:.1f}%".replace(".", ",")


def ejecutar() -> tuple[dict, dict]:
    base = pd.read_csv(ROOT / "data/processed/ventas_clean.csv", parse_dates=["fecha_venta"])
    df = enriquecer(base)
    k = resumen(df)
    t = tablas(df)
    figuras = generar(t, ROOT / "reports/figures")
    reportes = ROOT / "reports"; reportes.mkdir(exist_ok=True)
    (reportes / "kpis.json").write_text(json.dumps(k, ensure_ascii=False, indent=2), encoding="utf-8")
    m = t["mensual"]; cat = t["categoria"]; prod = t["producto"]; reg = t["region"]; canal = t["canal"]
    mejor_cat = cat.sort_values("utilidad_bruta", ascending=False).iloc[0]
    bajo_margen = prod[prod["ventas_netas"] >= prod["ventas_netas"].quantile(.75)].sort_values("margen_pct").iloc[0]
    mejor_region = reg.sort_values("ventas_netas", ascending=False).iloc[0]
    mejor_canal = canal.sort_values("ventas_netas", ascending=False).iloc[0]
    peor_mes = m.loc[m["crecimiento_mom_pct"].idxmin()]
    d = t["descuentos"]; sin = d[d["rango_descuento"].astype(str).eq("0%")].iloc[0]; alto = d[d["rango_descuento"].astype(str).eq(">20%")].iloc[0]
    hallazgos = [
        (f"La categoría {mejor_cat.categoria} aporta {clp(mejor_cat.utilidad_bruta)} de utilidad bruta.", f"Margen agregado: {pct(mejor_cat.margen_pct)}; ventas: {clp(mejor_cat.ventas_netas)}.", "Priorizar surtido y disponibilidad de esta categoría.", "Utilidad bruta y margen por categoría"),
        (f"{bajo_margen['producto']} combina ventas altas con margen de {pct(bajo_margen.margen_pct)}.", f"Ventas: {clp(bajo_margen.ventas_netas)}; utilidad: {clp(bajo_margen.utilidad_bruta)}.", "Revisar costo de compra y límites de descuento de este producto.", "Margen y utilidad por producto"),
        (f"{mejor_region.region} lidera las ventas regionales.", f"Ventas: {clp(mejor_region.ventas_netas)}; utilidad: {clp(mejor_region.utilidad_bruta)}.", "Proteger cobertura logística y probar campañas incrementales en otras regiones.", "Ventas y utilidad por región"),
        (f"{mejor_canal.canal_venta} es el mayor canal por ventas.", f"Ventas: {clp(mejor_canal.ventas_netas)}; margen: {pct(mejor_canal.margen_pct)}.", "Comparar costo comercial y adquisición antes de ampliar inversión.", "Margen y ventas por canal"),
        (f"El mayor descenso mensual ocurrió en {peor_mes.mes}.", f"Variación frente al mes anterior: {pct(peor_mes.crecimiento_mom_pct)}; ventas: {clp(peor_mes.ventas_netas)}.", "Investigar mezcla de productos, demanda y calendario promocional.", "Crecimiento mensual de ventas"),
        ("Los descuentos altos se asocian con un margen distinto al de ventas sin descuento.", f"Margen sin descuento: {pct(sin.margen_pct)}; con descuento >20%: {pct(alto.margen_pct)}.", "Probar promociones con grupo de control; esta comparación no demuestra causalidad.", "Margen por rango de descuento"),
    ]
    bloque = "\n\n".join(f"### {i}. {h}\n\n**Evidencia:** {e}\n\n**Interpretación y oportunidad:** {a}\n\n**Seguimiento:** {s}." for i, (h, e, a, s) in enumerate(hallazgos, 1))
    figlinks = "\n".join(f"![{p.stem}](figures/{p.name})" for p in figuras[:3])
    texto = f"""# Resumen ejecutivo | Business Sales Analytics

## Contexto y objetivo

Caso de retail/e-commerce **enteramente sintético** en regiones de Chile, de enero de 2024 a diciembre de 2025. Se evalúan ventas reconocidas, utilidad bruta y oportunidades comerciales.

## Metodología

Se generaron pedidos y líneas con semilla fija. Se eliminaron duplicados y registros inválidos, se normalizaron categorías y se excluyeron pedidos cancelados y devueltos de ingresos y costos reconocidos. Las tasas operacionales usan pedidos únicos.

## KPIs principales

| Indicador | Valor |
|---|---:|
| Ventas netas | {clp(k['ventas_netas_clp'])} CLP |
| Utilidad bruta | {clp(k['utilidad_bruta_clp'])} CLP |
| Margen bruto global | {pct(k['margen_bruto_pct'])} |
| Pedidos completados únicos | {k['pedidos_completados']:,} |
| Ticket promedio | {clp(k['ticket_promedio_clp'])} CLP |
| Unidades vendidas | {k['unidades_vendidas']:,} |
| Clientes compradores | {k['clientes_compradores']:,} |
| Cancelación / devolución | {pct(k['tasa_cancelacion_pct'])} / {pct(k['tasa_devolucion_pct'])} |

## Hallazgos priorizados y decisiones

{bloque}

## Gráficos

{figlinks}

## Limitaciones y próximos pasos

Datos sintéticos: los patrones no validan demanda real. Utilidad bruta excluye gastos operacionales, impuestos e intereses. No se modelan costos de marketing, logística ni adquisición. Antes de invertir, contrastar con datos reales y experimentos controlados.
"""
    (reportes / "resumen_ejecutivo.md").write_text(texto, encoding="utf-8")
    (reportes / "hallazgos.json").write_text(json.dumps([{"hallazgo": h, "evidencia": e, "accion": a, "seguimiento": s} for h,e,a,s in hallazgos], ensure_ascii=False, indent=2), encoding="utf-8")
    return k, t


if __name__ == "__main__":
    print(json.dumps(ejecutar()[0], ensure_ascii=False, indent=2))
