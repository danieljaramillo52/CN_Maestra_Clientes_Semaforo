# Transformación de objetos de data. (Pandas / numpy).
import pandas as pd
from numpy import where
from loguru import logger
from typing import List
from Utils.general_functions import registro_tiempo


def seleccionar_columnas_pd(
    df: pd.DataFrame, cols_elegidas: List[str]
) -> pd.DataFrame | None:
    """
    Filtra y retorna las columnas especificadas del DataFrame.

    Parámetros:
    dataframe (pd.DataFrame): DataFrame del cual se filtrarán las columnas.
    cols_elegidas (list): Lista de nombres de las columnas a incluir en el DataFrame filtrado.

    Retorna:
    pd.DataFrame: DataFrame con las columnas filtradas.
    """
    try:
        # Verificar si dataframe es un DataFrame de pandas
        if not isinstance(df, pd.DataFrame):
            raise TypeError("El argumento 'dataframe' debe ser un DataFrame de pandas.")

        # Filtrar las columnas especificadas
        df_filtrado = df[cols_elegidas]

        return df_filtrado

    except KeyError as ke:
        error_message = (
            f"Error: Columnas especificadas no encontradas en el DataFrame: {str(ke)}"
        )
        logger.critical(error_message)
        return df
    except Exception as e:
        logger.critical(f"Error inesperado al filtrar columnas: {str(e)}")


def renombrar_columnas_con_diccionario(
    df: pd.DataFrame, cols_to_rename: dict
) -> pd.DataFrame:
    """Funcion que toma un diccionario con keys ( nombres actuales ) y values (nuevos nombres) para remplazar nombres de columnas en un dataframe.
    Args:
        df: dataframe al cual se le harán los remplazos
        cols_to_rename: diccionario con nombres antiguos y nuevos
    Result:
        df_renombrado: df con las columnas renombradas.
    """
    df_renombrado = None

    try:
        df_renombrado = df.rename(columns=cols_to_rename, inplace=False)
        logger.success("Proceso de renombrar columnas satisfactorio: ")
    except Exception:
        logger.critical("Proceso de renombrar columnas fallido.")
        raise Exception

    return df_renombrado


@registro_tiempo
def eliminar_dos_primeros_caracteres_pd(
    df: pd.DataFrame, col: str, n: int
) -> pd.DataFrame:
    """
    Elimina los dos primeros caracteres de una columna específica en un DataFrame
    y devuelve una copia modificada del mismo.

    Descripción
    -----------
    Aplica una transformación sobre la columna indicada, removiendo los dos primeros
    caracteres de cada valor. Trabaja sobre una copia del DataFrame original.

    Args
    ----
    df : pd.DataFrame
        DataFrame de entrada que contiene la columna a transformar.
    col : str
        Nombre de la columna sobre la cual se eliminarán los dos primeros caracteres.
    n: int
        Número de caracteres a eliminar.

    Returns
    -------
    pd.DataFrame
        Copia del DataFrame con la columna transformada. Si ocurre un error,
        se devuelve el DataFrame original.
    """
    try:
        # Crear una copia para no modificar el DataFrame original
        df_mod = df.copy()

        # Validar existencia de la columna
        if col not in df_mod.columns:
            raise KeyError(f"La columna '{col}' no existe en el DataFrame")

        # Eliminar los dos primeros caracteres
        df_mod[col] = df_mod[col].astype(str).str[n:]

        # Log de éxito en coherencia con el estándar del proyecto
        mensaje = f"Eliminados los '{n}' primeros caracteres de '{col}'"

        return df_mod, mensaje

    except Exception as e:
        logger.critical(
            f"Error al eliminar los dos primeros caracteres en '{col}': {e}"
        )
        return df


@registro_tiempo
def reemplazar_columna_en_funcion_de_otra(
    df: pd.DataFrame,
    nom_columna_a_reemplazar: str,
    nom_columna_de_referencia: str,
    mapeo: dict,
) -> pd.DataFrame:
    """
    Reemplaza los valores en una columna en función de los valores en otra columna en un DataFrame.

    Args:
        df (pandas.DataFrame): El DataFrame en el que se realizarán los reemplazos.
        columna_a_reemplazar (str): El nombre de la columna que se reemplazará.
        columna_de_referencia (str): El nombre de la columna que se utilizará como referencia para el reemplazo.
        mapeo (dict): Un diccionario que mapea los valores de la columna de referencia a los nuevos valores.

    Returns:
        pandas.DataFrame: El DataFrame actualizado con los valores reemplazados en la columna indicada.
    """
    try:
        logger.info(f"Inicio de remplazamiento de datos en {nom_columna_a_reemplazar}")
        df[nom_columna_a_reemplazar] = where(
            df[nom_columna_de_referencia].isin(mapeo.keys()),
            df[nom_columna_de_referencia].map(mapeo),
            df[nom_columna_a_reemplazar],
        )
        mensaje = f"Proceso de remplazamiento en {nom_columna_a_reemplazar} exitoso"

    except Exception as e:
        logger.critical(
            f"Proceso de remplazamiento de datos en {nom_columna_a_reemplazar} fallido."
        )
        raise e

    return df, mensaje
