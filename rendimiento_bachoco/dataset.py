from pathlib import Path
from typing import Callable, List

from loguru import logger
from tqdm import tqdm
import typer
import yfinance as yf

from rendimiento_bachoco.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, INEGI_API_KEY
import urllib.request
import json

app = typer.Typer()


def download_finance_data(
    output_path: Path,
    ticker: str = "GRUMAB.MX",
    period: str = "1mo",
) -> None:
    """
    Download the data from YAHOO Finance and save it to the output path.
    """
    logger.info(f"Downloading {ticker} from YAHOO Finance to {output_path}...")

    data = yf.Ticker(ticker).history(period=period)
    if data.empty:
        raise ValueError(f"YAHOO Finance returned no data for {ticker}")

    data.to_csv(output_path)
    logger.success(f"YAHOO Finance data downloaded successfully: {output_path}")


def download_inegi_metadata(
        state_dict_url: str = 'https://inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/CL_GEO_AREA/0/es/BISE/2.0/' + str(INEGI_API_KEY) + '?type=json'
):
    state_dict_dst = RAW_DATA_DIR / 'MX_state_dict.json'


    if not state_dict_dst.exists():
        urllib.request.urlretrieve(state_dict_url, state_dict_dst)

    stateDict = dict()

    with state_dict_dst.open('r') as fp:
        stateList = json.load(fp)['CODE']
        for s in stateList:
            stateDict[s['value']] = s['Description']
        # for i in range(0, len(stateList)):
        #     stateDict[stateList[i]['value']] = stateList[i]['Description']

    # Delete 'Otros estados', 'Extranjero' and 'No especificada'
    del stateDict['35']
    del stateDict['36']
    del stateDict['39']

    return stateDict

def download_inegi_data(
        data_root : Path,
        indicators: List[str],
        stateDict: dict
):
    for indicator in indicators:
        for sCode in stateDict.keys():

            dest_dir = data_root / 'INEGI' / indicator
            # if not dest_dir.exists():
            Path.mkdir(dest_dir, parents = True, exist_ok = True)

            # TODO: Replace API key
            src = 'https://inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/' + indicator + '/es/' + sCode + '/false/BISE/2.0/' + INEGI_API_KEY + '?type=json'
            dst_file = sCode + '.json'

            if not Path(dst_file).exists():
                urllib.request.urlretrieve(src, dest_dir / dst_file)

@app.command()
def main() -> None:

    # Git doesn't track empty folders, so make sure the data folders exist.
    for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    # Each entry is "name of the task": function with no arguments.
    # To add a new source, write its download function and add one line here.
    download_raw_data: dict[str, Callable[[], None]] = {
        "Finance data (YAHOO Finance)": lambda: download_finance_data(
            RAW_DATA_DIR / "rendimiento_acciones.csv"
        ),
        "INEGI-Indicators": lambda: download_inegi_data(
            RAW_DATA_DIR,
            indicators = ['6207095719'],
            stateDict = download_inegi_metadata()
        )
        # "Other source": lambda: download_other_source(RAW_DATA_DIR / "other_source.csv"),
    }

    logger.info("Downloading raw data...")
    failed: list[str] = []

    for name, download in tqdm(
        download_raw_data.items(),
        total=len(download_raw_data),
        desc="Downloads",
    ):
        try:
            download()
        except Exception:
            # One failing source shouldn't stop the rest.
            logger.exception(f"Download failed: {name}")
            failed.append(name)

    if failed:
        logger.error(f"{len(failed)} download(s) failed: {', '.join(failed)}")
        raise typer.Exit(code=1)

    logger.success("All downloads complete.")





if __name__ == "__main__":
    app()