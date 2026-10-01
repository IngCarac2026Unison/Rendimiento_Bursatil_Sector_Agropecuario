from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
import requests


def download_sniim_data(
    output_path: Path,
    market_code: str = "100",
    market_name: str = "Iztapalapa",
) -> None:

    logger.success(f"\tDescargando maíz blanco de {market_name}...")

    url = (
        "http://www.economia-sniim.gob.mx/"
        "SNIIM-AN/estadisticas/anuariosgran1.asp"
    )

    if output_path.exists():
        logger.info(f'Requerimiento SNIIM previamente satisfecho: {output_path}')
        return
    
    response = requests.post(
        url,
        data={
            "cent": market_code,
            "prod": "OMABLAN",
            "ACCION": "Aceptar",
        },
        timeout=60,
    )
    response.raise_for_status()

    if market_name not in response.text or "2013" not in response.text:
        raise ValueError(f"El SNIIM no devolvió la tabla esperada de {market_name}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    metadata = (
        "Fuente: Sistema Nacional de Información e Integración de Mercados (SNIIM)\n"
        f"URL de consulta: {url}\n"
        f"URL de respuesta: {response.url}\n"
        f"Fecha de descarga (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"Mercado: {market_name}\n"
        f"Código del mercado: {market_code}\n"
        "Producto: Maíz blanco (OMABLAN)\n"
        "Unidad: Pesos mexicanos por kilogramo\n"
        "Frecuencia: Promedios mensuales\n"
        "Contenido: Tabla histórica original en formato HTML, sin filtrar años.\n"
        "Origen: Procedencia del producto; distinto de la ubicación del mercado.\n"
        "Valores faltantes: Las celdas vacías no representan precios de cero.\n"
        f"Archivo de datos: {output_path.name}\n"
    )
    output_path.with_suffix(".txt").write_text(metadata, encoding="utf-8")

    logger.success(f"\tTabla SNIIM guardada en: {output_path}")
    
