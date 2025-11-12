# Control de flujo del proyecto.
import pandas as pd
import config_path_routes  # Configuración de paths del proyecto. NO eliminar.
import Utils.general_functions as gf
import Utils.data_quality_functions as dqf
import Utils.transformation_functions as tf
import Utils.proyect_functions as proy_ft
from Controllers.config_loader import ConfigLoader
from Controllers.process import (
    directa_controller,
    indirecta_controller,
    inactivos_dir_controller,
    inactivos_indir_controller,
)


class Aplicacion:
    """
    Clase principal que orquesta la ejecución de los procesos principales del proyecto.

    Carga la configuración global una sola vez e inicializa los subprocesos (Directa,
    Indirecta, etc.) de manera diferida solo cuando se requieren. También centraliza
    la lectura de los archivos de drivers compartidos entre procesos y permite ejecutar
    flujos parciales o completos de forma controlada.

    Attributes:
        config_loader (ConfigLoader): Manejador de la configuración principal del proyecto.
        config_view (Callable): Función auxiliar para acceder a secciones del archivo de configuración.
        cfg_cols (dict): Diccionario de columnas globales definido en la configuración (`dict_cols`).
        _directa (ProcesoDirecta | None): Instancia del proceso Directa, creada al primer acceso.
        _indirecta (ProcesoIndirecta | None): Instancia del proceso Indirecta, creada al primer acceso.
        _drivers (pandas.DataFrame | dict[str, pandas.DataFrame] | None): Datos de drivers cargados una sola vez.

    Methods:
        ejecutar_parcial(proceso: str): Ejecuta un proceso específico ("directa" o "indirecta").
        ejecutar_todo(): Ejecuta ambos procesos de forma secuencial.
    """

    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_view = self.config_loader.view
        self.cfg_cols = self.config_view("dict_cols")

        # Variables privadas para lazy initialization
        self._directa = None
        self._indirecta = None
        self._inactivos_directa = None
        self._inactivos_indirecta = None
        self._drivers = None

    # Inicialización de procesos
    @property
    def drivers(self):
        """Develve el objeto drivers necesario para los procesos directa e indirecta

        Se carga una sola vez al primer acceso (lazy loading)."""
        if self._drivers is None:
            cfg_drivers = self.config_view("insumos", "drivers")

            # Validacion de columnas para todas las hojas del driver.
            dict_driver_df = gf.lectura_simple_excel(
                dir_insumo=cfg_drivers["path"],
                nom_insumo=cfg_drivers["nom_base"],
            )
            for cada_hoja in cfg_drivers["nom_hojas"]:

                driver_df = dict_driver_df[cada_hoja]

                dqf.verificar_columnas(
                    df=driver_df,
                    columnas_esperadas=cfg_drivers["cols"][cada_hoja],
                    nombre_arc=cfg_drivers["nom_base"],
                    nom_hoja=cada_hoja,
                )

            self._drivers = gf.lectura_simple_excel(
                dir_insumo=cfg_drivers["path"], nom_insumo=cfg_drivers["nom_base"]
            )
        return self._drivers

    @property
    def directa(self):
        """Devuelve una instancia de ProcesoDirecta solo al primer acceso."""
        if self._directa is None:
            cfg_directa = self.config_view("insumos", "directa")
            self._directa = directa_controller.ProcesoDirecta(
                cfg_directa, cfg_cols=self.cfg_cols, dict_drivers=self.drivers
            )
        return self._directa

    @property
    def indirecta(self):
        """Devuelve una instancia de ProcesoIndirecta solo al primer acceso."""
        if self._indirecta is None:
            cfg_indirecta = self.config_view("insumos", "indirecta")
            self._indirecta = indirecta_controller.ProcesoIndirecta(
                cfg_indirecta, cfg_cols=self.cfg_cols, dict_drivers=self.drivers
            )
        return self._indirecta

    @property
    def inactivos_directa(self):
        """Devuelve una instancia de ProcesoIndirecta solo al primer acceso."""
        if self._inactivos_directa is None:
            cfg_inactivos_directa = self.config_view("insumos", "directa")
            self._inactivos_directa = inactivos_dir_controller.ProcesoDirectaInactivos(
                cfg_inactivos_directa, cfg_cols=self.cfg_cols, dict_drivers=self.drivers
            )
        return self._inactivos_directa

    @property
    def inactivos_indirecta(self):
        """Devuelve una instancia de ProcesoIndirecta solo al primer acceso."""
        if self._inactivos_indirecta is None:
            cfg_inactivos_indirecta = self.config_view("insumos", "indirecta")
            self._inactivos_indirecta = (
                inactivos_indir_controller.ProcesoIndirectaInactivos(
                    cfg_inactivos_indirecta,
                    cfg_cols=self.cfg_cols,
                    dict_drivers=self.drivers,
                )
            )
        return self._inactivos_indirecta

    @gf.registro_tiempo
    def ejecutar_parcial(self, proceso: str):
        """Ejecuta parcialmente un proceso específico."""
        if proceso == "directa":
            self.directa.ejecutar()
        elif proceso == "indirecta":
            self.indirecta.ejecutar()
        elif proceso == "inactivos_directa":
            self.inactivos_directa.ejecutar()
        elif proceso == "inactivos_indirecta":
            self.inactivos_indirecta.ejecutar()
        else:
            raise ValueError(f"Proceso '{proceso}' no reconocido.")

    @gf.registro_tiempo
    def ejecutar_todo(self):
        """Ejecuta ambos procesos completos en secuencia."""
        self.directa.ejecutar()
        self.indirecta.ejecutar()
        self.inactivos_directa.ejecutar()
        self.inactivos_indirecta.ejecutar()


if __name__ == "__main__":
    app = Aplicacion()

    cfg_insumos = app.config_view("insumos")

    path_insumos_dir = dqf.ensure_dir(base_dir=cfg_insumos("directa", "path"))
    path_insumos_indir = dqf.ensure_dir(base_dir=cfg_insumos("indirecta", "path"))
    path_insumos_drvs = dqf.ensure_dir(base_dir=cfg_insumos("drivers", "path"))

    # Validación de insumos.
    dqf.resolve_existing_file(
        base_dir=path_insumos_dir,
        filename=cfg_insumos.require("directa", "universo_directa", "nom_base"),
    )
    dqf.resolve_existing_file(
        base_dir=path_insumos_dir,
        filename=cfg_insumos.require("directa", "base_inicio_mes_dir", "nom_base"),
    )

    dqf.resolve_existing_file(
        base_dir=path_insumos_indir,
        filename=cfg_insumos.require("indirecta", "universo_indirecta", "nom_base"),
    )
    dqf.resolve_existing_file(
        base_dir=path_insumos_indir,
        filename=cfg_insumos.require("indirecta", "base_inicio_mes_indir", "nom_base"),
    )

    dqf.resolve_existing_file(
        base_dir=path_insumos_dir,
        filename=cfg_insumos.require("directa", "maestra_inactivos_dir", "nom_base"),
    )
    dqf.resolve_existing_file(
        base_dir=path_insumos_indir,
        filename=cfg_insumos.require(
            "indirecta", "maestra_inactivos_indir", "nom_base"
        ),
    )

    dqf.resolve_existing_file(
        base_dir=path_insumos_drvs,
        filename=cfg_insumos.require("drivers", "nom_base"),
    )
    gf.menu(app)
