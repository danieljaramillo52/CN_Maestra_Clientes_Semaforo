from loguru import logger
import Utils.general_functions as gf
import Utils.transformation_functions as tf
import Utils.proyect_functions as proy_ft


class ProcesoDirecta:
    """Proceso para la parte Directa del proyecto."""

    def __init__(self, cfg_directa: dict, cfg_cols: dict):
        self.cfg = cfg_directa
        self.cfg_cols = cfg_cols

    def ejecutar(self):
        logger.info("\n=== Iniciando proceso DIRECTA ===")

        COLS_UNIVERSO = [*self.cfg["universo_directa"]["renombrar_cols"]]
        COLS_BASE_IN_MES = [*self.cfg["base_inicio_mes_dir"]["renombrar_cols"]]

        # Carga insumos proceso directa.
        df_unviverso = gf.lectura_insumos_excel(
            path=self.cfg["path"],
            nom_insumo=self.cfg["universo_directa"]["nom_base"],
            nom_hoja=self.cfg["universo_directa"]["nom_hoja"],
            modo_pruebas=True,
            engine="pyxlsb",
            cols=COLS_UNIVERSO,
        )

        df_ini_mes = gf.lectura_insumos_excel(
            path=self.cfg["path"],
            nom_insumo=self.cfg["base_inicio_mes_dir"]["nom_base"],
            nom_hoja=self.cfg["base_inicio_mes_dir"]["nom_hoja"],
            modo_pruebas=True,
            cols=COLS_BASE_IN_MES,
        )

        # Seleccionar y renombrar cols bases.
        # df_ini_mes = tf.seleccionar_columnas_pd(
        #    df=df_ini_mes,
        #    cols_elegidas=[*self.cfg["base_inicio_mes_dir"]["renombrar_cols"]],
        # )
        df_ini_mes = tf.renombrar_columnas_con_diccionario(
            df=df_ini_mes,
            cols_to_rename=self.cfg["base_inicio_mes_dir"]["renombrar_cols"],
        )
        # df_unviverso = tf.seleccionar_columnas_pd(
        #    df=df_unviverso,
        #    cols_elegidas=[*self.cfg["universo_directa"]["renombrar_cols"]],
        # )
        df_unviverso = tf.renombrar_columnas_con_diccionario(
            df=df_unviverso,
            cols_to_rename=self.cfg["universo_directa"]["renombrar_cols"],
        )
        # Eliminar duplicados por orden de prioridad cód vendedor.
        df_ini_mes_fil = proy_ft.eliminar_duplicados_por_prioridad(
            df=df_ini_mes,
            col_clave=self.cfg_cols["cod_cliente"],
            col_prioridad=self.cfg_cols["funcion_inter"],
            orden_prioridad=self.cfg["universo_directa"]["orden_prioridad_jv_vend"],
        )

        df_ini_mes_fil = tf.eliminar_dos_primeros_caracteres_pd(
            df=df_ini_mes_fil, col=self.cfg_cols["cod_cliente"], n=2
        )

        dict_reemplazos_jv = gf.crear_diccionario_desde_dataframe(
            df=df_unviverso,
            col_clave=self.cfg_cols["cod_jefe_vtas"],
            col_valor=self.cfg_cols["nom_jefe_vtas"],
        )
        # Traer nombre correcto jefe de vtas.
        df_ini_mes_fil = tf.reemplazar_columna_en_funcion_de_otra(
            df=df_ini_mes_fil,
            nom_columna_de_referencia=self.cfg_cols["cod_jefe_vtas"],
            nom_columna_a_reemplazar=["nom_jefe_vtas"],
            mapeo=dict_reemplazos_jv,
        )
        # Duplicar las columnas lógica vendedor y nom vendedor.
        logger.info("=== Proceso Directa finalizado ===\n")
