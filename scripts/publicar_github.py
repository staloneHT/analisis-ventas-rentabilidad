"""Publica este repositorio usando credenciales existentes de Git Credential Manager.

Uso: python scripts/publicar_github.py. No imprime ni almacena el token.
"""
from pathlib import Path
import json
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NOMBRE = "analisis-ventas-rentabilidad"


def comando(*args: str, entrada: str | None = None) -> str:
    proceso = subprocess.run(args, input=entrada, text=True, capture_output=True, cwd=ROOT, check=True)
    return proceso.stdout.strip()


def api(ruta: str, token: str, metodo: str = "GET", datos: dict | None = None) -> dict:
    solicitud = urllib.request.Request(
        f"https://api.github.com{ruta}",
        data=json.dumps(datos).encode() if datos is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "business-sales-analytics"},
        method=metodo,
    )
    with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
        return json.load(respuesta)


def main() -> None:
    credencial = comando("git", "credential", "fill", entrada="protocol=https\nhost=github.com\n\n")
    campos = dict(linea.split("=", 1) for linea in credencial.splitlines() if "=" in linea)
    token = campos.get("password")
    if not token:
        raise RuntimeError("No se encontró una credencial HTTPS de GitHub.")
    usuario = api("/user", token)["login"]
    try:
        repo = api(f"/repos/{usuario}/{NOMBRE}", token)
        if not repo.get("empty", False) and repo.get("size", 0) > 0:
            raise RuntimeError(f"El repositorio https://github.com/{usuario}/{NOMBRE} ya tiene contenido; revise antes de subir.")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise RuntimeError(f"GitHub no permitió consultar el repositorio (HTTP {exc.code}).") from None
        try:
            repo = api("/user/repos", token, "POST", {"name": NOMBRE, "private": False,
                        "description": "Análisis reproducible de ventas y rentabilidad de retail chileno con datos sintéticos."})
        except urllib.error.HTTPError as create_error:
            raise RuntimeError(f"GitHub no permitió crear el repositorio (HTTP {create_error.code}).") from None
    url = repo["html_url"]
    if not comando("git", "remote"):
        comando("git", "remote", "add", "origin", f"{url}.git")
    comando("git", "push", "-u", "origin", "main")
    print(url)


if __name__ == "__main__":
    main()
