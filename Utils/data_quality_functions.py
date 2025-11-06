from __future__ import annotations
from loguru import logger
import logging
import sys
from typing import Literal
from functools import wraps
from pathlib import Path
import pandas as pd


def manejar_excepciones(func, modo: Literal["produccion", "debug"] = "produccion"):
    """
    Decorador minimalista para capturar errores comunes de sistema de archivos,
    registrarlos en CRITICAL con traza y finalizar el proceso con código 1.

    Args:
        func: Función objetivo a envolver.

    Returns:
        wrapper: Función envuelta con manejo de excepciones y salida controlada.
    """
    if modo == "debug":
        val_excep = True
    else:
        val_excep = False

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except NotADirectoryError as e:
            logger.opt(exception=val_excep).critical(
                f"Directorio inválido (verifique que la carpeta exista.): {e}"
            )
            sys.exit(1)
        except FileNotFoundError as e:
            logger.opt(exception=val_excep).critical(
                f"Archivo no encontrado. Verifique que el archivo este presente en: {e}"
            )
            sys.exit(1)
        except PermissionError as e:
            logger.opt(exception=val_excep).critical(
                f"Permiso denegado (Verique que los archivos excel están cerrado.): {e}"
            )
            sys.exit(1)
        except OSError as e:
            logger.opt(exception=val_excep).critical(f"Error de E/S del sistema: {e}")
            sys.exit(1)
        except Exception as e:
            logger.opt(exception=val_excep).critical(f"Error inesperado: {e}")
            sys.exit(1)

    return wrapper


@manejar_excepciones
def ensure_dir(base_dir: str | Path) -> Path:
    """
    Verifica que `base_dir` exista y sea un directorio y devuelve su ruta absoluta.

    Args:
        base_dir: Ruta del directorio a validar (relativa o absoluta).

    Returns:
        Path: Ruta absoluta del directorio validado.
    """
    if base_dir:
        base = Path(base_dir)
        if not base.is_dir():
            raise NotADirectoryError(base)
        return base.resolve()


@manejar_excepciones
def resolve_existing_file(base_dir: str | Path, filename: str) -> Path:
    """
    Verifica que `base_dir` sea un directorio y que `filename` exista dentro;
    devuelve la ruta absoluta del archivo.

    Args:
        base_dir: Directorio base donde se buscará el archivo.
        filename: Nombre del archivo (puede incluir subcarpetas relativas).

    Returns:
        Path: Ruta absoluta del archivo existente.
    """
    # Utilizamos resolve para trabajar con la ruta absoluta.
    file_path = (base_dir / filename).resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"{file_path.name} en {base_dir}")
    logger.info(f"Archivo {file_path.name} encontrado.")
    return file_path.resolve()


def verificar_columnas(
    df, columnas_esperadas: dict | list, nombre_arc: str, nom_hoja: str
):
    """
    Verifica que el DataFrame contenga todas las columnas esperadas.

    Args:
        df (pd.DataFrame): DataFrame cargado.
        columnas_esperadas (dict|list): Diccionario {alias: nombre_columna_real} | lista de columnas.
        nombre (str): Nombre descriptivo del DataFrame (para logs).

    Raises:
        ValueError: Si faltan columnas.
    """
    # En dict_cols los valores son los nombres reales
    if isinstance(columnas_esperadas, dict):
        esperadas = set(columnas_esperadas.values)
    else:
        esperadas = set(columnas_esperadas)
    presentes = set(df.columns)

    faltantes = esperadas - presentes

    if faltantes:
        logger.error(
            f"En el archivo: '{nombre_arc}' en la hoja: '{nom_hoja}', faltan las siguientes columnas: {faltantes}"
        )
        sys.exit(1)

    logger.success(
        f"✅ {nombre_arc}: todas las columnas esperadas en la hoja '{nom_hoja}' están presentes."
    )
