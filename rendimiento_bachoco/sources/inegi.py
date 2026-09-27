import json
from datetime import datetime
from pathlib import Path
from typing import List
import urllib.request

from loguru import logger

from rendimiento_bachoco.config import INEGI_API_KEY, RAW_DATA_DIR


def url_call(url: str, dst: Path):
    try:
        if not dst.exists():
            urllib.request.urlretrieve(url, dst)

    except urllib.error.HTTPError as e:
        raise ValueError(e)


def get_state_dict():

    dict_url: str = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/CL_GEO_AREA/0/es/BISE/2.0/{str(INEGI_API_KEY)}?type=json'
    dict_dir = RAW_DATA_DIR / 'INEGI' / 'MX_state_dict.json'
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

    meta_dst_dir = Path(RAW_DATA_DIR / 'INEGI' / 'METADATA')

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
