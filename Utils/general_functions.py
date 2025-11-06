from loguru import logger
from functools import wraps
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import yaml
import time
import sys


def procesar_configuracion(nom_archivo_configuracion: str) -> Dict:
    """
    Lee un archivo YAML de configuración y devuelve su contenido como diccionario.

    Args:
        nom_archivo_configuracion (str): Ruta completa o relativa al archivo YAML.

    Returns:
        dict: Diccionario con la configuración cargada.

    Raises:
        Exception: Si el archivo no existe o no se puede parsear.
    """
    try:
        with open(nom_archivo_configuracion, "r", encoding="utf-8") as archivo:
            configuracion_yaml = yaml.safe_load(archivo)
        return configuracion_yaml
    except Exception as e:
        logger.error(f"Error al leer configuración '{nom_archivo_configuracion}': {e}")
        raise


def log_tiempo_proceso(func_name: str, segundos: float, mensaje: str = None) -> None:
    """
    Registra en el log el tiempo total de ejecución de un proceso.
    Si se proporciona un mensaje, se agrega la duración al final.
    """
    diferencia = timedelta(seconds=segundos)
    minutos = int(diferencia.total_seconds() // 60)
    segundos = int(diferencia.total_seconds() % 60)
    duracion = f"{minutos}m {segundos}s"

    # depth=1 hace que el log aparezca con el contexto de la función original
    logger.opt(depth=1).success(
        f"{mensaje or f'Proceso {func_name} completado'} (Duración: {duracion})"
    )


def registro_tiempo(original_func):
    """
    Decorador que mide el tiempo de ejecución de una función
    y delega el formateo del log a `log_tiempo_proceso`.

    - Si la función devuelve un string, se considera el mensaje de éxito.
    - Si devuelve una tupla (data, mensaje), se usa el segundo valor como mensaje.
    - Si no devuelve string, imprime un mensaje genérico.
    """

    @wraps(original_func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = original_func(*args, **kwargs)
        end = time.time()
        segundos = end - start

        # Caso 1: función devuelve un mensaje (string)
        if isinstance(result, str):
            mensaje = result
            log_tiempo_proceso(original_func.__name__, segundos, mensaje)
            return result

        #  Caso 2: función devuelve (data, mensaje)
        elif isinstance(result, tuple) and isinstance(result[-1], str):
            mensaje = result[-1]
            log_tiempo_proceso(original_func.__name__, segundos, mensaje)
            return result[0]

        #  Caso 3: sin mensaje explícito
        else:
            log_tiempo_proceso(original_func.__name__, segundos)
            return result

    return wrapper


@registro_tiempo
def exportar_a_excel(
    ruta_archivo: str, df: pd.DataFrame, nom_hoja: str = "Hoja1", index: bool = False
) -> str:
    """
    Exporta un DataFrame a un archivo Excel en la ruta completa especificada.
    Si la carpeta destino no existe, se crea automáticamente.

    Args:
        ruta_archivo (str): Ruta completa del archivo (incluye el nombre y extensión .xlsx).
        df (pd.DataFrame): DataFrame a exportar.
        nom_hoja (str): Nombre de la hoja dentro del archivo.
        index (bool): Si se incluye o no el índice.

    Returns:
        str: Mensaje de éxito para el log.
    """
    try:
        ruta = Path(ruta_archivo)

        # Crear carpeta si no existe
        ruta.parent.mkdir(parents=True, exist_ok=True)

        # Exportar el DataFrame.
        logger.info(f"Inicio exportacion {ruta.name}")

        df.to_excel(ruta, sheet_name=nom_hoja, index=index)

        return f"✅ Exportación completada: '{ruta.name}' con hoja '{nom_hoja}' en '{ruta.parent}'"

    except Exception as e:
        logger.error(f"❌ Error exportando '{ruta_archivo}': {e}")
        raise


@registro_tiempo
def lectura_insumos_excel(
    path: str,
    nom_insumo: str,
    nom_hoja: str,
    engine="openpyxl",
    cols: int | list = None,
    modo_pruebas=False,
) -> Tuple[pd.DataFrame, str]:
    """
    Lee archivos de Excel con cualquier extensión y carga los datos de una hoja específica.

    Args:
        path (str): Ruta del archivo.
        nom_insumo (str): Nombre del archivo con extensión.
        nom_hoja (str): Nombre de la hoja a cargar.
        engine (str): Motor de lectura (por defecto 'openpyxl').
        cols (list | int, opcional): Columnas a cargar.
        modo_pruebas (bool): Si True, carga solo 2 filas para pruebas.

    Returns:
        Tuple[pd.DataFrame, str]: DataFrame leído y mensaje de éxito.
    """
    try:
        nrows = 1000 if modo_pruebas else None
        logger.info(f"Iniciando lectura {nom_insumo} Hoja: {nom_hoja}")

        base_leida = pd.read_excel(
            Path(path) / nom_insumo,
            sheet_name=nom_hoja,
            dtype=str,
            engine=engine,
            nrows=nrows,
            usecols=cols,
        )

        mensaje = f"Lectura de {nom_insumo} Hoja: {nom_hoja} completada con éxito"
        return base_leida, mensaje

    except Exception as e:
        logger.error(f"Error leyendo {nom_insumo} Hoja: {nom_hoja} → {e}")
        raise


@registro_tiempo
def lectura_simple_excel(
    dir_insumo: str, nom_insumo: str, nom_hoja: str = None
) -> pd.DataFrame:
    """
    Lee un archivo de Excel y devuelve su contenido en un DataFrame.

    Args:
        dir_insumo (str): Ruta del directorio donde se encuentra el archivo.
        nom_insumo (str): Nombre del archivo de Excel (incluyendo la extensión).
        nom_hoja (str): Nombre de la hoja a leer dentro del archivo de Excel.

    Returns:
        pd.DataFrame: Contenido de la hoja de Excel como un DataFrame.

    Raises:
        Exception: Si ocurre algún error durante la lectura del archivo.
    """

    try:
        logger.info(f"Inicio lectura simple de '{nom_insumo}' hoja: '{nom_hoja}' ")
        base_leida = pd.read_excel(
            dir_insumo + nom_insumo,
            sheet_name=nom_hoja,
            dtype=str,
        )
        mensaje = f"Lectura simple de {nom_insumo} realizada con éxito"
        return base_leida, mensaje
    except PermissionError as pe:
        logger.opt(exception=True).critical(
            f"Permiso al archivo denegado verificar que el insumo esté cerrado: {pe}"
        )
        sys.exit(1)
    except Exception as e:
        logger.opt(exception=True).critical(
            f"Permiso al archivo denegado verificar que el insumo esté cerrado: {e}"
        )
        sys.exit(1)


def crear_diccionario_desde_dataframe(
    df: pd.DataFrame, col_clave: str, col_valor: str
) -> dict:
    """
    Crea un diccionario a partir de un DataFrame utilizando dos columnas especificadas.

    Args:
        df (pd.DataFrame): El DataFrame de entrada.
        col_clave (str): El nombre de la columna que se utilizará como clave en el diccionario.
        col_valor (str): El nombre de la columna que se utilizará como valor en el diccionario.

    Returns:
        dict: Un diccionario creado a partir de las columnas especificadas.
    """
    try:
        # Verificar si las columnas existen en el DataFrame
        if col_clave not in df.columns or col_valor not in df.columns:
            raise ValueError("Las columnas especificadas no existen en el DataFrame.")

        # Crear el diccionario a partir de las columnas especificadas
        resultado_dict = df.set_index(col_clave)[col_valor].to_dict()

        return resultado_dict

    except ValueError as ve:
        # Registrar un mensaje crítico si hay un error
        logger.critical(f"Error: {ve}")
        raise ve


def menu(app):
    """
    Menú mínimo por consola para ejecutar procesos:
      1) Directa
      2) Indirecta
      3) Todo
      0) Salir
    """
    acciones = {
        "1": lambda: app.ejecutar_parcial("directa"),
        "2": lambda: app.ejecutar_parcial("indirecta"),
        "3": lambda: app.ejecutar_parcial("inactivos_directa"),
        "4": lambda: app.ejecutar_parcial("inactivos_indirecta"),
        "5": app.ejecutar_todo,
    }

    while True:
        print("\n=== MENÚ ===")
        print("1) Ejecutar UNIVERSO DIRECTA")
        print("2) Ejecutar UVIERSO INDIRECTA")
        print("3) Ejecutar INACTIVOS DIRECTA")
        print("4) Ejecutar INACTIVOS INDIRECTA")
        print("5) Ejecutar TODO")
        print("0) Salir")
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "0":
            print("Saliendo...")
            break

        accion = acciones.get(opcion)
        if not accion:
            print("Opción inválida. Intenta de nuevo.")
            continue

        try:
            accion()
            print("✔ Proceso finalizado.")
        except KeyboardInterrupt:
            print("\nInterrumpido por el usuario.")
        except Exception as e:
            # Muestra error breve; puedes loguear detalles con logger si quieres
            print(f"✖ Error al ejecutar la opción {opcion}: {e}")
