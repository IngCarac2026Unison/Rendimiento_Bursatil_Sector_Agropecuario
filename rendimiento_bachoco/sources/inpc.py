from datetime import UTC, datetime
import json
from pathlib import Path

from loguru import logger
import pandas as pd
import requests

from rendimiento_bachoco.config import INEGI_API_KEY

INPC_API_URL = (
    "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
    "INDICATOR/{id}/es/00/false/BIE-BISE/2.0/{token}?type=json"
)
INPC_BASE = "2a quincena de julio de 2018 = 100"
INPC_START = "2013-01-01"

# clave de la serie en el archivo tidy -> (ID del indicador en el API, título)
INPC_INDICADORES: dict[str, tuple[str, str]] = {
    "general": ("910392", "INPC, índice general, nacional, mensual"),
}


def download_inpc(output_dir: Path, indicadores: dict[str, tuple[str, str]]) -> None:
    logger.info("\tDescargando INPC del INEGI...")
    if not INEGI_API_KEY:
        raise ValueError("Falta INEGI_API_KEY en el entorno (.env).")

    output_dir.mkdir(parents=True, exist_ok=True)
    for clave, (indicador, titulo) in indicadores.items():
        dst = output_dir / f"{clave}.json"
        if dst.exists():
            logger.info(f"Requerimiento INPC previamente satisfecho: {dst}")
            continue

        try:
            response = requests.get(
                INPC_API_URL.format(id=indicador, token=INEGI_API_KEY), timeout=60
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            # El mensaje original incluye la URL con el token.
            raise ValueError(
                f"Falló la consulta del indicador {indicador}: {type(exc).__name__}"
            ) from None
        payload = response.json()
        if not isinstance(payload, dict) or "Series" not in payload:
            raise ValueError(f"Respuesta inesperada del INEGI para el indicador {indicador}.")

        dst.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        metadata = (
            "Fuente: INEGI, Banco de Información Económica (BIE), API de Indicadores\n"
            f"Indicador: {indicador} ({titulo})\n"
            f"URL: {INPC_API_URL.format(id=indicador, token='<TOKEN>')}\n"
            f"Fecha de descarga (UTC): {datetime.now(UTC).isoformat()}\n"
            f"Base del índice: {INPC_BASE}\n"
            "Frecuencia: Mensual; cobertura nacional\n"
            f"Archivo de datos: {dst.name}\n"
        )
        dst.with_suffix(".txt").write_text(metadata, encoding="utf-8")
        logger.success(f"\tINPC {clave} guardado en: {dst}")


def _leer_serie(path: Path, clave: str) -> pd.DataFrame:
    obs = json.loads(path.read_text(encoding="utf-8"))["Series"][0]["OBSERVATIONS"]
    df = pd.DataFrame(obs)[["TIME_PERIOD", "OBS_VALUE"]]
    return pd.DataFrame(
        {
            "fecha": pd.to_datetime(df["TIME_PERIOD"], format="%Y/%m"),
            "serie": clave,
            "indice": pd.to_numeric(df["OBS_VALUE"]),
        }
    )


def process_inpc(raw_dir: Path, output_path: Path) -> None:
    logger.info("Procesando INPC del INEGI...")

    partes = []
    for clave in INPC_INDICADORES:
        s = _leer_serie(raw_dir / f"{clave}.json", clave).sort_values("fecha")
        s = s.drop_duplicates("fecha").reset_index(drop=True)
        # Las variaciones se calculan sobre la serie completa y luego se recorta.
        s = s.set_index("fecha").asfreq("MS")
        s["serie"] = clave
        s["var_mensual_pct"] = (s["indice"].pct_change(1, fill_method=None) * 100).round(4)
        s["var_anual_pct"] = (s["indice"].pct_change(12, fill_method=None) * 100).round(4)
        partes.append(s.reset_index().loc[lambda d: d["fecha"] >= INPC_START])

    tidy = pd.concat(partes, ignore_index=True)[
        ["fecha", "serie", "indice", "var_mensual_pct", "var_anual_pct"]
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(output_path, index=False)

    logger.success(f"INPC mensual guardado en: {output_path}")
