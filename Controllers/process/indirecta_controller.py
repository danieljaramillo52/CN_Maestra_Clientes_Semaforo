from loguru import logger
from pandas import DataFrame, merge, concat
from typing import Dict
import Utils.general_functions as gf
import Utils.transformation_functions as tf
import Utils.proyect_functions as proy_ft


class ProcesoIndirecta:
    """Proceso para la parte Indirecta del proyecto."""

    def __init__(
        self, cfg_indirecta: Dict, cfg_cols: Dict, dict_drivers: Dict[str, DataFrame]
    ):
        self.cfg = cfg_indirecta
        self.cfg_cols = cfg_cols
        self.dict_drivers = dict_drivers

    def ejecutar(self, parcial: bool = False):
        logger.info("\n=== Iniciando proceso INDIRECTA ===")

        COLS_UNIVERSO = [*self.cfg["universo_indirecta"]["renombrar_cols"]]
        COLS_BASE_IN_MES = [*self.cfg["base_inicio_mes_indir"]["renombrar_cols"]]

        # Carga insumos proceso indirecta.
        df_unviverso = gf.lectura_insumos_excel(
            path=self.cfg["path"],
            nom_insumo=self.cfg["universo_indirecta"]["nom_base"],
            nom_hoja=self.cfg["universo_indirecta"]["nom_hoja"],
            engine="pyxlsb",
            cols=COLS_UNIVERSO,
            # modo_pruebas=True,
        )
        df_unviverso_wtout_dup = df_unviverso.drop_duplicates()

        df_ini_mes = gf.lectura_insumos_excel(
            path=self.cfg["path"],
            nom_insumo=self.cfg["base_inicio_mes_indir"]["nom_base"],
            nom_hoja=self.cfg["base_inicio_mes_indir"]["nom_hoja"],
            cols=COLS_BASE_IN_MES,
            # modo_pruebas=True,
        )

        df_ini_mes_ren = tf.renombrar_columnas_con_diccionario(
            df=df_ini_mes,
            cols_to_rename=self.cfg["base_inicio_mes_indir"]["renombrar_cols"],
        )

        df_unviverso_ren = tf.renombrar_columnas_con_diccionario(
            df=df_unviverso_wtout_dup,
            cols_to_rename=self.cfg["universo_indirecta"]["renombrar_cols"],
        )

        # Obtener coordenadas completas.
        df_ini_mes_ren = tf.concatenar_columnas_pd(
            df=df_ini_mes_ren,
            cols_elegidas=[self.cfg_cols["coord_y"], self.cfg_cols["coord_x"]],
            nueva_columna=self.cfg_cols["coord_unif"],
            separador=", ",
            usar_separador=True,
        )
        # Tomar columnas referentes a cordenadas (Pregunta Agente - cliente)
        df_ini_mes_coord = tf.seleccionar_columnas_pd(
            df=df_ini_mes_ren,
            cols_elegidas=[self.cfg_cols["cod_actual"], self.cfg_cols["coord_unif"]],
        )
        # Traer las coordenadas unificadas al universo.
        df_unviverso_merge = tf.pd_left_merge_two_keys(
            base_left=df_unviverso_ren,
            base_right=df_ini_mes_coord.drop_duplicates(),
            left_key=self.cfg_cols["cod_actual"],
        )

        # Tomar solo clientes que estan en base inicio mes y no en universo.
        df_ini_mes_ren = df_ini_mes_ren[
            ~df_ini_mes_ren["Cod Cliente"].isin(df_unviverso_merge["Cod Cliente"])
        ]

        dict_reemplazos_jv = gf.crear_diccionario_desde_dataframe(
            df=df_unviverso_merge,
            col_clave=self.cfg_cols["cod_jefe_vtas"],
            col_valor=self.cfg_cols["nom_jefe_vtas"],
        )
        # Traer nombre correcto jefe de vtas.
        df_ini_mes_ren = tf.reemplazar_columna_en_funcion_de_otra(
            df=df_ini_mes_ren,
            nom_columna_de_referencia=self.cfg_cols["cod_jefe_vtas"],
            nom_columna_a_reemplazar=self.cfg_cols["nom_jefe_vtas"],
            mapeo=dict_reemplazos_jv,
        )

        # Aignar columas constantes indirecta (base inicio mes y universo)
        for cada_col in self.cfg["base_inicio_mes_indir"]["cols_constantes_guion"]:
            df_ini_mes_ren[cada_col] = self.cfg_cols["valor_guion"]

        df_unviverso_merge[self.cfg_cols["funcion_inter"]] = self.cfg_cols[
            "valor_guion"
        ]

        # Ajustar las columnas: Cód. Canal/ Cód. Sub Canal Cód./Segmento) transformado.

        df_ini_mes_ren = tf.modificar_caracteres_columna_pd(
            df=df_ini_mes_ren, col=self.cfg_cols["canal"], n=1, accion="conservar"
        )
        df_ini_mes_ren = tf.modificar_caracteres_columna_pd(
            df=df_ini_mes_ren, col=self.cfg_cols["subcanal"], n=2, accion="conservar"
        )
        df_ini_mes_ren = tf.modificar_caracteres_columna_pd(
            df=df_ini_mes_ren, col=self.cfg_cols["segmento"], n=2, accion="conservar"
        )

        # Extraer la tabla de tipologías del diccionario de drivers
        drv_tipologias = self.dict_drivers.get("Tipologías")

        #  Diccionario con las configuraciones de columnas
        par_cols = self.cfg["base_inicio_mes_indir"]["par_cols_merge_drv_tipologia"]

        df_ini_mes_ren_copy = df_ini_mes_ren.copy()

        # Lógica de negocio merge sucesivos con el drv_tipologias usando la configuración establecida.
        df_ini_mes_merge = proy_ft.merge_con_tipologia(
            df_base=df_ini_mes_ren_copy,
            drv_tipologia=drv_tipologias,
            par_cols=par_cols,
        )

        # Traer información del driver municipios (Universo / base inicio mes)
        drv_municipios = self.dict_drivers.get("Municipios")

        # Tratar datos de municipios para garantizar el cruce completo del mege
        drv_municipios.loc[:, self.cfg_cols["municipio"]] = drv_municipios[
            self.cfg_cols["municipio"]
        ].str.lower()

        # Tnasformación para relacionar municipio y departamento base y driver
        df_ini_mes_merge = merge(
            left=df_ini_mes_merge,
            right=drv_municipios.drop_duplicates(
                subset=[
                    self.cfg_cols["cod_poblacion"],
                    self.cfg_cols["cod_departamento"],
                ]
            ),
            on=[
                self.cfg_cols["cod_poblacion"],
                self.cfg_cols["cod_departamento"],
            ],
            how="left",
        )

        df_unviverso_merge = merge(
            left=df_unviverso_merge,
            right=drv_municipios.drop_duplicates(subset=self.cfg_cols["cod_poblacion"]),
            on=[self.cfg_cols["cod_poblacion"]],
            how="left",
        )

        df_unviverso_merge.loc[:, self.FUENTE] = self.VALOR_UNIVERSO
        df_ini_mes_merge.loc[:, self.FUENTE] = self.VALOR_BASE_INICIO_MES

        df_base_completa = concat(
            objs=[df_unviverso_merge, df_ini_mes_merge], join="inner"
        )

        logger.info("=== Proceso Indirecta finalizado ===\n")
