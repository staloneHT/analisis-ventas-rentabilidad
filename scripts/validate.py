"""Verificación de artefactos entregables y consistencia básica."""
from pathlib import Path
import json
import nbformat
import pandas as pd

root = Path(__file__).resolve().parents[1]
raw = pd.read_csv(root / "data/raw/ventas_raw.csv")
clean = pd.read_csv(root / "data/processed/ventas_clean.csv")
kpis = json.loads((root / "reports/kpis.json").read_text(encoding="utf-8"))
notebook = nbformat.read(root / "notebooks/01_analisis_ventas_rentabilidad.ipynb", as_version=4)
figuras = list((root / "reports/figures").glob("*.png"))
resultado = {
    "lineas_raw": len(raw), "lineas_limpias": len(clean),
    "meses": clean.fecha_venta.str[:7].nunique(), "productos": clean.id_producto.nunique(),
    "categorias": clean.categoria.nunique(), "clientes": clean.id_cliente.nunique(),
    "regiones": clean.region.nunique(), "figuras": len(figuras),
    "celdas_notebook": len(notebook.cells),
    "celdas_codigo_ejecutadas": sum(c.cell_type == "code" and c.execution_count is not None for c in notebook.cells),
}
assert resultado["lineas_raw"] >= 12000
assert resultado["meses"] == 24 and resultado["productos"] >= 30
assert resultado["categorias"] >= 6 and resultado["clientes"] >= 500
assert resultado["regiones"] >= 6 and resultado["figuras"] >= 10
assert all(c.execution_count is not None for c in notebook.cells if c.cell_type == "code")
readme = (root / "README.md").read_text(encoding="utf-8")
reporte = (root / "reports/resumen_ejecutivo.md").read_text(encoding="utf-8")
numero = f"${kpis['ventas_netas_clp']:,.0f}".replace(",", ".")
assert numero in readme and numero in reporte
print(resultado)
