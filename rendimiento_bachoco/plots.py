"""Gráficas de la historia de datos: la tortilla partida por eslabón de la cadena del maíz."""

from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse, Polygon
import matplotlib.pyplot as plt
import numpy as np

from rendimiento_bachoco.config import FIGURES_DIR

# Paleta: maíz cocido, comal y tinta; un color por eslabón
FONDO = "#fbf6ea"
MAIZ = "#ecc97e"
MAIZ_BORDE = "#c99a4b"
TINTA = "#3b2f24"
TINTA_SUAVE = "#7a6a58"
ESLABONES = {
    "productor": ("#3f8f4f", "#16381c"),
    "mayorista": ("#c9913d", "#5a3a0c"),
    "tortilla": ("#c0392b", "#4a110b"),
}
ETIQUETAS = {
    "productor": "Productor",
    "mayorista": "Margen mayorista",
    "tortilla": "Tortillería y resto",
}


def guardar_figura(
    fig: Figure, nombre: str, carpeta: Path = FIGURES_DIR, svg: bool = False
) -> None:
    """Guarda la figura como PNG (200 dpi) y, opcionalmente, como SVG."""
    carpeta.mkdir(parents=True, exist_ok=True)
    fig.savefig(carpeta / f"{nombre}.png", dpi=200, bbox_inches="tight", facecolor=FONDO)
    if svg:
        fig.savefig(carpeta / f"{nombre}.svg", bbox_inches="tight", facecolor=FONDO)


def _borde_irregular(rng: np.random.Generator, n: int = 720) -> tuple[np.ndarray, np.ndarray]:
    """Ángulos (grados desde las 12, en sentido horario) y radios con un borde ligeramente irregular."""
    ang = np.linspace(0, 360, n, endpoint=False)
    t = np.radians(ang)
    r = np.ones(n)
    for k in (2, 3, 5, 8):
        r += rng.normal(0, 0.012 / k**0.3) * np.sin(k * t + rng.uniform(0, 2 * np.pi))
    return ang, r


def _manchas(
    rng: np.random.Generator, n: int = 70
) -> list[tuple[float, float, float, float, float]]:
    """Manchas tostadas de comal: (x, y, ancho, alto, ángulo)."""
    rad = 0.93 * np.sqrt(rng.uniform(0, 1, n))
    t = rng.uniform(0, 2 * np.pi, n)
    return [
        (
            r * np.cos(a),
            r * np.sin(a),
            rng.uniform(0.05, 0.17),
            rng.uniform(0.03, 0.10),
            rng.uniform(0, 180),
        )
        for r, a in zip(rad, t, strict=True)
    ]


def grafica_tortilla_cadena(
    anio: int,
    productor: float,
    mayorista: float,
    tortilla: float,
    ax: Axes | None = None,
    semilla: int = 7,
    escala: float = 1.0,
) -> Axes:
    """Tortilla partida en el precio por kilo del productor, el margen mayorista y el resto hasta la tortilla."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5.2), facecolor=FONDO)
    rng = np.random.default_rng(semilla)
    ang, r = _borde_irregular(rng)
    manchas = _manchas(rng)
    ang_c, r_c = np.append(ang, 360.0), np.append(r, r[0])

    def punto(a: float) -> np.ndarray:
        rad = np.interp(a, ang_c, r_c)
        return np.array([np.sin(np.radians(a)), np.cos(np.radians(a))]) * rad

    tramos = {
        "productor": productor,
        "mayorista": mayorista - productor,
        "tortilla": tortilla - mayorista,
    }
    inicio = 0.0
    for clave, valor in tramos.items():
        fin = inicio + valor / tortilla * 360
        color, mancha = ESLABONES[clave]
        medio = np.radians((inicio + fin) / 2)
        direccion = np.array([np.sin(medio), np.cos(medio)])
        dentro = (ang > inicio) & (ang < fin)
        vertices = np.vstack(
            [
                [0, 0],
                punto(inicio),
                np.column_stack(
                    [
                        np.sin(np.radians(ang[dentro])) * r[dentro],
                        np.cos(np.radians(ang[dentro])) * r[dentro],
                    ]
                ),
                punto(fin),
            ]
        )
        delta = direccion * 0.05 * escala
        poligono = Polygon(
            vertices * escala + delta,
            closed=True,
            facecolor=color,
            edgecolor=FONDO,
            lw=2.4,
            joinstyle="round",
        )
        ax.add_patch(poligono)
        for mx, my, w, h, a in manchas:
            e = Ellipse(
                (mx * escala + delta[0], my * escala + delta[1]),
                w * escala,
                h * escala,
                angle=a,
                facecolor=mancha,
                alpha=0.3,
                lw=0,
            )
            ax.add_patch(e)
            e.set_clip_path(poligono)
        ancla = direccion * (1.16 * escala) + delta
        ax.text(
            ancla[0],
            ancla[1],
            f"{ETIQUETAS[clave]}\n${valor:.2f} · {valor / tortilla * 100:.0f} %",
            ha="left" if direccion[0] >= 0 else "right",
            va="bottom" if direccion[1] >= 0.2 else ("top" if direccion[1] <= -0.2 else "center"),
            fontsize=11,
            fontweight="bold",
            color=TINTA,
            linespacing=1.3,
        )
        inicio = fin

    ax.text(
        -2.4,
        1.5 * escala + 0.75,
        f"{anio}",
        ha="left",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=TINTA,
    )
    ax.text(
        -2.4,
        1.5 * escala + 0.45,
        f"1 kg de tortilla = ${tortilla:.2f}",
        ha="left",
        va="center",
        fontsize=12,
        color=TINTA_SUAVE,
    )
    ax.set_xlim(-2.5, 2.7)
    ax.set_ylim(-1.3 * escala, 1.5 * escala + 1.0)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def grafica_tortillas_cadena_comparadas(datos: dict[int, tuple[float, float, float]]) -> Figure:
    """Una tortilla por año con área proporcional al precio del kilo; datos: año a (productor, mayorista, tortilla)."""
    base = min(v[2] for v in datos.values())
    fig, axes = plt.subplots(1, len(datos), figsize=(6.4 * len(datos), 5.2), facecolor=FONDO)
    for ax, (anio, (p, m, t)) in zip(np.atleast_1d(axes), datos.items(), strict=True):
        grafica_tortilla_cadena(anio, p, m, t, ax=ax, escala=float(np.sqrt(t / base)))
    fig.text(
        0.5,
        0.02,
        "Precios por kilo, pesos corrientes. El área de la tortilla es proporcional a su precio.",
        ha="center",
        fontsize=10,
        color=TINTA_SUAVE,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig
