from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
import pandas as pd
import yfinance as yf

from rendimiento_bachoco.config import TICKERS_YAHOO


def download_finance_data(
    output_dir: Path,
    tickers: list[str] = TICKERS_YAHOO,
    period: str = "max",
) -> None:
    """
    Downloads historical data from Yahoo Finance for each ticker and saves it
    as a parquet file per ticker inside output_dir, alongside a .txt metadata file.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []

    for ticker in tickers:
        logger.info(f"\tDescargando {ticker} de Yahoo Finance...")
        data = yf.Ticker(ticker).history(period=period)
        if data.empty:
            logger.warning(f"\tYahoo Finance no retorno datos para {ticker}, ignorando...")
            failed.append(ticker)
            continue

        output_path = output_dir / f"{ticker.replace('.', '_')}.parquet"
        data.to_parquet(output_path)

        dtypes_str = "\n".join(f"  {col}: {dtype}" for col, dtype in data.dtypes.items())
        metadata = (
            f"Fuente: Yahoo Finance (yfinance)\n"
            f"Fecha de descarga (UTC): {datetime.now(timezone.utc).isoformat()}\n"
            f"Ticker: {ticker}\n"
            f"Periodo solicitado: {period}\n"
            f"Filas descargadas: {len(data)}\n"
            f"Fecha inicio: {data.index.min()}\n"
            f"Fecha fin: {data.index.max()}\n"
            f"Zona horaria: {str(data.index.tz)}\n"
            f"Auto-ajustado por dividendos y splits: Sí (auto_adjust=True por defecto)\n"
            f"Archivo de datos: {output_path.name}\n"
            f"\nColumnas y tipos de datos:\n{dtypes_str}\n"
            f"\nDescripción de columnas:\n"
            f"  Date: Fecha de la sesión bursátil (índice)\n"
            f"  Open: Precio de apertura (MXN)\n"
            f"  High: Precio máximo del día (MXN)\n"
            f"  Low: Precio mínimo del día (MXN)\n"
            f"  Close: Precio de cierre (MXN)\n"
            f"  Volume: Volumen de acciones operadas\n"
            f"  Dividends: Dividendos pagados ese día (MXN)\n"
            f"  Stock Splits: Factor de división de acciones\n"
        )
        output_path.with_suffix(".txt").write_text(metadata, encoding="utf-8")
        logger.success(f"\t{ticker} guardado en {output_path}")

    if len(failed) == len(tickers):
        raise ValueError("Yahoo Finance no retorno datos para ningun ticker.")


def process_finance_data(
    input_dir: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    parquets = list(input_dir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"No se encontraron archivos .parquet en {input_dir}")

    frames = []
    for path in parquets:
        df = pd.read_parquet(path)
        df.index = df.index.tz_convert(None)
        df["ticker"] = path.stem.replace("_", ".", 1)
        frames.append(df[["Close", "ticker"]])

    largo_diario = pd.concat(frames).sort_index()

    mensual = (
        largo_diario.groupby("ticker")
        .resample("ME")["Close"]
        .last()
        .reset_index()
        .rename(columns={"Date": "mes", "Close": "cierre"})
    )
    mensual["rendimiento"] = mensual.groupby("ticker")["cierre"].pct_change()

    rendimiento = mensual.pivot(index="mes", columns="ticker", values="rendimiento")
    rendimiento.columns.name = None

    rendimiento.to_parquet(output_dir / "rendimiento_mensual.parquet")

    metadata = (
        f"Fecha de procesamiento (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"Fuente: {input_dir}\n"
        f"Tickers procesados: {', '.join(sorted(mensual['ticker'].unique()))}\n"
        f"Periodo: {mensual['mes'].min()} → {mensual['mes'].max()}\n"
        f"\nArchivo generado:\n"
        f"  rendimiento_mensual.parquet: formato ancho (mes x ticker), rendimiento mensual\n"
        f"\nNotas:\n"
        f"  Resampleo: último cierre del mes (resample='ME', agg='last')\n"
        f"  Rendimiento: (cierre_t / cierre_{{t-1}}) - 1, por ticker\n"
        f"  Zona horaria: eliminada con tz_convert(None)\n"
        f"  Meses sin operaciones: NaN\n"
    )
    (output_dir / "rendimiento_mensual.txt").write_text(metadata, encoding="utf-8")
    logger.success(f"\tProcesamiento completado: {output_dir}")
