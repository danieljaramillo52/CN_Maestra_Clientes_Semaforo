from loguru import logger
from typing import Dict
from Utils.data_quality_functions import verificar_columnas
from pandas import DataFrame, merge, concat
import Utils.general_functions as gf
import Utils.transformation_functions as tf
from Utils.proyect_functions import (
    eliminar_duplicados_por_prioridad,
    agregar_conteo_duplicados,
)


class ProcesoDirecta:
    """Proceso para la parte Directa del proyecto."""

    FUENTE = "Fuente"
    VALOR_UNIVERSO = "universo"
    VALOR_BASE_INICIO_MES = "base_inicio_mes"
    LISTA_COORD_NULL = ["0, 0", ", "]

    def __init__(
        self, cfg_directa: Dict, cfg_cols: Dict, dict_drivers: Dict[str, DataFrame]
    ):
        self.cfg = cfg_directa
        self.cfg_cols = cfg_cols
        self.dict_drivers = dict_drivers

    def ejecutar(self):
        logger.info("\n=== Iniciando proceso DIRECTA ===")

        COLS_UNIVERSO = [*self.cfg("universo_directa", "renombrar_cols")]
        COLS_BASE_IN_MES = [*self.cfg("base_inicio_mes_dir", "renombrar_cols")]

        # Validar columnas previamente cargando una pequeña parte del insumo
        df_unviverso_min = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("universo_directa", "nom_base"),
            nom_hoja=self.cfg("universo_directa", "nom_hoja"),
            engine="pyxlsb",
            modo_pruebas=True,
        )

        df_ini_mes_min = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("base_inicio_mes_dir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_dir", "nom_hoja"),
            modo_pruebas=True,
        )
        # Validación de columnas esperadas
        verificar_columnas(
            df=df_unviverso_min,
            columnas_esperadas=COLS_UNIVERSO,
            nombre_arc=self.cfg("universo_directa", "nom_base"),
            nom_hoja=self.cfg("universo_directa", "nom_hoja"),
        )
        verificar_columnas(
            df=df_ini_mes_min,
            columnas_esperadas=COLS_BASE_IN_MES,
            nombre_arc=self.cfg("base_inicio_mes_dir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_dir", "nom_hoja"),
        )
        # Carga insumos proceso directa.
        df_unviverso = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("universo_directa", "nom_base"),
            nom_hoja=self.cfg("universo_directa", "nom_hoja"),
            engine="pyxlsb",
            cols=COLS_UNIVERSO,
            modo_pruebas=False,
        )

        df_ini_mes = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("base_inicio_mes_dir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_dir", "nom_hoja"),
            cols=COLS_BASE_IN_MES,
            modo_pruebas=False,
        )

        df_ini_mes = tf.renombrar_columnas_con_diccionario(
            df=df_ini_mes,
            cols_to_rename=self.cfg("base_inicio_mes_dir", "renombrar_cols"),
        )

        df_unviverso = tf.renombrar_columnas_con_diccionario(
            df=df_unviverso,
            cols_to_rename=self.cfg("universo_directa", "renombrar_cols"),
        )
        # Eliminar duplicados por orden de prioridad cód vendedor.
        df_ini_mes_fil = eliminar_duplicados_por_prioridad(
            df=df_ini_mes,
            col_clave=self.cfg_cols("cod_cliente"),
            col_prioridad=self.cfg_cols("funcion_inter"),
            orden_prioridad=self.cfg("base_inicio_mes_dir", "orden_prioridad_jv_vend"),
        )
        df_unviverso_fil = eliminar_duplicados_por_prioridad(
            df=df_unviverso,
            col_clave=self.cfg_cols("cod_cliente"),
            col_prioridad=self.cfg_cols("funcion_inter"),
            orden_prioridad=self.cfg("universo_directa", "orden_prioridad_jv_vend"),
        )

        df_ini_mes_fil = tf.modificar_caracteres_columna_pd(
            df=df_ini_mes_fil,
            col=self.cfg_cols("cod_cliente"),
            n=2,
        )

        df_ini_mes_fil = tf.concatenar_columnas_pd(
            df=df_ini_mes_fil,
            cols_elegidas=[self.cfg_cols("coord_y"), self.cfg_cols("coord_x")],
            nueva_columna=self.cfg_cols("coord_unif"),
            separador=", ",
            usar_separador=True,
        )

        # Tomar columnas referentes a cordenadas
        df_ini_mes_coord = tf.seleccionar_columnas_pd(
            df=df_ini_mes_fil,
            cols_elegidas=[self.cfg_cols("cod_cliente"), self.cfg_cols("coord_unif")],
        )
        # Traer las coordenadas unificadas al universo.
        df_unviverso_fil = tf.pd_left_merge_two_keys(
            base_left=df_unviverso_fil,
            base_right=df_ini_mes_coord,
            left_key=self.cfg_cols("cod_cliente"),
        )

        # Tomar solo clientes que estan en base inicio mes y no en universo.
        df_ini_mes_fil = df_ini_mes_fil[
            ~df_ini_mes_fil["Cod Cliente"].isin(df_unviverso_fil["Cod Cliente"])
        ]

        dict_reemplazos_jv = gf.crear_diccionario_desde_dataframe(
            df=df_unviverso,
            col_clave=self.cfg_cols("cod_jefe_vtas"),
            col_valor=self.cfg_cols("nom_jefe_vtas"),
        )
        # Traer nombre correcto jefe de vtas.
        df_ini_mes_fil = tf.reemplazar_columna_en_funcion_de_otra(
            df=df_ini_mes_fil,
            nom_columna_de_referencia=self.cfg_cols("cod_jefe_vtas"),
            nom_columna_a_reemplazar=self.cfg_cols("nom_jefe_vtas"),
            mapeo=dict_reemplazos_jv,
        )

        # Duplicar columnas constantes.
        df_ini_mes_fil = tf.duplicar_columnas_cfg(
            df=df_ini_mes_fil,
            duplicaciones=self.cfg("base_inicio_mes_dir", "cols_duplicar"),
        )

        df_unviverso_fil = tf.duplicar_columnas_cfg(
            df=df_unviverso_fil,
            duplicaciones=self.cfg("universo_directa", "cols_duplicar"),
        )

        # Extraer la tabla de tipologías del diccionario de drivers
        drv_tipologias = self.dict_drivers.get("Tipologías")

        df_ini_mes_ren_copy = df_ini_mes_fil.copy()

        # Lógica de negocio merge sucesivos con el drv_tipologias usando la configuración establecida.
        df_unviverso_fil = tf.pd_left_merge_two_keys(
            base_left=df_unviverso_fil,
            base_right=drv_tipologias,
            left_key=self.cfg_cols("cod_tipologia"),
        )

        df_ini_mes_merge = tf.pd_left_merge_two_keys(
            base_left=df_ini_mes_ren_copy,
            base_right=drv_tipologias,
            left_key=self.cfg_cols("cod_tipologia"),
        )
        # Traer información de driver regional
        drv_region = self.dict_drivers.get("Regionales")

        df_unviverso_fil = tf.pd_left_merge_two_keys(
            base_left=df_unviverso_fil,
            base_right=drv_region,
            left_key=self.cfg_cols("cod_oficina"),
        )

        df_ini_mes_merge_reg = tf.pd_left_merge_two_keys(
            base_left=df_ini_mes_merge,
            base_right=drv_region,
            left_key=self.cfg_cols("cod_oficina"),
        )
        # Traer información del driver municipios (Universo / base inicio mes)
        drv_municipios = self.dict_drivers.get("Municipios")

        # Tratar datos de municipios para garantizar el cruce completo del mege
        drv_municipios.loc[:, self.cfg_cols("municipio")] = drv_municipios[
            self.cfg_cols("municipio")
        ].str.lower()

        df_unviverso_fil.loc[:, self.cfg_cols("municipio")] = df_unviverso_fil[
            self.cfg_cols("municipio")
        ].str.lower()

        # Tnasformación para relacionar municipio y departamento base y driver
        df_ini_mes_merge_reg = merge(
            left=df_ini_mes_merge_reg,
            right=drv_municipios.drop(
                columns=self.cfg_cols("municipio")
            ).drop_duplicates(
                subset=[
                    self.cfg_cols("cod_poblacion"),
                    self.cfg_cols("cod_departamento"),
                ]
            ),
            on=[
                self.cfg_cols("cod_poblacion"),
                self.cfg_cols("cod_departamento"),
            ],
            how="left",
        )

        df_unviverso_fil = merge(
            left=df_unviverso_fil,
            right=drv_municipios,
            on=[self.cfg_cols("municipio"), self.cfg_cols("cod_departamento")],
            how="left",
        )

        df_unviverso_fil.loc[:, self.FUENTE] = self.VALOR_UNIVERSO
        df_ini_mes_merge_reg.loc[:, self.FUENTE] = self.VALOR_BASE_INICIO_MES

        df_base_completa = concat(
            objs=[df_unviverso_fil, df_ini_mes_merge_reg], join="inner"
        )

        # Ajustar jefes de ventas y vendedores finales.
        mask = (
            df_base_completa[self.cfg_cols("cod_jefe_vtas")]
            == self.cfg_cols("valor_guion")
        ) & (
            df_base_completa[self.cfg_cols("nom_jefe_vtas")]
            == self.cfg_cols("valor_guion")
        )

        df_base_completa.loc[mask, self.cfg_cols("cod_jefe_vtas")] = (
            df_base_completa.loc[mask, self.cfg_cols("cod_vendedor")]
        )
        df_base_completa.loc[mask, self.cfg_cols("nom_jefe_vtas")] = (
            df_base_completa.loc[mask, self.cfg_cols("nom_vendedor")]
        )

        mask_kam = df_base_completa[self.cfg_cols("nom_jefe_vtas")] == self.cfg_cols(
            "valor_KAM"
        )

        df_base_completa.loc[mask_kam, self.cfg_cols("cod_jefe_vtas")] = "1"

        # Extraer columnas que contienen nulos
        cols_con_nulos = df_base_completa.columns[
            df_base_completa.isna().any()
        ].tolist()

        df_base_completa[self.cfg_cols("coord_unif")] = df_base_completa[
            self.cfg_cols("coord_unif")
        ].replace(self.LISTA_COORD_NULL, self.cfg_cols("valor_guion"), regex=False)

        df_base_completa = tf.remplazar_nulos_multiples_columnas_pd(
            base=df_base_completa,
            list_columns=cols_con_nulos,
            value=self.cfg_cols("valor_nulo"),
        )

        # Tratar datos de municipios para homologar nombres
        df_base_completa.loc[:, self.cfg_cols("municipio")] = df_base_completa[
            self.cfg_cols("municipio")
        ].str.upper()

        df_base_completa_select = tf.seleccionar_columnas_pd(
            df=df_base_completa, cols_elegidas=self.cfg("cols_finales")
        )

        df_base_completa_select = df_base_completa_select.copy()

        df_base_completa_select = agregar_conteo_duplicados(
            df=df_base_completa_select,
            col=self.cfg_cols("cliente"),
            col_salida="duplicados",
        )

        gf.exportar_a_excel(
            ruta_archivo=self.cfg("path_guardado"), df=df_base_completa_select
        )

        logger.info("=== Proceso Directa finalizado ===\n")
