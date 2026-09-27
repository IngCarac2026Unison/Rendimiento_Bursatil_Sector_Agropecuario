from pathlib import Path

from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

from rendimiento_bachoco.config import TICKERS_YAHOO

# Ruido de punto flotante del ajuste por dividendos/splits de yfinance.
_PRICE_EPS = 1e-6

finance_raw_schema = DataFrameSchema(
    columns={
        "Open": Column(float, Check.gt(0)),
        "High": Column(float, Check.gt(0)),
        "Low": Column(float, Check.gt(0)),
        "Close": Column(float, Check.gt(0)),
        "Volume": Column(int, Check.ge(0)),
        "Dividends": Column(float, Check.ge(0)),
        "Stock Splits": Column(float, Check.ge(0)),
    },
    checks=[
        # Pandera no valida bien dtypes tz-aware, se checa con pandas.
        Check(
            lambda df: isinstance(df.index, pd.DatetimeIndex),
            error="El índice debe ser de fechas (DatetimeIndex)",
        ),
        Check(lambda df: df.index.is_unique, error="El índice de fechas tiene duplicados"),
        Check(
            lambda df: df.index.is_monotonic_increasing,
            error="El índice de fechas no está ordenado de forma creciente",
        ),
        Check(lambda df: df["High"] >= df["Low"] - _PRICE_EPS, error="High debe ser >= Low"),
        Check(lambda df: df["High"] >= df["Open"] - _PRICE_EPS, error="High debe ser >= Open"),
        Check(lambda df: df["Low"] <= df["Open"] + _PRICE_EPS, error="Low debe ser <= Open"),
        # Close puede caer fuera de [Low, High] en días ex-dividendo (factor de
        # ajuste distinto al de O/H/L en yfinance): advertencia, no error duro.
        Check(
            lambda df: df["High"] >= df["Close"] - _PRICE_EPS,
            error="High debe ser >= Close",
            raise_warning=True,
        ),
        Check(
            lambda df: df["Low"] <= df["Close"] + _PRICE_EPS,
            error="Low debe ser <= Close",
            raise_warning=True,
        ),
    ],
    strict=False,
)

finance_monthly_schema = DataFrameSchema(
    columns={
        ticker: Column(float, Check.gt(-1), nullable=True) for ticker in TICKERS_YAHOO
    },
    checks=[
        Check(
            lambda df: isinstance(df.index, pd.DatetimeIndex),
            error="El índice debe ser de fechas (DatetimeIndex)",
        ),
        Check(lambda df: df.index.is_unique, error="El índice de meses tiene duplicados"),
        Check(
            lambda df: df.index.is_monotonic_increasing,
            error="El índice de meses no está ordenado de forma creciente",
        ),
        *(
            Check(
                lambda df, t=ticker: not df[t].isna().all(),
                error=f"La columna {ticker} está completamente vacía",
            )
            for ticker in TICKERS_YAHOO
        ),
    ],
    strict=True,
)


def validate_finance_raw(raw_dir: Path) -> None:
    parquets = list(raw_dir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"No se encontraron archivos .parquet en {raw_dir}")

    for path in parquets:
        df = pd.read_parquet(path)
        finance_raw_schema.validate(df)

    logger.success(f"\tEsquema de datos crudos validado: {len(parquets)} archivo(s) en {raw_dir}")


def validate_finance_monthly(monthly_path: Path) -> None:
    df = pd.read_parquet(monthly_path)
    finance_monthly_schema.validate(df)

    logger.success(f"\tEsquema de rendimiento mensual validado: {monthly_path}")
