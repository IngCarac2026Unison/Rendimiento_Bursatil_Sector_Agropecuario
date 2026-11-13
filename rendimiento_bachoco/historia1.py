"""Historia de datos 1: regenera las figuras de "¿Quién paga el maíz caro?"."""

from loguru import logger
import matplotlib.pyplot as plt
import pandas as pd
import typer

from rendimiento_bachoco.config import FIGURES_DIR, PROCESSED_DATA_DIR
from rendimiento_bachoco.plots import (
    grafica_tortilla_cadena,
    grafica_tortillas_cadena_comparadas,
    guardar_figura,
)

app = typer.Typer()

ANIO_INICIAL, ANIO_FINAL = 2018, 2025


def cargar_cadena() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DATA_DIR / "cadena_maiz_anual.csv").set_index("anio")


@app.command()
def main() -> None:
    cadena = cargar_cadena()
    precios = {
        a: tuple(float(cadena.loc[a, c]) for c in ("productor", "mayorista", "tortilla"))
        for a in (ANIO_INICIAL, ANIO_FINAL)
    }

    for anio, (p, m, t) in precios.items():
        fig, ax = plt.subplots(figsize=(7, 5.2), facecolor="#fbf6ea")
        grafica_tortilla_cadena(anio, p, m, t, ax=ax)
        guardar_figura(fig, f"historia1_tortilla_cadena_{anio}", svg=True)
        plt.close(fig)

    fig = grafica_tortillas_cadena_comparadas(precios)
    guardar_figura(fig, "historia1_tortilla_cadena_comparadas", svg=True)
    plt.close(fig)

    logger.success(f"Figuras en {FIGURES_DIR}")


if __name__ == "__main__":
    app()
