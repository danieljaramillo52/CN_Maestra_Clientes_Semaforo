from typing import Dict, Any
import Utils.general_functions as gf

class ProcesarInsumos:
    def __init__(self, config_insumos: Dict[str, Any], dict_cols: Dict[str, Any], config_msg: Dict[str, Any] | None = None):
        """
        Controlador para cargar y validar insumos de ventas y drivers.

        Args:
            config_insumos (Dict[str, Any]): Configuración de rutas, nombres de archivo y hojas de Excel.
            dict_cols (Dict[str, Any]): Diccionario global con las definiciones de columnas.
            config_msg (Dict[str, Any] | None): Configuración opcional de mensajes de UI.
        """
        self.config_insumos = config_insumos
        self.cnf_cols = dict_cols
        self.cnf_msg = config_msg

        # Guardar nombres de hoja para evitar redundancia
        self.hoja_vtas = self.config_insumos["base_vtas"]["nom_hoja"]
        self.hoja_drv = self.config_insumos["drivers"]["nom_hoja"]

    def _carga(self, *, path: str, hoja: str, modo_pruebas: bool, cols: list | dict | None):
        """
        Carga genérica de un archivo Excel.

        Args:
            path (str): Ruta del archivo Excel.
            hoja (str): Nombre de la hoja a leer.
            modo_pruebas (bool): Si True, realiza una carga mínima para verificación.
            cols (list | dict | None): Columnas a verificar o seleccionar. Si None, carga todas.

        Returns:
            DataFrame: DataFrame con los datos cargados desde el archivo.
        """
        return gf.Lectura_insumos_excel(
            path_insumo=path,
            nom_hoja=hoja,
            modo_pruebas=modo_pruebas,
            cols_verificados=cols
        )
