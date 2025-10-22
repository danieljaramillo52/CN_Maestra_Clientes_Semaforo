# Transformación de objetos de data. (Pandas / numpy).
import pandas as pd
from numpy import where
from loguru import logger
from typing import List, Dict, Any
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
def pd_left_merge_two_keys(
    base_left: pd.DataFrame,
    base_right: pd.DataFrame,
    left_key: str,
    right_key: str | None = None,
    drop_right_key: bool = True,
) -> pd.DataFrame:
    """Realiza un left join entre dos DataFrames de pandas.

    Si no se especifica right_key, se asume que ambas bases comparten la misma llave.

    Args:
        base_left (pd.DataFrame): DataFrame base del join.
        base_right (pd.DataFrame): DataFrame derecho con los datos complementarios.
        left_key (str): Llave del DataFrame izquierdo.
        right_key (str, optional): Llave del DataFrame derecho. Si es None, se usa left_key.
        drop_right_key (bool, optional): Si es True, elimina la llave derecha después
            del merge para conservar solo la izquierda. Por defecto True.

    Returns:
        pd.DataFrame: DataFrame resultante del merge.
    """
    if not isinstance(base_left, pd.DataFrame):
        raise TypeError("El argumento base_left debe ser un DataFrame de pandas.")
    if not isinstance(base_right, pd.DataFrame):
        raise TypeError("El argumento base_right debe ser un DataFrame de pandas.")

    # Si no se especifica right_key, asumir que es igual a left_key
    right_key = right_key or left_key

    try:
        base = pd.merge(
            left=base_left,
            right=base_right,
            how="left",
            left_on=left_key,
            right_on=right_key,
        )
        mensaje = "Proceso de merge satisfactorio"

        # Si las llaves son distintas, puedes decidir conservar solo la izquierda
        if drop_right_key and right_key in base.columns and right_key != left_key:
            base = base.drop(columns=[right_key])

    except pd.errors.MergeError as e:
        logger.critical(f"Proceso de merge fallido: {e}")
        raise e

    return base, mensaje


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


def concatenar_columnas_pd(
    df: pd.DataFrame,
    cols_elegidas: List[str],
    nueva_columna: str,
    usar_separador: bool = False,  # 🔹 Nuevo parámetro opcional (False por defecto)
    separador: str = " : ",  # 🔹 Separador por defecto (espacio)
) -> pd.DataFrame:
    """
    Concatena las columnas especificadas y agrega el resultado como una nueva columna al DataFrame.

    Parámetros:
    - dataframe (pd.DataFrame): DataFrame del cual se concatenarán las columnas.
    - cols_elegidas (list): Lista de nombres de las columnas a concatenar.
    - nueva_columna (str): Nombre de la nueva columna que contendrá el resultado de la concatenación.
    - usar_separador (bool): Si es True, concatena las columnas con el separador definido en 'separador'.
    - separador (str): Caracter usado para separar las columnas concatenadas (por defecto, espacio).

    Retorna:
    - pd.DataFrame: DataFrame con la nueva columna agregada.
    """
    try:
        # Verificar si dataframe es un DataFrame de pandas
        if not isinstance(df, pd.DataFrame):
            raise TypeError("El argumento 'dataframe' debe ser un DataFrame de pandas.")

        # Verificar si las columnas especificadas existen en el DataFrame
        for col in cols_elegidas:
            if col not in df.columns:
                raise KeyError(f"La columna '{col}' no existe en el DataFrame.")

        df_copy = df.copy()

        # 🔹 Si usar_separador es True, concatenar con separador. Si no, concatenar normal.
        if usar_separador:
            df_copy.loc[:, nueva_columna] = (
                df_copy[cols_elegidas].fillna("").agg(separador.join, axis=1)
            )
        else:
            df_copy.loc[:, nueva_columna] = (
                df_copy[cols_elegidas].fillna("").agg("".join, axis=1)
            )

        # Registrar el proceso
        logger.info(
            f"Columnas '{', '.join(cols_elegidas)}' concatenadas {'con separador' if usar_separador else 'sin separador'} y almacenadas en '{nueva_columna}'."
        )

        return df_copy

    except Exception as e:
        logger.error(f"Error en la concatenación de columnas: {e}")
        return df


def duplicar_columnas_cfg(
    df: pd.DataFrame, duplicaciones: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Duplica valores entre columnas de un DataFrame según una configuración externa,
    sin depender de un mapeo lógico (cfg_cols). Se espera que los nombres de columna
    usados en la configuración correspondan directamente a los del DataFrame.

    Args:
        df (pd.DataFrame):
            DataFrame sobre el cual se aplican las duplicaciones.
        duplicaciones (List[Dict[str, Any]]):
            Lista de reglas de duplicación cargada desde el YAML.

    Returns:
        pd.DataFrame:
            El mismo DataFrame con las columnas duplicadas según la configuración.

    Raises:
        KeyError:
            Si alguna columna origen o destino no existe en el DataFrame.
        ValueError:
            Si la lista de duplicaciones está vacía o mal estructurada.
    """
    if not duplicaciones:
        raise ValueError("La lista de duplicaciones está vacía o no definida.")

    for regla in duplicaciones:
        origen = regla["origen"]
        destinos = regla["destinos"]

        if origen not in df.columns:
            raise KeyError(f"La columna origen '{origen}' no existe en el DataFrame.")

        for destino in destinos:
            if destino not in df.columns:
                # si no existe la crea automáticamente con el mismo contenido
                df[destino] = df[origen]
            else:
                df.loc[:, destino] = df[origen]

    return df


def remplazar_nulos_multiples_columnas_pd(
    base: pd.DataFrame, list_columns: list, value: str
) -> pd.DataFrame:
    base_modificada = None
    """Funcion que toma un dataframe, una lista de sus columnas para hacer un 
        cambio en los datos nulos de las mismas.
        Args:
            base: Dataframe a base del cambio.
            list_columns: Columnas a modificar su tipo de dato.
            Value: valor del dato: (Notar, solo del tipo str.) 
        Returns: 
            base_modificada (copia de la base con los cambios.)
        """
    try:
        base.loc[:, list_columns] = base[list_columns].fillna(value)
        base_modificada = base
        logger.success("cambio tipo de dato satisfactorio: ")

    except Exception:
        logger.critical("cambio tipo de dato fallido.")
        raise Exception

    return base_modificada
