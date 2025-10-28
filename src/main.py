# Control de flujo del proyecto.
import pandas as pd
import config_path_routes  # Configuración de paths del proyecto. NO eliminar.
import Utils.general_functions as gf
import Utils.transformation_functions as tf
import Utils.proyect_functions as proy_ft
from Controllers.config_loader import ConfigLoader
from Controllers.process import directa_controller, indirecta_controller


class Aplicacion:
    """
    Clase principal que orquesta la ejecución de los procesos principales del proyecto.

    Carga la configuración global una sola vez e inicializa los subprocesos (Directa,
    Indirecta, etc.) de manera diferida solo cuando se requieren. También centraliza
    la lectura de los archivos de drivers compartidos entre procesos y permite ejecutar
    flujos parciales o completos de forma controlada.

    Attributes:
        config_loader (ConfigLoader): Manejador de la configuración principal del proyecto.
        config_global (Callable): Función auxiliar para acceder a secciones del archivo de configuración.
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
        self.config_global = self.config_loader.get_config
        self.cfg_cols = self.config_global("dict_cols")

        # Variables privadas para lazy initialization
        self._directa = None
        self._indirecta = None
        self._drivers = None

    # Inicialización de procesos

    @property
    def drivers(self):
        """Develve el objeto drivers necesario para los procesos directa e indirecta

        Se carga una sola vez al primer acceso (lazy loading)."""
        if self._drivers is None:
            cfg_drivers = self.config_global("insumos", "drivers")
            self._drivers = gf.lectura_simple_excel(
                dir_insumo=cfg_drivers["path"], nom_insumo=cfg_drivers["nom_base"]
            )
        return self._drivers

    @property
    def directa(self):
        """Devuelve una instancia de ProcesoDirecta solo al primer acceso."""
        if self._directa is None:
            cfg_directa = self.config_global("insumos", "directa")
            self._directa = directa_controller.ProcesoDirecta(
                cfg_directa, cfg_cols=self.cfg_cols, dict_drivers=self.drivers
            )
        return self._directa

    @property
    def indirecta(self):
        """Devuelve una instancia de ProcesoIndirecta solo al primer acceso."""
        if self._indirecta is None:
            cfg_indirecta = self.config_global("insumos", "indirecta")
            self._indirecta = indirecta_controller.ProcesoIndirecta(
                cfg_indirecta, cfg_cols=self.cfg_cols, dict_drivers=self.drivers
            )
        return self._indirecta

    @gf.registro_tiempo
    def ejecutar_parcial(self, proceso: str):
        """Ejecuta parcialmente un proceso específico."""
        if proceso == "directa":
            self.directa.ejecutar()
        elif proceso == "indirecta":
            self.indirecta.ejecutar()
        else:
            raise ValueError(f"Proceso '{proceso}' no reconocido.")

    @gf.registro_tiempo
    def ejecutar_todo(self):
        """Ejecuta ambos procesos completos en secuencia."""
        self.directa.ejecutar()
        self.indirecta.ejecutar()


if __name__ == "__main__":
    app = Aplicacion()

    # ejecutar solo Directa de forma parcial
    app.ejecutar_parcial("directa")
    app.ejecutar_parcial("indirecta")

    # ejecutar ambos procesos completos
    # app.ejecutar_todo()
