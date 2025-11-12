# Transformación de objetos de data. (Pandas / numpy).
import pandas as pd
from numpy import where
from loguru import logger
from typing import List, Dict, Any, Tuple, Literal
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
        # logger.success("Proceso de renombrar columnas satisfactorio: ")
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
def modificar_caracteres_columna_pd(
    df: pd.DataFrame,
    col: str,
    n: int,
    accion: Literal["eliminar", "conservar"] = "eliminar",
) -> Tuple[pd.DataFrame, str]:
    """
    Elimina o conserva los primeros `n` caracteres de una columna específica en un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame de entrada que contiene la columna a transformar.
        col (str): Nombre de la columna a modificar.
        n (int): Número de caracteres a eliminar o conservar.
        accion (Literal["eliminar", "conservar"], opcional):
            Acción a realizar:
            - "eliminar": elimina los primeros `n` caracteres.
            - "conservar": mantiene solo los primeros `n` caracteres.
            Por defecto "eliminar".

    Returns:
        Tuple[pd.DataFrame, str]:
            DataFrame modificado y mensaje descriptivo.
    """
    try:
        df_mod = df.copy()

        if col not in df_mod.columns:
            raise KeyError(f"La columna '{col}' no existe en el DataFrame.")

        if accion == "eliminar":
            df_mod[col] = df_mod[col].str[n:]
            mensaje = f" Eliminados los primeros {n} caracteres de '{col}'."
        elif accion == "conservar":
            df_mod[col] = df_mod[col].str[:n]
            mensaje = f" Conservados solo los primeros {n} caracteres de '{col}'."
        else:
            raise ValueError("El parámetro 'accion' debe ser 'eliminar' o 'conservar'.")

        return df_mod, mensaje

    except Exception as e:
        mensaje = f" Error al modificar caracteres en '{col}': {e}"
        return df, mensaje

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
    """
    try:
        df_copy = df.copy()

        # logger.info(f"Inicio de reemplazamiento de datos en {nom_columna_a_reemplazar}")

        df_copy.loc[:, nom_columna_a_reemplazar] = where(
            df_copy[nom_columna_de_referencia].isin(mapeo.keys()),
            df_copy[nom_columna_de_referencia].map(mapeo),
            df_copy[nom_columna_a_reemplazar],
        )

        mensaje = f"Proceso de reemplazamiento en {nom_columna_a_reemplazar} exitoso"
        # logger.info(mensaje)

    except Exception as e:
        logger.critical(
            f"Proceso de reemplazamiento de datos en {nom_columna_a_reemplazar} fallido: {e}"
        )
        raise e

    return df_copy, mensaje


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
        logger.success("tratamienmto de nulos satisfacotiro: ")

    except Exception:
        logger.critical("cambio tipo de dato fallido.")
        raise Exception

    return base_modificada


@registro_tiempo
def reemplazar_nulos_con_dict(
    df: pd.DataFrame, valores_por_defecto: Dict[str, Any]
) -> pd.DataFrame:
    """
    Reemplaza los valores nulos en un DataFrame según un diccionario de valores por columna.

    Descripción
    -----------
    Esta función itera sobre las claves del diccionario `valores_por_defecto`,
    reemplazando los valores nulos (NaN) en cada columna indicada por el valor
    correspondiente definido en el diccionario.
    Solo se procesan las columnas existentes en el DataFrame.

    Args
    ----
    df : pd.DataFrame
        DataFrame de entrada sobre el que se aplicarán los reemplazos.
    valores_por_defecto : Dict[str, Any]
        Diccionario con pares {columna: valor_por_defecto} que define el valor
        con el que se reemplazarán los nulos en cada columna.

    Returns
    -------
    pd.DataFrame
        Copia del DataFrame con los valores nulos reemplazados según el diccionario.

    Raises
    ------
    TypeError
        Si `valores_por_defecto` no es un diccionario.
    Exception
        Si ocurre cualquier otro error durante el proceso.
    """
    try:
        # Validar tipo del diccionario
        if not isinstance(valores_por_defecto, dict):
            raise TypeError(
                "El parámetro 'valores_por_defecto' debe ser un diccionario."
            )

        # Crear copia del DataFrame
        df_copy = df.copy()

        # Reemplazar valores nulos según el diccionario
        df_copy = df_copy.fillna(value=valores_por_defecto)

        logger.info(
            f"Reemplazo de nulos completado para columnas: {list(valores_por_defecto.keys())}"
        )
        mensaje = (
            f"Reemplazo de nulos exitoso en columnas {list(valores_por_defecto.keys())}"
        )

        return df_copy, mensaje

    except Exception as e:
        mensaje_error = (
            f"❌ Error al reemplazar nulos: {e}. Se devuelve el DataFrame original."
        )
        logger.error(mensaje_error)
        return df, mensaje_error


def conservar_n_caracteres(
    df: pd.DataFrame, columnas: str | List[str], n_caracteres: int
) -> pd.DataFrame:
    """
    Conserva únicamente los primeros `n_caracteres` de una o varias columnas
    de texto en un DataFrame.

    Si una celda contiene menos caracteres que el valor indicado, no se trunca.
    En caso de error (columna inexistente o tipo no compatible), se registra
    el fallo y se devuelve el DataFrame sin modificar.

    Args:
        df (pd.DataFrame): DataFrame con las columnas a modificar.
        columnas (str | list[str]): Nombre o lista de nombres de las columnas a truncar.
        n_caracteres (int): Número de caracteres a conservar desde el inicio de cada valor.

    Returns:
        pd.DataFrame: DataFrame con las columnas modificadas. Si ocurre un error,
        se devuelve el DataFrame original sin cambios.

    Example:
        >>> df = conservar_n_caracteres(df, columnas="CodigoCliente", n_caracteres=5)
    """
    try:
        df = df.copy()

        if isinstance(columnas, str):
            columnas = [columnas]

        columnas_invalidas = [col for col in columnas if col not in df.columns]
        if columnas_invalidas:
            raise KeyError(f"Columnas inexistentes: {columnas_invalidas}")

        # Aplicar truncamiento
        df[columnas] = (
            df[columnas].astype(str).apply(lambda col: col.str[:n_caracteres])
        )

        logger.info(
            f"Se conservaron los primeros {n_caracteres} caracteres en columnas: {columnas}"
        )
        return df

    except Exception as e:
        logger.error(
            f"Error al truncar columnas {columnas} a {n_caracteres} caracteres: {e}"
        )
        return df
