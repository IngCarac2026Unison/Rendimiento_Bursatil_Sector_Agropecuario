from pathlib import Path

from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

from rendimiento_bachoco.sources.profeco import ESTADOS

PRECIO_MIN = 5.0
PRECIO_MAX = 60.0


def _sin_duplicados(df: pd.DataFrame) -> bool:
    return not df.duplicated(["fecha", "nivel", "estado", "giro"]).any()


def _estado_consistente(df: pd.DataFrame) -> bool:
    return bool(
        df.loc[df["nivel"] == "nacional", "estado"].isna().all()
        and df.loc[df["nivel"] == "estado", "estado"].notna().all()
    )


def _cuantiles_ordenados(df: pd.DataFrame) -> bool:
    return bool(
        (df["precio_p25"] <= df["precio_mediana_mxn_kg"]).all()
        and (df["precio_mediana_mxn_kg"] <= df["precio_p75"]).all()
    )


profeco_schema = DataFrameSchema(
    columns={
        "fecha": Column(
            "datetime64[ns]",
            Check(lambda s: s.dt.is_month_start, error="La fecha debe ser el primer día del mes"),
        ),
        "nivel": Column(str, Check.isin(["nacional", "estado"])),
        "estado": Column(str, Check.isin(ESTADOS), nullable=True),
        "giro": Column(str, Check.isin(["tortilleria", "autoservicio"])),
        "precio_mediana_mxn_kg": Column(
            float,
            Check.in_range(
                PRECIO_MIN, PRECIO_MAX, error=f"Mediana fuera de {PRECIO_MIN}-{PRECIO_MAX} MXN/kg"
            ),
            nullable=False,
        ),
        "precio_p25": Column(float, Check.gt(0), nullable=False),
        "precio_p75": Column(float, Check.gt(0), nullable=False),
        "n_registros": Column(int, Check.gt(0)),
        "n_establecimientos": Column(int, Check.gt(0)),
    },
    checks=[
        Check(_sin_duplicados, error="Hay duplicados en (fecha, nivel, estado, giro)"),
        Check(_estado_consistente, error="`estado` debe ser nulo solo en el nivel nacional"),
        Check(_cuantiles_ordenados, error="Se esperaba p25 <= mediana <= p75"),
    ],
    strict=True,
)


def _reportar_meses_faltantes(df: pd.DataFrame) -> None:
    nacional = df[df["nivel"] == "nacional"]
    for giro, g in nacional.groupby("giro"):
        presentes = set(g["fecha"])
        for year in range(g["fecha"].min().year, g["fecha"].max().year + 1):
            esperados = set(pd.date_range(f"{year}-01-01", f"{year}-12-01", freq="MS"))
            faltan = sorted(esperados - presentes)
            if faltan:
                meses = ", ".join(str(m.month) for m in faltan)
                logger.warning(f"\t{giro} {year}: faltan {len(faltan)} meses (meses {meses})")


def _reportar_atipicos(df: pd.DataFrame) -> None:
    q1, q3 = df["precio_mediana_mxn_kg"].quantile([0.25, 0.75])
    fuera = df[df["precio_mediana_mxn_kg"] > q3 + 3 * (q3 - q1)]
    if len(fuera):
        logger.warning(
            f"\t{len(fuera)} medianas atípicas (> Q3 + 3 RIC) en {df['giro'].nunique()} giros"
        )


def validate_profeco(path: Path) -> None:
    df = pd.read_csv(path, parse_dates=["fecha"])
    df["fecha"] = df["fecha"].astype("datetime64[ns]")
    profeco_schema.validate(df)

    estados = set(df.loc[df["nivel"] == "estado", "estado"])
    if len(estados) != len(ESTADOS):
        logger.warning(
            f"\tSolo hay {len(estados)} de {len(ESTADOS)} estados: {sorted(set(ESTADOS) - estados)}"
        )
    _reportar_meses_faltantes(df)
    _reportar_atipicos(df)

    logger.success(f"\tEsquema de precio de tortilla validado: {path}")
