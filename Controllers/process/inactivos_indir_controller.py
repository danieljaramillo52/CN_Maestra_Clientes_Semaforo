from loguru import logger
from pandas import DataFrame, merge, concat
from Utils.data_quality_functions import verificar_columnas
from typing import Dict
import Utils.general_functions as gf
import Utils.transformation_functions as tf


class ProcesoIndirectaInactivos:
    """Proceso para la parte Indirecta del proyecto."""

    FUENTE = "Fuente"
    LISTA_COORD_NULL = ["0, 0 ", ", ", "0.0, 0.0"]

    def __init__(
        self, cfg_indirecta: Dict, cfg_cols: Dict, dict_drivers: Dict[str, DataFrame]
    ):
        self.cfg = cfg_indirecta
        self.cfg_cols = cfg_cols
        self.dict_drivers = dict_drivers

    def ejecutar(self, parcial: bool = False):
        logger.info("\n=== Iniciando proceso INACTIVOS INDIRECTA ===")

        COLS_AMOVIL = [*self.cfg("maestra_inactivos_amovil", "renombrar_cols")]
        COLS_DF_INAC_INDIR = [*self.cfg("maestra_inactivos_indir", "renombrar_cols")]

        df_inac_amovil = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_amovil", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_amovil", "nom_hoja"),
            modo_pruebas=True,
        )
        df_inac_amovil.columns = df_inac_amovil.columns.str.strip().str.upper()

        # Eliminar columnas no coincidentes si exsiten.
        df_inac_indir = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_indir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_indir", "nom_hoja"),
            modo_pruebas=True,
        )

        # Validación de columnas esperadas
        verificar_columnas(
            df=df_inac_amovil,
            columnas_esperadas=COLS_AMOVIL,
            nombre_arc=self.cfg("maestra_inactivos_amovil", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_amovil", "nom_hoja"),
        )
        verificar_columnas(
            df=df_inac_indir,
            columnas_esperadas=COLS_DF_INAC_INDIR,
            nombre_arc=self.cfg("maestra_inactivos_indir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_indir", "nom_hoja"),
        )
        # Carga insumos proceso indirecta.
        df_inac_amovil = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_amovil", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_amovil", "nom_hoja"),
            modo_pruebas=True,
        )

        df_inac_amovil.columns = df_inac_amovil.columns.str.strip().str.upper()

        df_inac_amovil = tf.seleccionar_columnas_pd(
            df=df_inac_amovil, cols_elegidas=COLS_AMOVIL
        )

        df_inidir_inac = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("maestra_inactivos_indir", "nom_base"),
            nom_hoja=self.cfg("maestra_inactivos_indir", "nom_hoja"),
            cols=COLS_DF_INAC_INDIR,
            modo_pruebas=True,
        )

        df_inidir_inac_ren = tf.renombrar_columnas_con_diccionario(
            df=df_inidir_inac,
            cols_to_rename=self.cfg("maestra_inactivos_indir", "renombrar_cols"),
        )

        df_inac_amovil_ren = tf.renombrar_columnas_con_diccionario(
            df=df_inac_amovil,
            cols_to_rename=self.cfg("maestra_inactivos_amovil", "renombrar_cols"),
        )

        # Concatenar dfs.
        df_inac_indir_complto = concat([df_inac_amovil_ren, df_inidir_inac_ren])

        # Obtener coordenadas completas.
        df_inac_indir_complto = tf.concatenar_columnas_pd(
            df=df_inac_indir_complto,
            cols_elegidas=[self.cfg_cols("coord_y"), self.cfg_cols("coord_x")],
            nueva_columna=self.cfg_cols("coord_unif"),
            separador=", ",
            usar_separador=True,
        )

        # Aignar columas constantes indirecta (base inicio mes y universo)
        for cada_col, cada_valor in self.cfg(
            "base_inicio_mes_indir", "dict_cols_constantes"
        ).items():
            df_inac_indir_complto[cada_col] = cada_valor

        # Ajustar las columnas: Cód. Canal/ Cód. Sub Canal Cód./Segmento) transformado.
        df_inac_indir_complto = tf.modificar_caracteres_columna_pd(
            df=df_inac_indir_complto,
            col=self.cfg_cols("cod_tipologia"),
            n=2,
            accion="conservar",
        )

        # Extraer la tabla de tipologías del diccionario de drivers
        drv_tipologias = self.dict_drivers.get("Tipologías")

        df_inac_indir_complto_copy = df_inac_indir_complto.copy()

        # Lógica de negocio merge sucesivos con el drv_tipologias usando la configuración establecida.
        df_ind_inac_merge = tf.pd_left_merge_two_keys(
            base_left=df_inac_indir_complto_copy,
            base_right=drv_tipologias,
            left_key=self.cfg_cols("cod_tipologia"),
        )
        # Traer información de driver regional
        drv_region = self.dict_drivers.get("Regionales")

        df_ind_ina_merge_reg = tf.pd_left_merge_two_keys(
            base_left=df_ind_inac_merge,
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
        df_ind_ina_merge_reg = merge(
            left=df_ind_ina_merge_reg,
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

        # Tratar canales / subcanal / segmentos restantes
        df_ind_ina_merge_reg = tf.reemplazar_nulos_con_dict(
            df=df_ind_ina_merge_reg,
            valores_por_defecto=self.cfg(
                "base_inicio_mes_indir", "dict_cn_sub_seg_null"
            ),
        )

        # Crear columna cliente.
        df_base_completa = tf.concatenar_columnas_pd(
            df=df_ind_ina_merge_reg,
            cols_elegidas=[
                self.cfg_cols("cod_jefe_vtas"),
                self.cfg_cols("cod_cliente"),
            ],
            nueva_columna=self.cfg_cols("cliente"),
        )

        # Ajustar Nulos razón social.
        df_base_completa[self.cfg_cols("nombre_comercial")] = df_base_completa[
            self.cfg_cols("nombre_comercial")
        ].mask(
            df_base_completa[self.cfg_cols("nombre_comercial")].isna(),
            df_base_completa[self.cfg_cols("nombre_razon")],
        )

        cols_con_nulos = df_base_completa.columns[
            df_base_completa.isna().any()
        ].tolist()

        df_base_completa[self.cfg_cols("coord_unif")] = df_base_completa[
            self.cfg_cols("coord_unif")
        ].replace(self.LISTA_COORD_NULL, self.cfg_cols("valor_guion"), regex=False)

        # Reemplazar nulos por defecto.
        df_base_completa = tf.remplazar_nulos_multiples_columnas_pd(
            base=df_base_completa,
            list_columns=cols_con_nulos,
            value=self.cfg_cols("valor_nulo"),
        )

        df_base_completa.loc[:, self.cfg_cols("municipio")] = df_base_completa[
            self.cfg_cols("municipio")
        ].str.upper()

        # Ajustar Jefes de Venta (Agentes comerciales finales.)

        # Traer información del driver agentes.
        drv_ac = self.dict_drivers.get("Agentes Comerciales")

        dict_jefe_nom_jefe = gf.crear_diccionario_desde_dataframe(
            df=drv_ac,
            col_clave=self.cfg_cols("cod_jefe_vtas"),
            col_valor=self.cfg_cols("nom_jefe_vtas"),
        )
        df_base_completa = tf.reemplazar_columna_en_funcion_de_otra(
            df=df_base_completa,
            nom_columna_a_reemplazar=self.cfg_cols("nom_jefe_vtas"),
            nom_columna_de_referencia=self.cfg_cols("cod_jefe_vtas"),
            mapeo=dict_jefe_nom_jefe,
        )
        cols_finales = self.cfg("cols_finales")

        if self.FUENTE in cols_finales:
            cols_finales.remove(self.FUENTE)

        # Seleccionar cols finales
        df_final_select = tf.seleccionar_columnas_pd(
            df=df_base_completa, cols_elegidas=self.cfg("cols_finales")
        )

        # Exportar resultados
        gf.exportar_a_excel(
            ruta_archivo=self.cfg("maestra_inactivos_indir", "path_guardado"),
            df=df_final_select,
        )

        logger.info("=== Proceso Indirecta finalizado ===\n")
