"""Métricas que cruzan salario mínimo, precio de la tortilla y consumo de los hogares."""

import pandas as pd

HORAS_JORNADA = 8

ENTIDADES = {
    "01": "Aguascalientes",
    "02": "Baja California",
    "03": "Baja California Sur",
    "04": "Campeche",
    "05": "Coahuila",
    "06": "Colima",
    "07": "Chiapas",
    "08": "Chihuahua",
    "09": "Ciudad de México",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "Estado de México",
    "16": "Michoacán",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz",
    "31": "Yucatán",
    "32": "Zacatecas",
}


def _mes(serie: pd.Series) -> pd.Series:
    """Normaliza fechas al primer día del mes."""
    return pd.to_datetime(serie).dt.to_period("M").dt.to_timestamp()


def consumo_hogar_mensual(
    enigh_df: pd.DataFrame,
    inicio: str = "2013-01-01",
    fin: str = "2025-12-01",
    mes_levantamiento: int = 10,
    nivel: str = "nacional",
    clave_nivel: str = "nacional",
) -> pd.DataFrame:
    """Interpola linealmente kg/día y gasto/día por hogar entre levantamientos ENIGH, constantes fuera de ellos."""
    base = enigh_df[
        (enigh_df["nivel"] == nivel) & (enigh_df["clave_nivel"].astype(str) == clave_nivel)
    ]
    base = base.assign(
        fecha=pd.to_datetime(base["anio"].astype(str) + f"-{mes_levantamiento:02d}-01")
    )
    base = base.set_index("fecha")[["kg_dia_hogar", "gasto_dia_hogar_mxn"]].sort_index()
    meses = pd.date_range(inicio, fin, freq="MS")
    out = base.reindex(base.index.union(meses)).interpolate(method="time", limit_area="inside")
    out = out.ffill().bfill().reindex(meses)
    out.index.name = "fecha"
    return out.reset_index()


def _salario_area(salario_df: pd.DataFrame, area: str) -> pd.Series:
    """Salario mínimo diario por mes para un área salarial."""
    s = salario_df[salario_df["area"] == area]
    return pd.Series(
        s["salario_minimo_diario_mxn"].values, index=_mes(s["fecha"]), name="salario_diario"
    )


def _precio_nacional(precio_df: pd.DataFrame, giro: str) -> pd.Series:
    """Precio nacional mensual (MXN/kg) de un giro."""
    p = precio_df[(precio_df["nivel"] == "nacional") & (precio_df["giro"] == giro)]
    return pd.Series(p["precio_mediana_mxn_kg"].values, index=_mes(p["fecha"]), name="precio_kg")


def _metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Añade costo diario del hogar y razones de poder adquisitivo."""
    df = df.copy()
    df["costo_tortilla_dia_hogar"] = df["precio_kg"] * df["kg_dia_hogar"]
    df["pct_salario"] = df["costo_tortilla_dia_hogar"] / df["salario_diario"] * 100
    df["minutos_trabajo_por_kg"] = df["precio_kg"] / (df["salario_diario"] / HORAS_JORNADA) * 60
    df["kg_por_salario"] = df["salario_diario"] / df["precio_kg"]
    return df


def tortilla_salario_mensual(
    salario_df: pd.DataFrame,
    precio_df: pd.DataFrame,
    consumo_df: pd.DataFrame,
    area: str = "general",
    giro: str = "tortilleria",
) -> pd.DataFrame:
    """Métricas mensuales de tortilla frente al salario mínimo, solo en meses con precio observado."""
    precio = _precio_nacional(precio_df, giro)
    salario = _salario_area(salario_df, area)
    consumo = consumo_df.assign(fecha=_mes(consumo_df["fecha"])).set_index("fecha")["kg_dia_hogar"]
    df = pd.concat([precio, salario, consumo.rename("kg_dia_hogar")], axis=1, join="inner")
    df = _metricas(df.dropna()).rename_axis("fecha").reset_index()
    df.insert(1, "area", area)
    df.insert(2, "giro", giro)
    return df


def tortilla_salario_anual(
    salario_df: pd.DataFrame,
    precio_df: pd.DataFrame,
    consumo_df: pd.DataFrame,
    enigh_df: pd.DataFrame,
    area: str = "general",
    giro: str = "tortilleria",
) -> pd.DataFrame:
    """Promedio anual de los meses con precio y versión ENIGH directa (gasto/salario) en años de levantamiento."""
    mensual = tortilla_salario_mensual(salario_df, precio_df, consumo_df, area, giro)
    mensual["anio"] = mensual["fecha"].dt.year
    cols = ["precio_kg", "salario_diario", "kg_dia_hogar", "costo_tortilla_dia_hogar"]
    anual = mensual.groupby("anio").agg(
        n_meses=("fecha", "size"), **{c: (c, "mean") for c in cols}
    )
    anual = _metricas(anual.drop(columns="n_meses")).join(anual["n_meses"])
    sal = _salario_area(salario_df, area)
    sal_anio = sal.groupby(sal.index.year).mean().rename("salario_prom_anio")
    nac = (
        enigh_df[enigh_df["nivel"] == "nacional"]
        .set_index("anio")["gasto_dia_hogar_mxn"]
        .rename("gasto_dia_enigh")
    )
    anual = anual.join(nac, how="outer").join(sal_anio, how="left")
    anual["pct_salario_enigh"] = anual["gasto_dia_enigh"] / anual["salario_prom_anio"] * 100
    anual = anual[anual["salario_prom_anio"].notna()]
    anual.insert(0, "area", area)
    anual.insert(1, "giro", giro)
    return anual.rename_axis("anio").reset_index()


def _precio_anual(precio_df: pd.DataFrame, giro: str, anio: int, nivel: str) -> pd.DataFrame:
    """Promedio anual de la mediana mensual de precio por nivel geográfico."""
    p = precio_df[(precio_df["nivel"] == nivel) & (precio_df["giro"] == giro)].copy()
    p = p[_mes(p["fecha"]).dt.year == anio]
    clave = "estado" if nivel == "estado" else "nivel"
    return p.groupby(clave)["precio_mediana_mxn_kg"].mean().rename("precio_kg").reset_index()


def _salario_anio(salario_df: pd.DataFrame, area: str, anio: int) -> float:
    """Salario mínimo diario promedio de un año."""
    s = _salario_area(salario_df, area)
    return float(s[s.index.year == anio].mean())


def pct_salario_por_decil(
    salario_df: pd.DataFrame,
    precio_df: pd.DataFrame,
    enigh_df: pd.DataFrame,
    anio: int | None = None,
    area: str = "general",
    giro: str = "tortilleria",
) -> pd.DataFrame:
    """Costo diario de tortilla por decil de ingreso como % del salario mínimo, en un año ENIGH."""
    anio = int(enigh_df["anio"].max()) if anio is None else anio
    d = enigh_df[(enigh_df["nivel"] == "decil") & (enigh_df["anio"] == anio)].copy()
    d["decil"] = d["clave_nivel"].astype(int)
    precio = float(_precio_anual(precio_df, giro, anio, "nacional")["precio_kg"].iloc[0])
    salario = _salario_anio(salario_df, area, anio)
    d["anio"], d["precio_kg"], d["salario_diario"] = anio, precio, salario
    d["costo_tortilla_dia_hogar"] = d["kg_dia_hogar"] * precio
    d["pct_salario"] = d["costo_tortilla_dia_hogar"] / salario * 100
    d["pct_salario_enigh"] = d["gasto_dia_hogar_mxn"] / salario * 100
    cols = [
        "anio",
        "decil",
        "kg_dia_hogar",
        "precio_kg",
        "salario_diario",
        "costo_tortilla_dia_hogar",
        "pct_salario",
        "pct_salario_enigh",
    ]
    return d.sort_values("decil")[cols].reset_index(drop=True)


def pct_salario_por_entidad(
    salario_df: pd.DataFrame,
    precio_df: pd.DataFrame,
    enigh_df: pd.DataFrame,
    anio: int | None = None,
    area: str = "general",
    giro: str = "tortilleria",
) -> pd.DataFrame:
    """Costo diario de tortilla por entidad (mediana PROFECO estatal x kg ENIGH estatal) como % del salario mínimo."""
    anio = int(enigh_df["anio"].max()) if anio is None else anio
    e = enigh_df[(enigh_df["nivel"] == "entidad") & (enigh_df["anio"] == anio)].copy()
    e["estado"] = e["clave_nivel"].astype(str).map(ENTIDADES)
    precio = _precio_anual(precio_df, giro, anio, "estado")
    salario = _salario_anio(salario_df, area, anio)
    d = e.merge(precio, on="estado", how="left")
    d["anio"], d["salario_diario"] = anio, salario
    d["costo_tortilla_dia_hogar"] = d["kg_dia_hogar"] * d["precio_kg"]
    d["pct_salario"] = d["costo_tortilla_dia_hogar"] / salario * 100
    cols = [
        "anio",
        "estado",
        "kg_dia_hogar",
        "precio_kg",
        "salario_diario",
        "costo_tortilla_dia_hogar",
        "pct_salario",
    ]
    return d.sort_values("pct_salario", ascending=False)[cols].reset_index(drop=True)


ESLABONES = ("productor", "mayorista", "tortilla")


def cadena_precios_anual(
    dgsiap_df: pd.DataFrame,
    sniim_df: pd.DataFrame,
    tortilla_df: pd.DataFrame,
    rendimiento_df: pd.DataFrame,
    ticker: str = "GRUMAB.MX",
    giro: str = "tortilleria",
    excluir_mercados: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Precios por eslabón (productor, mayorista, tortilla, $/kg), diferencias, participación y rendimiento anual de Gruma."""
    maiz = dgsiap_df.assign(
        volumen=pd.to_numeric(dgsiap_df["Volumenproduccion"], errors="coerce"),
        valor=pd.to_numeric(dgsiap_df["Valorproduccion"], errors="coerce"),
    )
    por_anio = maiz.groupby("Anio")[["volumen", "valor"]].sum()
    productor = (por_anio["valor"] / por_anio["volumen"] / 1000).rename("productor")

    s = sniim_df[~sniim_df["mercado"].isin(excluir_mercados)]
    por_mercado = s.groupby([_mes(s["fecha"]), "mercado"])["precio_mxn_kg"].mean().unstack()
    mensual = por_mercado.median(axis=1)
    mayorista = mensual.groupby(mensual.index.year).mean().rename("mayorista")

    tort = _precio_nacional(tortilla_df, giro)
    tortilla = tort.groupby(tort.index.year).mean().rename("tortilla")
    n_meses = tort.groupby(tort.index.year).size().rename("meses_tortilla")

    rend = rendimiento_df[ticker].dropna()
    gruma = (1 + rend).groupby(rend.index.year).prod().sub(1).rename("rendimiento_gruma")

    df = pd.concat([productor, mayorista, tortilla, n_meses, gruma], axis=1)
    df = df.loc[df["productor"].notna()].rename_axis("anio")
    df["dif_mayorista_productor"] = df["mayorista"] - df["productor"]
    df["dif_tortilla_mayorista"] = df["tortilla"] - df["mayorista"]
    df["dif_tortilla_productor"] = df["tortilla"] - df["productor"]
    df["part_productor_mayorista"] = df["productor"] / df["mayorista"] * 100
    df["part_productor_tortilla"] = df["productor"] / df["tortilla"] * 100
    return df.reset_index()


def transmision_asimetrica(
    cadena_df: pd.DataFrame,
    base: int = 2020,
    pico: int = 2022,
    final: int = 2025,
    eslabones: tuple[str, ...] = ESLABONES,
) -> pd.DataFrame:
    """Cambio de cada eslabón en la subida (base a pico) y en la bajada (pico a final), en $/kg y %."""
    c = cadena_df.set_index("anio")
    filas = []
    for e in eslabones:
        v0, v1, v2 = c.loc[base, e], c.loc[pico, e], c.loc[final, e]
        subida, bajada = v1 - v0, v2 - v1
        filas.append(
            {
                "eslabon": e,
                f"precio_{base}": v0,
                f"precio_{pico}": v1,
                f"precio_{final}": v2,
                "subida_abs": subida,
                "subida_pct": subida / v0 * 100,
                "bajada_abs": bajada,
                "bajada_pct": bajada / v1 * 100,
                "pct_subida_revertido": -bajada / subida * 100,
            }
        )
    return pd.DataFrame(filas)
