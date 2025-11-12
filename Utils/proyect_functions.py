# Lógica especifica del negocio.
from Utils.general_functions import registro_tiempo
from pandas import DataFrame
from loguru import logger
from typing import List


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
