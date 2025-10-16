from loguru import logger
import Utils.general_functions as gf


class ProcesoIndirecta:
    """Proceso para la parte Indirecta del proyecto."""

    def __init__(self, cfg_indirecta: dict):
        self.cfg = cfg_indirecta

    def ejecutar(self, parcial: bool = False):
        logger.info("\n=== Iniciando proceso INDIRECTA ===")

        logger.info("=== Proceso Indirecta finalizado ===\n")
