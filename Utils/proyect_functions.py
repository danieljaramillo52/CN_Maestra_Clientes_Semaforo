# Lógica especifica del negocio.
from Utils.general_functions import registro_tiempo
from pandas import DataFrame
from loguru import logger
from typing import List, Dict, Optional


@registro_tiempo
def eliminar_duplicados_por_prioridad(
    df: DataFrame, col_clave: str, col_prioridad: str, orden_prioridad: List[str]
) -> DataFrame:
    """
    Elimina duplicados en un DataFrame según una columna clave, conservando
    únicamente la fila con mayor prioridad definida en una jerarquía específica.

    Descripción
    -----------
    Esta función permite eliminar duplicados manteniendo una jerarquía
    personalizada sobre una columna de prioridad. El criterio de orden
    se define manualmente en `orden_prioridad`, y las filas se ordenan
    según ese orden antes de eliminar duplicados por `col_clave`.

    Args
    ----
    df : DataFrame
        DataFrame de entrada que contiene los datos.
    col_clave : str
        Nombre de la columna por la cual se identificarán duplicados.
    col_prioridad : str
        Columna que contiene los valores jerárquicos (por ejemplo códigos).
    orden_prioridad : list[str]
        Lista que define el orden de prioridad (de mayor a menor).

    Returns
    -------
    DataFrame
        DataFrame sin duplicados, conservando las filas de mayor prioridad.
    """
    try:
        df_mod = df.copy()

        # Crear un mapeo de prioridades numéricas
        prioridad_map = {v: i for i, v in enumerate(orden_prioridad)}
        df_mod["__orden__"] = df_mod[col_prioridad].map(prioridad_map)

        # Ordenar según la jerarquía (menor índice = mayor prioridad)
        df_mod = df_mod.sort_values("__orden__")

        # Eliminar duplicados conservando la fila de mayor prioridad
        df_mod = df_mod.drop_duplicates(subset=col_clave, keep="first")

        # Eliminar columna auxiliar
        df_mod = df_mod.drop(columns="__orden__")

        mensaje = (
            f"Eliminación de duplicados completada según jerarquía en '{col_prioridad}' "
            f"→ prioridad: {orden_prioridad}"
        )

        return df_mod, mensaje

    except Exception as e:
        logger.critical(f"Error al eliminar duplicados según jerarquía: {e}")
        return df


def agregar_conteo_duplicados(
    df: DataFrame,
    col: str,
    col_salida: str = "duplicados",
    incluir_nan: bool = False,
    cfg_cols: Optional[Dict[str, str]] = None,
) -> DataFrame:
    """
    Agrega a un DataFrame una columna con el número de repeticiones de cada valor de otra columna.

    Descripción:
        Retorna una **copia** de `df` con una nueva columna `col_salida` que indica,
        para cada fila, cuántas veces aparece el valor de `col` en todo el DataFrame.
        Se usa `.copy()` para evitar `SettingWithCopyWarning`.

    Args:
        df (pd.DataFrame): DataFrame de entrada.
        col (str): Nombre de la columna a contar. Si se provee `cfg_cols` y `col` existe
            como clave en ese diccionario, se usará el nombre físico `cfg_cols[col]`.
        col_salida (str, opcional): Nombre de la columna resultante con el conteo. Por defecto, "duplicados".
        incluir_nan (bool, opcional): Si `True`, cuenta también los NaN como grupo (usa `dropna=False`). Por defecto, `False`.
        cfg_cols (dict[str, str] | None, opcional): Mapeo lógico→físico de columnas. Por defecto, `None`.

    Returns:
        pd.DataFrame: Copia de `df` con la columna `col_salida` añadida.

    Ejemplo:
        >>> df2 = agregar_conteo_duplicados(df, col="cliente", col_salida="veces")
        >>> # Con mapeo lógico→físico:
        >>> df2 = agregar_conteo_duplicados(df, col="cliente", cfg_cols={"cliente": "cod_cliente"})
    """
    col_fisica = (cfg_cols or {}).get(col, col)

    dfx = df.copy()
    dfx.loc[:, col_salida] = dfx.groupby(col_fisica, dropna=incluir_nan)[
        col_fisica
    ].transform("size")
    return dfx
