import json
from datetime import datetime
from pathlib import Path
from typing import List
import urllib.request
import pandas as pd

from loguru import logger

from rendimiento_bachoco.config import INEGI_API_KEY, RAW_DATA_DIR, PROCESSED_DATA_DIR, REFERENCES_DIR, INTERIM_DATA_DIR


def url_call(url: str, dst: Path):
    try:
        if not dst.exists():
            urllib.request.urlretrieve(url, dst)
        else: 
            logger.info(f'Requerimiento de descarga previamente satisfecho: {dst}')

    except urllib.error.HTTPError as e:
        raise ValueError(e)


def get_state_dict():

    dict_url: str = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/CL_GEO_AREA/0/es/BISE/2.0/{str(INEGI_API_KEY)}?type=json'
    dict_dir = REFERENCES_DIR / 'INEGI'
    dict_dst = dict_dir / 'MX_state_dict.json'

    Path.mkdir(dict_dir, parents = True, exist_ok = True)
    url_call(dict_url, dict_dst)

    stateDict = dict()

    with dict_dst.open('r') as fp:
        stateList = json.load(fp)['CODE']
        for s in stateList:
            stateDict[s['value']] = s['Description']

    # Delete 'Otros estados', 'Extranjero' and 'No especificada'
    del stateDict['35']
    del stateDict['36']
    del stateDict['39']

    return stateDict


# Done like this because INEGI API does not authorize batch calls.
def download_inegi_data(
        data_root : Path,
        indicators: List[str]
):

    stateDict: dict = get_state_dict()

    by_state_indicators = ['6207095692', '6207095719']

    data_arg = 'INDICATOR'
    meta_arg = 'CL_INDICATOR'

    meta_dst_dir = REFERENCES_DIR / 'INEGI' / 'METADATA'

    logger.info("\tDescargando datos del INEGI...")

    for indicator in indicators:

        Path.mkdir(meta_dst_dir, parents = True, exist_ok = True)
        meta_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{meta_arg}/{indicator}/es/BISE/2.0/{str(INEGI_API_KEY)}?type=json'
        meta_dst = meta_dst_dir / (indicator + '.json')
        url_call(meta_src, meta_dst)

        if indicator in by_state_indicators:
            for sCode in stateDict.keys():

                dest_dir = data_root / 'INEGI' / indicator
                Path.mkdir(dest_dir, parents = True, exist_ok = True)
                data_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{data_arg}/{indicator}/es/{sCode}/false/BISE/2.0/{INEGI_API_KEY}?type=json'
                data_dst = dest_dir / (sCode + '.json')

                try:
                    url_call(data_src, data_dst)

                except urllib.error.HTTPError as e:
                    if e.code == 400:
                        logger.error(f'\tError: {e}. Verifica que el indicador tenga información por estado. Se omite el indicador.')
                        break
        else:
            dest_dir = data_root / 'INEGI' / indicator
            Path.mkdir(dest_dir, parents = True, exist_ok = True)
            data_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{data_arg}/{indicator}/es/0/false/BISE/2.0/{INEGI_API_KEY}?type=json'
            data_dst = dest_dir / '0.json'
            try:
                url_call(data_src, data_dst)
            except urllib.error.HTTPError as e:
                raise(e)

    log_text = f'''
        Datos del INEGI descargados el {datetime.now()}. Indicadores:
        {[f'{x}' for x in indicators]}
    '''
    text_log_id = logger.add(meta_dst_dir / "inegi_log.txt")
    logger.info(log_text)
    logger.remove(text_log_id)

def process_inegi_data(
        inegi_raw_dir : Path,
        inegi_tidy_dir : Path,
        indicators
):
    def read_inegi(dfs: List[pd.DataFrame], filepath : Path, indicator : str):
        if path_file.is_file():
            with open(path_file, "r", encoding = "utf-8") as fp:
                data  = json.load(fp)
                df = pd.json_normalize(
                    data,
                    record_path="Series",
                )
                df["Indicator"] = indicator
                dfs.append(df)
    

    # METADATA
    dfs = []
    for path in (REFERENCES_DIR / "INEGI" / "METADATA").iterdir():
        if path.is_file() and path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # Normalize the nested 'CODE' list into rows
            df = pd.json_normalize(
                data,
                record_path="CODE",
                meta=["id", "agencyID", "version", "lang"],
            )
            df["indicator"] = path.stem
            dfs.append(df)

    inegi_meta_df = pd.concat(dfs, ignore_index=True)
    inegi_meta_df = inegi_meta_df.drop(columns = ["id", "agencyID", "version", "lang", "indicator"], errors = 'ignore')
    inegi_meta_df = inegi_meta_df.rename(columns = {"value": "Indicador", "Description": "Descripcion"})
    inegi_meta_df.to_csv(INTERIM_DATA_DIR / 'inegi_metadata.csv')



    # DATA
    dfs = []
    state_dict = get_state_dict()
    by_state_indicators = ['6207095692', '6207095719']

    for indicator in inegi_meta_df['Indicador']:
        path_dir = (RAW_DATA_DIR / "INEGI" / indicator)
        if indicator in by_state_indicators:
            for sCode in state_dict.keys():
                path_file = path_dir / (sCode + ".json")
                read_inegi(dfs = dfs, filepath = path_file, indicator = indicator)
        else:
            path_file = path_dir / ("0.json")
            read_inegi(dfs = dfs, filepath = path_file, indicator = indicator)

    inegi_data_df = pd.concat(dfs, ignore_index=True)
    exploded_df = inegi_data_df.explode("OBSERVATIONS").reset_index(drop=True)
    observations_json = exploded_df["OBSERVATIONS"]
    obs_df = pd.json_normalize(observations_json)
    inegi_data_expanded = exploded_df.drop(columns=["OBSERVATIONS"]).join(obs_df)
    inegi_data_expanded = inegi_data_expanded.drop(columns = ['OBS_EXCEPTION', 'STATUS', 'OBS_SOURCE', 'OBS_NOTE', 'Indicator'], errors = 'ignore')
    inegi_data_expanded['TIME_PERIOD'] =  pd.to_datetime(inegi_data_expanded['TIME_PERIOD'], format ='mixed', yearfirst = True)
    inegi_data_expanded['LASTUPDATE'] =  pd.to_datetime(inegi_data_expanded['LASTUPDATE'], format ='mixed', dayfirst = True)
    inegi_data_expanded['TOPIC'] = inegi_data_expanded['TOPIC'].astype('int')
    inegi_data_expanded['OBS_VALUE'] = inegi_data_expanded['OBS_VALUE'].astype('float')
    inegi_data_expanded['COBER_GEO'] = inegi_data_expanded['COBER_GEO'].astype('int')
    inegi_data_expanded.to_csv(INTERIM_DATA_DIR / "inegi_data.csv")

    