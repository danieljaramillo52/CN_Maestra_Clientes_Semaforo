from Utils.general_functions import procesar_configuracion
from loguru import logger


class ConfigLoader:
    """
    Clase encargada de cargar, combinar y exponer la configuración de la aplicación.

    Carga un archivo interno de configuración estructural y un archivo editable por el usuario.
    Si hay claves duplicadas, los valores definidos por el usuario tienen prioridad.
    """

    def __init__(
        self,
        config_file: str = "Controllers/settings/config.yml",
        editable_file: str = "editable.yml",
    ):
        self._config_interna = procesar_configuracion(config_file)
        self._config_usuario = self._cargar_config_usuario(editable_file)
        self._config = self._combinar_configuraciones()

    def _cargar_config_usuario(self, path: str) -> dict:
        try:
            return procesar_configuracion(path)
        except FileNotFoundError:
            logger.warning(
                f"No se encontró archivo de configuración editable en: {path}. Se usará solo la configuración base."
            )
            return {}

    def deep_update(base: dict, overrides: dict) -> dict:
        """
        Combina recursivamente dos diccionarios.
        Los valores de 'overrides' tienen prioridad.
        """
        result = base.copy()
        for k, v in overrides.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = ConfigLoader.deep_update(result[k], v)
            else:
                result[k] = v
        return result

    def _combinar_configuraciones(self) -> dict:
        """
        Combina la configuración interna y editable.
        En caso de conflicto, los valores del usuario sobrescriben.

        Returns:
            dict: configuración unificada.
        """
        cng_interna_copy = self._config_interna.copy()
        if self._config_usuario:
            cng_interna_copy = ConfigLoader.deep_update(
                cng_interna_copy, self._config_usuario
            )
            return cng_interna_copy
        return self._config_interna

    @property
    def config(self) -> dict:
        """Devuelve el diccionario combinado de configuración final."""
        return self._config

    def get_config(self, *claves: str, por_defecto=None):
        """
        Accede a una clave anidada de la configuración de forma segura.

        Args:
            *claves: Secuencia de claves anidadas, por ejemplo: ("insumos", "drivers", "nom_base").
            por_defecto: Valor a retornar si la clave no existe (por defecto: None).

        Returns:
            Cualquier valor de configuración encontrado o el valor por defecto.
        """
        actual = self._config
        for clave in claves:
            if isinstance(actual, dict) and clave in actual:
                actual = actual[clave]
            else:
                logger.debug(
                    f"Clave de configuración no encontrada: {' > '.join(claves)}"
                )
                return por_defecto
        return actual
