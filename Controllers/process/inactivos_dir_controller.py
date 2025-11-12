from loguru import logger
from typing import Dict
from Utils.data_quality_functions import verificar_columnas
from pandas import DataFrame, merge, concat
import Utils.general_functions as gf
import Utils.transformation_functions as tf
from Utils.proyect_functions import eliminar_duplicados_por_prioridad


class ProcesoDirectaInactivos:
    """Proceso para la parte Directa del proyecto."""

    FUENTE = "Fuente"
    # VALOR_UNIVERSO = "universo"
    # VALOR_BASE_INICIO_MES = "base_inicio_mes"
    LISTA_COORD_NULL = ["0, 0", ", "]

    def __init__(
        self, cfg_directa: Dict, cfg_cols: Dict, dict_drivers: Dict[str, DataFrame]
    ):
        self.cfg = cfg_directa
        self.cfg_cols = cfg_cols
        self.dict_drivers = dict_drivers

    def ejecutar(self):
        logger.info("\n=== Iniciando proceso INACTIVOS DIRECTA ===")

        COLS_BASE_INACTIVOS = [*self.cfg("maestra_inactivos_dir", "renombrar_cols")]

        # Validar columnas previamente cargando una pequeña parte del insumo
        df_ini_mes_min = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_dir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_dir", "nom_hoja"),
            modo_pruebas=True,
        )
        # Validación de columnas esperadas
        verificar_columnas(
            df=df_ini_mes_min,
            columnas_esperadas=COLS_BASE_INACTIVOS,
            nombre_arc=self.cfg("maestra_inactivos_dir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_dir", "nom_hoja"),
        )

        df_maes_inac = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_dir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_dir", "nom_hoja"),
            cols=COLS_BASE_INACTIVOS,
            # modo_pruebas=True,
        )

        df_maes_inac = tf.renombrar_columnas_con_diccionario(
            df=df_maes_inac,
            cols_to_rename=self.cfg("maestra_inactivos_dir", "renombrar_cols"),
        )

        # Eliminar duplicados por orden de prioridad cód vendedor.
        df_maes_inac_fil = eliminar_duplicados_por_prioridad(
            df=df_maes_inac,
            col_clave=self.cfg_cols("cod_cliente"),
            col_prioridad=self.cfg_cols("funcion_inter"),
            orden_prioridad=self.cfg(
                "maestra_inactivos_dir", "orden_prioridad_jv_vend"
            ),
        )

        df_maes_inac_fil = tf.modificar_caracteres_columna_pd(
            df=df_maes_inac_fil,
            col=self.cfg_cols("cod_cliente"),
            n=2,
        )

        df_maes_inac_fil = tf.concatenar_columnas_pd(
            df=df_maes_inac_fil,
            cols_elegidas=[self.cfg_cols("coord_y"), self.cfg_cols("coord_x")],
            nueva_columna=self.cfg_cols("coord_unif"),
            separador=", ",
            usar_separador=True,
        )

        # Extraer la tabla de tipologías del diccionario de drivers
        drv_tipologias = self.dict_drivers.get("Tipologías")

        df_maes_inac_fil_copy = df_maes_inac_fil.copy()

        # Lógica de negocio merge sucesivos con el drv_tipologias usando la configuración establecida.
        df_maes_inac_merge = tf.pd_left_merge_two_keys(
            base_left=df_maes_inac_fil_copy,
            base_right=drv_tipologias,
            left_key=self.cfg_cols("cod_tipologia"),
        )

        # Traer información de driver regional
        drv_region = self.dict_drivers.get("Regionales")

        df_maes_inac_merge = tf.pd_left_merge_two_keys(
            base_left=df_maes_inac_merge,
            base_right=drv_region,
            left_key=self.cfg_cols("cod_oficina"),
        )
        # Traer información del driver municipios (Universo / base inicio mes)
        drv_municipios = self.dict_drivers.get("Municipios")

        # Tratar datos de municipios para garantizar el cruce completo del mege
        drv_municipios.loc[:, self.cfg_cols("municipio")] = drv_municipios[
            self.cfg_cols("municipio")
        ].str.lower()

        # Tnasformación para relacionar municipio y departamento base y driver
        df_maes_inac_merge = merge(
            left=df_maes_inac_merge,
            right=drv_municipios.drop_duplicates(
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

        # Ajustar vendedores
        df_maes_inac_merge[self.cfg_cols("cod_vendedor")] = self.cfg_cols("valor_guion")
        df_maes_inac_merge[self.cfg_cols("nom_vendedor")] = self.cfg_cols("valor_guion")

        # Agregar columnas constantes.
        df_maes_inac_merge[self.cfg_cols("cod_actual")] = df_maes_inac_merge[
            self.cfg_cols("cod_cliente")
        ]
        df_maes_inac_merge[self.cfg_cols("cliente")] = df_maes_inac_merge[
            self.cfg_cols("cod_cliente")
        ]

        # Extraer columnas que contienen nulos
        cols_con_nulos = df_maes_inac_merge.columns[
            df_maes_inac_merge.isna().any()
        ].tolist()

        df_maes_inac_merge[self.cfg_cols("coord_unif")] = df_maes_inac_merge[
            self.cfg_cols("coord_unif")
        ].replace(self.LISTA_COORD_NULL, self.cfg_cols("valor_guion"), regex=False)

        df_maes_inac_merge = tf.remplazar_nulos_multiples_columnas_pd(
            base=df_maes_inac_merge,
            list_columns=cols_con_nulos,
            value=self.cfg_cols("valor_nulo"),
        )

        # Tratar datos de municipios para homologar nombres
        df_maes_inac_merge.loc[:, self.cfg_cols("municipio")] = df_maes_inac_merge[
            self.cfg_cols("municipio")
        ].str.upper()

        cols_finales = self.cfg("cols_finales")

        cols_finales.remove(self.FUENTE)

        df_base_completa_select = tf.seleccionar_columnas_pd(
            df=df_maes_inac_merge,
            cols_elegidas=cols_finales,
        )
        df_base_completa_select.loc[:, "Barrio"] = self.cfg_cols("valor_nulo")

        gf.exportar_a_excel(
            ruta_archivo=self.cfg("maestra_inactivos_dir", "path_guardado"),
            df=df_base_completa_select,
        )

        logger.info("=== Proceso Directa finalizado ===\n")
