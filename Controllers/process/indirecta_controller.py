from loguru import logger
from pandas import DataFrame, merge, concat
from Utils.data_quality_functions import verificar_columnas
from typing import Dict
import Utils.general_functions as gf
import Utils.transformation_functions as tf
from Utils.proyect_functions import agregar_conteo_duplicados


class ProcesoIndirecta:
    """Proceso para la parte Indirecta del proyecto."""

    FUENTE = "Fuente"
    VALOR_UNIVERSO = "universo"
    VALOR_BASE_INICIO_MES = "base_inicio_mes"
    LISTA_COORD_NULL = ["0, 0 ", ", ", "0.0, 0.0"]

    def __init__(
        self, cfg_indirecta: Dict, cfg_cols: Dict, dict_drivers: Dict[str, DataFrame]
    ):
        self.cfg = cfg_indirecta
        self.cfg_cols = cfg_cols
        self.dict_drivers = dict_drivers

    def ejecutar(self, parcial: bool = False):
        logger.info("\n=== Iniciando proceso INDIRECTA ===")

        COLS_UNIVERSO = [*self.cfg("universo_indirecta", "renombrar_cols")]
        COLS_BASE_IN_MES = [*self.cfg("base_inicio_mes_indir", "renombrar_cols")]

        df_unviverso_min = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("universo_indirecta", "nom_base"),
            nom_hoja=self.cfg("universo_indirecta", "nom_hoja"),
            engine="pyxlsb",
            modo_pruebas=True,
        )

        df_ini_mes_min = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("base_inicio_mes_indir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_indir", "nom_hoja"),
            modo_pruebas=True,
        )
        # Validación de columnas esperadas
        verificar_columnas(
            df=df_unviverso_min,
            columnas_esperadas=COLS_UNIVERSO,
            nombre_arc=self.cfg("universo_indirecta", "nom_base"),
            nom_hoja=self.cfg("universo_indirecta", "nom_hoja"),
        )
        verificar_columnas(
            df=df_ini_mes_min,
            columnas_esperadas=COLS_BASE_IN_MES,
            nombre_arc=self.cfg("base_inicio_mes_indir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_indir", "nom_hoja"),
        )
        # Carga insumos proceso indirecta.
        df_unviverso = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("universo_indirecta", "nom_base"),
            nom_hoja=self.cfg("universo_indirecta", "nom_hoja"),
            engine="pyxlsb",
            cols=COLS_UNIVERSO,
            modo_pruebas=False,
        )
        df_unviverso_wtout_dup = df_unviverso.drop_duplicates()

        df_ini_mes = gf.lectura_insumos_excel(
            path=self.cfg("path"),
            nom_insumo=self.cfg("base_inicio_mes_indir", "nom_base"),
            nom_hoja=self.cfg("base_inicio_mes_indir", "nom_hoja"),
            cols=COLS_BASE_IN_MES,
            modo_pruebas=False,
        )

        df_ini_mes_ren = tf.renombrar_columnas_con_diccionario(
            df=df_ini_mes,
            cols_to_rename=self.cfg("base_inicio_mes_indir", "renombrar_cols"),
        )

        df_unviverso_ren = tf.renombrar_columnas_con_diccionario(
            df=df_unviverso_wtout_dup,
            cols_to_rename=self.cfg("universo_indirecta", "renombrar_cols"),
        )

        # Obtener coordenadas completas.
        df_ini_mes_ren = tf.concatenar_columnas_pd(
            df=df_ini_mes_ren,
            cols_elegidas=[self.cfg_cols("coord_y"), self.cfg_cols("coord_x")],
            nueva_columna=self.cfg_cols("coord_unif"),
            separador=", ",
            usar_separador=True,
        )
        # Tomar columnas referentes a cordenadas (Pregunta Agente - cliente)
        df_ini_mes_coord = tf.seleccionar_columnas_pd(
            df=df_ini_mes_ren,
            cols_elegidas=[
                self.cfg_cols("cod_jefe_vtas"),
                self.cfg_cols("cod_cliente"),
                self.cfg_cols("coord_unif"),
            ],
        )
        # Traer las coordenadas unificadas al universo.
        df_unviverso_merge = merge(
            left=df_unviverso_ren,
            right=df_ini_mes_coord.drop_duplicates(),
            on=[
                self.cfg_cols("cod_jefe_vtas"),
                self.cfg_cols("cod_cliente"),
            ],
            how="left",
        )
        # Crear columna cliente.
        df_ini_mes_ren = tf.concatenar_columnas_pd(
            df=df_ini_mes_ren,
            cols_elegidas=[
                self.cfg_cols("cod_jefe_vtas"),
                self.cfg_cols("cod_cliente"),
            ],
            nueva_columna=self.cfg_cols("cliente"),
        )
        df_unviverso_merge = tf.concatenar_columnas_pd(
            df=df_unviverso_merge,
            cols_elegidas=[
                self.cfg_cols("cod_jefe_vtas"),
                self.cfg_cols("cod_cliente"),
            ],
            nueva_columna=self.cfg_cols("cliente"),
        )
        # Tomar solo clientes que estan en base inicio mes y no en universo.
        df_ini_mes_ren = df_ini_mes_ren[
            ~df_ini_mes_ren[self.cfg_cols("cliente")].isin(
                df_unviverso_merge[self.cfg_cols("cliente")]
            )
        ]

        df_unviverso_merge.sort_values(by=self.cfg_cols["cod_vendedor"], ascending=True)

        df_unviverso_merge = df_unviverso_merge.drop_duplicates(
            subset=[self.cfg_cols("cliente")]
        )

        dict_reemplazos_jv = gf.crear_diccionario_desde_dataframe(
            df=df_unviverso_merge,
            col_clave=self.cfg_cols("cod_jefe_vtas"),
            col_valor=self.cfg_cols("nom_jefe_vtas"),
        )
        # Traer nombre correcto jefe de vtas.
        df_ini_mes_ren = tf.reemplazar_columna_en_funcion_de_otra(
            df=df_ini_mes_ren,
            nom_columna_de_referencia=self.cfg_cols("cod_jefe_vtas"),
            nom_columna_a_reemplazar=self.cfg_cols("nom_jefe_vtas"),
            mapeo=dict_reemplazos_jv,
        )

        # Aignar columas constantes indirecta (base inicio mes y universo)
        for cada_col, cada_valor in self.cfg(
            "base_inicio_mes_indir", "dict_cols_constantes"
        ).items():
            df_ini_mes_ren[cada_col] = cada_valor

        df_unviverso_merge[self.cfg_cols("funcion_inter")] = self.cfg_cols(
            "valor_guion"
        )

        # Ajustar las columnas: Cód. Canal/ Cód. Sub Canal Cód./Segmento) transformado.
        df_ini_mes_ren = tf.modificar_caracteres_columna_pd(
            df=df_ini_mes_ren,
            col=self.cfg_cols("cod_tipologia"),
            n=2,
            accion="conservar",
        )

        # Extraer la tabla de tipologías del diccionario de drivers
        drv_tipologias = self.dict_drivers.get("Tipologías")

        #  Diccionario con las configuraciones de columnas
        df_ini_mes_ren_copy = df_ini_mes_ren.copy()

        # Lógica de negocio merge sucesivos con el drv_tipologias usando la configuración establecida.
        df_ini_mes_merge = tf.pd_left_merge_two_keys(
            base_left=df_ini_mes_ren_copy,
            base_right=drv_tipologias,
            left_key=self.cfg_cols("cod_tipologia"),
        )
        # Traer información de driver regional
        drv_region = self.dict_drivers.get("Regionales")

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

        # Tnasformación para relacionar municipio y departamento base y driver
        df_ini_mes_merge_reg = merge(
            left=df_ini_mes_merge_reg,
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

        df_unviverso_merge = merge(
            left=df_unviverso_merge,
            right=drv_municipios.drop_duplicates(subset=self.cfg_cols("cod_poblacion")),
            on=[self.cfg_cols("cod_poblacion")],
            how="left",
        )

        df_unviverso_merge.loc[:, self.FUENTE] = self.VALOR_UNIVERSO
        df_ini_mes_merge_reg.loc[:, self.FUENTE] = self.VALOR_BASE_INICIO_MES

        # Tratar canales / subcanal / segmentos restantes
        df_ini_mes_merge_reg = tf.reemplazar_nulos_con_dict(
            df=df_ini_mes_merge_reg,
            valores_por_defecto=self.cfg(
                "base_inicio_mes_indir", "dict_cn_sub_seg_null"
            ),
        )

        df_base_completa = concat(
            objs=[df_unviverso_merge, df_ini_mes_merge_reg], join="inner"
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

        #  Determinar registros con elementos nulos (Municipio)
        df_nulos_mun = df_base_completa[
            df_base_completa[self.cfg_cols("municipio")].isnull()
        ]

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

        # Seleccionar cols finales
        df_final_select = tf.seleccionar_columnas_pd(
            df=df_base_completa, cols_elegidas=self.cfg("cols_finales")
        )
        df_nulos_select = tf.seleccionar_columnas_pd(
            df=df_nulos_mun,
            cols_elegidas=self.cfg("cols_finales") + [self.cfg_cols("cod_poblacion")],
        )

        df_final_select = agregar_conteo_duplicados(
            df=df_final_select,
            col=self.cfg_cols("cliente"),
            col_salida="duplicados",
        )

        # Exportar resultados
        gf.exportar_a_excel(ruta_archivo=self.cfg("path_nulos"), df=df_nulos_select)
        gf.exportar_a_excel(ruta_archivo=self.cfg("path_guardado"), df=df_final_select)

        logger.info("=== Proceso Indirecta finalizado ===\n")
