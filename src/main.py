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
    Clase principal que orquesta la ejecución de los diferentes procesos del proyecto.

    Carga la configuración global una sola vez.
    Inicializa los subprocesos (Directa, Indirecta, etc.) solo cuando se usan.
    Permite ejecutar procesos parciales o completos.
    """

    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_global = self.config_loader.get_config
        self.cfg_cols = self.config_global("dict_cols")

        # Variables privadas para lazy initialization
        self._directa = None
        self._indirecta = None

    # Inicialización de procesos
    @property
    def directa(self):
        """Devuelve una instancia de ProcesoDirecta solo al primer acceso."""
        if self._directa is None:
            cfg_directa = self.config_global("insumos", "directa")
            self._directa = directa_controller.ProcesoDirecta(
                cfg_directa, cfg_cols=self.cfg_cols
            )
        return self._directa

    @property
    def indirecta(self):
        """Devuelve una instancia de ProcesoIndirecta solo al primer acceso."""
        if self._indirecta is None:
            cfg_indirecta = self.config_global.get("indirecta", {})
            self._indirecta = self.indirecta_controller.ProcesoIndirecta(cfg_indirecta)
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

    # 🔹 Ejemplo: ejecutar solo Directa de forma parcial
    app.ejecutar_parcial("directa")

    # 🔹 Ejemplo: ejecutar ambos procesos completos
    # app.ejecutar_todo()
