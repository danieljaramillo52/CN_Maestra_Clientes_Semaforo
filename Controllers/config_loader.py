from Utils.general_functions import procesar_configuracion
from loguru import logger
from typing import Any, Tuple
import sys


class ConfigView:
    """
    Vista segura (y perezosa) sobre un **sub-árbol** de la configuración.

    Esta clase no materializa el dict crudo: cada acceso delega en
    `ConfigLoader.get_config(...)` anteponiendo el **prefijo** con el que
    fue creada la vista. Así mantienes validación, trazas/logs y un
    punto único de acceso, pero escribiendo rutas **cortas**.

    Ejemplo:
        cfg_dir = app.config_view("insumos", "directa")
        nom_base = cfg_dir("universo_directa", "nom_base", por_defecto="universo.xlsx")
        hoja     = cfg_dir("universo_directa", "hoja", por_defecto="Hoja1")
        # Estricto (falla rápido si falta):
        nom_base_req = cfg_dir.require("universo_directa", "nom_base")
    """

    def __init__(self, loader: "ConfigLoader", prefix: Tuple[str, ...]):
        """
        Crea una vista anclada a un prefijo de claves.

        Args:
            loader ("ConfigLoader"): Instancia que expone `get_config`.
            prefix (Tuple[str, ...]): Ruta (prefijo) del sub-árbol, p.ej.
                `("insumos", "directa")`.

        """
        self._loader = loader
        self._prefix = prefix

    def get(self, *claves: str, por_defecto: Any = None) -> Any:
        """
        Acceso **tolerante** a una clave anidada partiendo del prefijo de la vista.

        Si alguna clave no existe, devuelve `por_defecto` (no lanza excepción).

        Args:
            *claves: Secuencia de claves a resolver desde el prefijo actual.
            por_defecto: Valor a retornar si la ruta no existe (por defecto: None).

        Returns:
            Any: Valor de configuración encontrado o `por_defecto`.

        Ejemplo:
            cfg_dir.get("universo_directa", "nom_base", por_defecto="universo.xlsx")
        """
        return self._loader.get_config(*self._prefix, *claves, por_defecto=por_defecto)

    # Alias para usar la vista como si fuera una función:
    #   cfg_dir("a","b", por_defecto="x")
    __call__ = get

    def require(self, *claves: str) -> Any:
        """
        Acceso **estricto**: exige que la clave exista.

        Si la ruta no existe, lanza `KeyError` con la ruta completa desde el
        nivel global. Útil para validar configuraciones obligatorias (fail fast).

        Args:
            *claves: Secuencia de claves a resolver desde el prefijo actual.

        Returns:
            Any: Valor de configuración encontrado.

        Raises:
            KeyError: Si la ruta no existe.

        Ejemplo:
            nom_base = cfg_dir.require("universo_directa", "nom_base")
        """
        valor = self.get(*claves, por_defecto=...)
        if valor is ...:
            ruta = " > ".join((*self._prefix, *claves))
            raise KeyError(f"Clave de configuración requerida no encontrada: {ruta}")
        return valor

    def __getitem__(self, clave: str) -> Any:
        """
        Acceso **estricto** estilo mapeo/dict para la clave **inmediata**.

        Equivale a `require(clave)` pero solo para un nivel (no acepta
        múltiples claves). Conveniente para `cfg_dir["universo_directa"]`.

        Args:
            clave (str): Clave inmediata dentro del sub-árbol.

        Returns:
            Any: Valor asociado a `clave`.

        Raises:
            KeyError: Si la clave no existe.

        Ejemplo:
            universo = cfg_dir["universo_directa"]
        """
        valor = self.get(clave, por_defecto=...)
        if valor is ...:
            ruta = " > ".join((*self._prefix, clave))
            raise KeyError(f"Clave de configuración no encontrada: {ruta}")
        return valor

    def as_dict(self) -> dict:
        """
        Devuelve una **copia materializada** del dict del sub-árbol.

        Útil cuando necesitas pasar el sub-árbol completo a otra función o
        validarlo con un esquema (p. ej., Pydantic). Los accesos posteriores
        que quieras “seguros” deberían seguir haciéndose mediante la vista.

        Returns:
            dict: Copia del sub-árbol o `{}` si el sub-árbol no existe.
        """
        d = self.get(por_defecto={})
        return {} if d is ... else d


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
                sys.exit(1)
                return por_defecto
        return actual

    def view(self, *claves: str) -> ConfigView:
        """Devuelve una vista segura anclada en el prefijo dado."""
        return ConfigView(self, tuple(claves))
