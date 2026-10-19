import re

from psycopg.errors import ForeignKeyViolation

from configuracion.base_datos import obtener_conexion


class RepositorioGenerico:
    """
    Ejecuta el SQL de CUALQUIER modulo usando su ConfiguracionModulo.
    Es la unica implementacion para todas las tablas del sistema.

    Soporta campos de RETORNO de referencias (guardar=False): el listado
    hace un JOIN automatico con la tabla referenciada para mostrar sus
    descripciones sin duplicarlas en la tabla principal.

    Seguridad SQL:
    - Los VALORES siempre van como parametros %s.
    - Tablas y columnas (nombres dinamicos) se validan contra una
      expresion segura antes de construir el SQL.
    """

    # Identificadores validos: letras, numeros y guion bajo.
    _IDENTIFICADOR_VALIDO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, configuracion, filtro=None):
        self.configuracion = configuracion
        self.filtro = dict(filtro or {})
        self._alias_referencias = {}  # campo_referencia -> alias del JOIN

    # ---------------------------------------------------------------
    #   Ayudas privadas
    # ---------------------------------------------------------------
    def _validar_identificadores(self, nombres):
        """Rechaza cualquier nombre que no sea un identificador seguro."""
        for nombre in nombres:
            if not self._IDENTIFICADOR_VALIDO.fullmatch(nombre):
                raise ValueError(f"Identificador SQL no valido: {nombre}")

    def _columnas_guardables(self, valores):
        """Columnas a guardar: solo campos configurados y presentes."""
        columnas = [
            c.nombre
            for c in self.configuracion.campos_que_se_guardan()
            if c.nombre in valores
        ]
        self._validar_identificadores(columnas)
        return columnas

    def _preparar_valores_guardados(self, valores):
        """
        Ajusta los valores antes de guardar:
        - el campo secreto (clave de acceso) se encripta;
        - si el campo secreto llega vacio se omite (no se cambia la clave).
        """
        configuracion = self.configuracion
        valores = dict(valores)
        if configuracion.campo_secreto and configuracion.campo_secreto in valores:
            if valores[configuracion.campo_secreto] in (None, ""):
                valores.pop(configuracion.campo_secreto)
            else:
                from nucleo.seguridad import encriptar_clave
                valores[configuracion.campo_secreto] = encriptar_clave(
                    str(valores[configuracion.campo_secreto])
                )
        return valores

    def _preparar_listado(self):
        """
        Construye las columnas del SELECT y los JOIN de referencias.
        Devuelve (columnas_dict, columnas_select, clausula_joins).
        """
        configuracion = self.configuracion
        columnas_dict = []
        columnas_select = []
        joins = []

        # Columnas normales: las que se guardan en la tabla.
        guardables = configuracion.campos_que_se_guardan()
        self._validar_identificadores(
            [configuracion.tabla] + [c.nombre for c in guardables]
        )
        for campo in guardables:
            columnas_select.append(f"{configuracion.tabla}.{campo.nombre}")
            columnas_dict.append(campo.nombre)

        # Campos de retorno (guardar=False): JOIN con la tabla referenciada.
        self._alias_referencias = {}
        for campo in configuracion.campos:
            if campo.referencia is None:
                continue
            for destino, origen in campo.referencia.campos_retorno.items():
                modulo_ref = campo.referencia.modulo
                self._validar_identificadores(
                    [modulo_ref.tabla, campo.nombre,
                     modulo_ref.clave_primaria, origen, destino]
                )
                if campo.nombre not in self._alias_referencias:
                    alias = f"ref_{len(self._alias_referencias) + 1}"
                    self._alias_referencias[campo.nombre] = alias
                    joins.append(
                        f"LEFT JOIN {modulo_ref.tabla} {alias} "
                        f"ON {alias}.{modulo_ref.clave_primaria} = "
                        f"{configuracion.tabla}.{campo.nombre}"
                    )
                alias = self._alias_referencias[campo.nombre]
                columnas_select.append(f"{alias}.{origen} AS {destino}")
                columnas_dict.append(destino)

        return columnas_dict, columnas_select, " ".join(joins)

    def _calificar(self, nombre_campo):
        """
        Nombre listo para el SQL (tabla.columna o alias.columna de retorno).
        """
        configuracion = self.configuracion
        campo = configuracion.obtener_campo(nombre_campo)
        if campo is None:
            return f"{configuracion.tabla}.{nombre_campo}"
        if campo.guardar:
            return f"{configuracion.tabla}.{campo.nombre}"

        # Campo de retorno: pertenece a la tabla referenciada.
        for candidato in configuracion.campos:
            if candidato.referencia is None:
                continue
            if nombre_campo in candidato.referencia.campos_retorno:
                origen = candidato.referencia.campos_retorno[nombre_campo]
                alias = self._alias_referencias.get(candidato.nombre)
                if alias is not None:
                    return f"{alias}.{origen}"
        return f"{configuracion.tabla}.{nombre_campo}"

    def _consulta_listado(self, where="", parametros=()):
        """SQL base de listado: select + joins + filtro + orden."""
        columnas_dict, columnas_select, joins = self._preparar_listado()
        configuracion = self.configuracion
        condiciones = []
        valores_filtro = []
        self._validar_identificadores([configuracion.tabla, *self.filtro])
        for columna, valor in self.filtro.items():
            if valor is None:
                condiciones.append(f"{configuracion.tabla}.{columna} IS NULL")
            else:
                condiciones.append(f"{configuracion.tabla}.{columna} = %s")
                valores_filtro.append(valor)
        if where:
            condiciones.append(where.removeprefix("WHERE "))
        clausula_where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        self._validar_identificadores([configuracion.orden_por])
        orden = "DESC" if configuracion.orden_desc else "ASC"
        sql = (
            f"SELECT {', '.join(columnas_select)} "
            f"FROM {configuracion.tabla} {joins} "
            f"{clausula_where} "
            f"ORDER BY {self._calificar(configuracion.orden_por)} {orden}"
        )
        return sql, columnas_dict, valores_filtro + list(parametros)

    def _ejecutar_escritura(self, sql, parametros):
        """Ejecuta una escritura con commit/rollback y cierre automaticos."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def _consultar(self, sql, parametros):
        """Ejecuta una consulta y devuelve las filas crudas."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return filas

    @staticmethod
    def _filas_a_diccionarios(columnas, filas):
        """Convierte filas del cursor en listas de diccionarios."""
        return [dict(zip(columnas, fila)) for fila in filas]

    # ---------------------------------------------------------------
    #   Operaciones publicas (API del repositorio)
    # ---------------------------------------------------------------
    def listar(self):
        """Devuelve todos los registros ordenados segun la configuracion."""
        sql, columnas, parametros = self._consulta_listado()
        return self._filas_a_diccionarios(columnas, self._consultar(sql, parametros))

    def buscar(self, texto, campo=None):
        """
        Filtra registros donde el campo contenga el texto (sin distinguir
        mayusculas). Si el texto esta vacio, devuelve todo.
        """
        configuracion = self.configuracion
        campo = campo or configuracion.buscar_por
        texto = texto.strip()
        if not texto:
            return self.listar()

        sql, columnas, parametros = self._consulta_listado(
            where=f"CAST({self._calificar(campo)} AS TEXT) ILIKE %s",
            parametros=[f"%{texto}%"],
        )
        return self._filas_a_diccionarios(columnas, self._consultar(sql, parametros))

    def buscar_exacto(self, texto, campo=None):
        """Coincidencia EXACTA (util para logins, RUC y codigos unicos)."""
        configuracion = self.configuracion
        campo = campo or configuracion.buscar_por
        sql, columnas, parametros = self._consulta_listado(
            where=f"{self._calificar(campo)} = %s",
            parametros=[texto],
        )
        return self._filas_a_diccionarios(columnas, self._consultar(sql, parametros))

    def obtener_por_clave(self, clave):
        """Devuelve un registro por su clave primaria, o None si no existe."""
        configuracion = self.configuracion
        self._validar_identificadores([configuracion.clave_primaria])
        sql, columnas, parametros = self._consulta_listado(
            where=f"{self._calificar(configuracion.clave_primaria)} = %s",
            parametros=[clave],
        )
        filas = self._consultar(sql, parametros)
        return self._filas_a_diccionarios(columnas, filas)[0] if filas else None

    def insertar(self, valores):
        """Inserta un registro. valores: {nombre_campo: valor}."""
        valores = self._preparar_valores_guardados(valores)
        columnas = self._columnas_guardables(valores)
        configuracion = self.configuracion
        if not columnas:
            raise ValueError("No hay datos para guardar.")
        sql = (
            f"INSERT INTO {configuracion.tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(['%s'] * len(columnas))})"
        )
        parametros = [valores[columna] for columna in columnas]
        self._ejecutar_escritura(sql, parametros)

    def actualizar(self, clave_original, valores):
        """
        Actualiza el registro cuya clave es clave_original.
        La clave primaria nunca aparece en el SET (no debe cambiarse).
        """
        valores = self._preparar_valores_guardados(valores)
        columnas = [
            c for c in self._columnas_guardables(valores)
            if c != self.configuracion.clave_primaria
        ]
        configuracion = self.configuracion
        if not columnas:
            raise ValueError("No hay datos para actualizar.")
        self._validar_identificadores([configuracion.clave_primaria])
        sql = (
            f"UPDATE {configuracion.tabla} "
            f"SET {', '.join(f'{c} = %s' for c in columnas)} "
            f"WHERE {configuracion.clave_primaria} = %s"
        )
        parametros = [valores[c] for c in columnas] + [clave_original]
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
                if cursor.rowcount == 0:
                    raise ValueError("El registro ya no existe en la base de datos.")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def eliminar(self, clave):
        """Elimina el registro con la clave indicada."""
        configuracion = self.configuracion
        self._validar_identificadores([configuracion.clave_primaria])
        sql = (
            f"DELETE FROM {configuracion.tabla} "
            f"WHERE {configuracion.clave_primaria} = %s"
        )
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(sql, [clave])
                if cursor.rowcount == 0:
                    raise ValueError("El registro ya no existe en la base de datos.")
            conexion.commit()
        except ForeignKeyViolation:
            conexion.rollback()
            raise
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def calcular_siguiente_codigo(self):
        """Devuelve el proximo valor del campo_codigo (MAX + 1)."""
        configuracion = self.configuracion
        campo = configuracion.campo_siguiente_codigo()
        if campo is None:
            return None
        self._validar_identificadores(
            [configuracion.tabla, campo.nombre]
        )
        sql = (
            f"SELECT COALESCE(MAX({campo.nombre}), 0) + 1 "
            f"FROM {configuracion.tabla}"
        )
        return self._consultar(sql, [])[0][0]