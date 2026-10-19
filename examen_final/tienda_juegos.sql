-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';

-- DROP SEQUENCE public.cajas_sesiones_codigo_seq;

CREATE SEQUENCE public.cajas_sesiones_codigo_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.cajas_sesiones_codigo_seq OWNER TO postgres;
GRANT ALL ON SEQUENCE public.cajas_sesiones_codigo_seq TO postgres;

-- DROP SEQUENCE public.cobros_codigo_seq;

CREATE SEQUENCE public.cobros_codigo_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.cobros_codigo_seq OWNER TO postgres;
GRANT ALL ON SEQUENCE public.cobros_codigo_seq TO postgres;

-- DROP SEQUENCE public.medios_pago_codigo_seq;

CREATE SEQUENCE public.medios_pago_codigo_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.medios_pago_codigo_seq OWNER TO postgres;
GRANT ALL ON SEQUENCE public.medios_pago_codigo_seq TO postgres;

-- DROP SEQUENCE public.movimientos_stock_codigo_seq;

CREATE SEQUENCE public.movimientos_stock_codigo_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.movimientos_stock_codigo_seq OWNER TO postgres;
GRANT ALL ON SEQUENCE public.movimientos_stock_codigo_seq TO postgres;

-- DROP SEQUENCE public.pedidos_venta_codigo_seq;

CREATE SEQUENCE public.pedidos_venta_codigo_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.pedidos_venta_codigo_seq OWNER TO postgres;
GRANT ALL ON SEQUENCE public.pedidos_venta_codigo_seq TO postgres;
-- public.categorias definition

-- Drop table

-- DROP TABLE public.categorias;

CREATE TABLE public.categorias (
	codigo int4 NOT NULL,
	descripcion varchar(100) NOT NULL,
	CONSTRAINT grupo_item_codigo_not_null NOT NULL codigo,
	CONSTRAINT grupo_item_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT grupo_item_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.categorias OWNER TO postgres;
GRANT ALL ON TABLE public.categorias TO postgres;


-- public.editoriales definition

-- Drop table

-- DROP TABLE public.editoriales;

CREATE TABLE public.editoriales (
	codigo int4 NOT NULL,
	nombre varchar(100) NOT NULL,
	importado bool DEFAULT false NOT NULL,
	CONSTRAINT marcas_items_codigo_not_null NOT NULL codigo,
	CONSTRAINT marcas_items_importado_not_null NOT NULL importado,
	CONSTRAINT marcas_items_nombre_not_null NOT NULL nombre,
	CONSTRAINT marcas_items_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.editoriales OWNER TO postgres;
GRANT ALL ON TABLE public.editoriales TO postgres;


-- public.grupo_contacto definition

-- Drop table

-- DROP TABLE public.grupo_contacto;

CREATE TABLE public.grupo_contacto (
	codigo varchar(5) NOT NULL,
	descripcion varchar(100) NOT NULL,
	CONSTRAINT grupo_contacto_codigo_not_null NOT NULL codigo,
	CONSTRAINT grupo_contacto_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT grupo_contacto_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.grupo_contacto OWNER TO postgres;
GRANT ALL ON TABLE public.grupo_contacto TO postgres;


-- public.grupocto definition

-- Drop table

-- DROP TABLE public.grupocto;

CREATE TABLE public.grupocto (
	gcto_cod int4 NOT NULL,
	gcto_descripcion varchar(50) NOT NULL,
	CONSTRAINT grupocto_gcto_cod_not_null NOT NULL gcto_cod,
	CONSTRAINT grupocto_gcto_descripcion_not_null NOT NULL gcto_descripcion,
	CONSTRAINT grupocto_pkey PRIMARY KEY (gcto_cod)
);

-- Permissions

ALTER TABLE public.grupocto OWNER TO postgres;
GRANT ALL ON TABLE public.grupocto TO postgres;


-- public.mecanicas definition

-- Drop table

-- DROP TABLE public.mecanicas;

CREATE TABLE public.mecanicas (
	codigo int4 NOT NULL,
	descripcion varchar(100) NOT NULL,
	CONSTRAINT sector_item_codigo_not_null NOT NULL codigo,
	CONSTRAINT sector_item_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT sector_item_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.mecanicas OWNER TO postgres;
GRANT ALL ON TABLE public.mecanicas TO postgres;


-- public.medios_pago definition

-- Drop table

-- DROP TABLE public.medios_pago;

CREATE TABLE public.medios_pago (
	codigo serial4 NOT NULL,
	descripcion varchar(50) NOT NULL,
	es_efectivo bool DEFAULT false NOT NULL,
	activo bool DEFAULT true NOT NULL,
	CONSTRAINT medios_pago_activo_not_null NOT NULL activo,
	CONSTRAINT medios_pago_codigo_not_null NOT NULL codigo,
	CONSTRAINT medios_pago_descripcion_key UNIQUE (descripcion),
	CONSTRAINT medios_pago_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT medios_pago_es_efectivo_not_null NOT NULL es_efectivo,
	CONSTRAINT medios_pago_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.medios_pago OWNER TO postgres;
GRANT ALL ON TABLE public.medios_pago TO postgres;


-- public.tipos_documentos definition

-- Drop table

-- DROP TABLE public.tipos_documentos;

CREATE TABLE public.tipos_documentos (
	codigo int4 NOT NULL,
	descripcion varchar(80) NOT NULL,
	abreviatura varchar(10) NOT NULL,
	activo bool DEFAULT true NOT NULL,
	CONSTRAINT tipos_documentos_abreviatura_not_null NOT NULL abreviatura,
	CONSTRAINT tipos_documentos_activo_not_null NOT NULL activo,
	CONSTRAINT tipos_documentos_codigo_not_null NOT NULL codigo,
	CONSTRAINT tipos_documentos_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT tipos_documentos_pkey PRIMARY KEY (codigo)
);

-- Permissions

ALTER TABLE public.tipos_documentos OWNER TO postgres;
GRANT ALL ON TABLE public.tipos_documentos TO postgres;


-- public.usuarios definition

-- Drop table

-- DROP TABLE public.usuarios;

CREATE TABLE public.usuarios (
	idusuario int4 NOT NULL,
	nombre_apellido varchar(100) NOT NULL,
	login varchar(30) NOT NULL,
	clave_acceso varchar(64) NOT NULL,
	CONSTRAINT usuarios_clave_acceso_not_null NOT NULL clave_acceso,
	CONSTRAINT usuarios_idusuario_not_null NOT NULL idusuario,
	CONSTRAINT usuarios_login_key UNIQUE (login),
	CONSTRAINT usuarios_login_not_null NOT NULL login,
	CONSTRAINT usuarios_nombre_apellido_not_null NOT NULL nombre_apellido,
	CONSTRAINT usuarios_pkey PRIMARY KEY (idusuario)
);

-- Permissions

ALTER TABLE public.usuarios OWNER TO postgres;
GRANT ALL ON TABLE public.usuarios TO postgres;


-- public.cajas_sesiones definition

-- Drop table

-- DROP TABLE public.cajas_sesiones;

CREATE TABLE public.cajas_sesiones (
	codigo serial4 NOT NULL,
	fecha_apertura timestamp DEFAULT now() NOT NULL,
	idusuario_apertura int4 NOT NULL,
	monto_apertura numeric(14, 2) DEFAULT 0 NOT NULL,
	fecha_cierre timestamp NULL,
	idusuario_cierre int4 NULL,
	monto_contado numeric(14, 2) NULL,
	estado varchar(10) DEFAULT 'ABIERTA'::character varying NOT NULL,
	observacion text NULL,
	CONSTRAINT cajas_sesiones_codigo_not_null NOT NULL codigo,
	CONSTRAINT cajas_sesiones_estado_check CHECK (((estado)::text = ANY ((ARRAY['ABIERTA'::character varying, 'CERRADA'::character varying])::text[]))),
	CONSTRAINT cajas_sesiones_estado_not_null NOT NULL estado,
	CONSTRAINT cajas_sesiones_fecha_apertura_not_null NOT NULL fecha_apertura,
	CONSTRAINT cajas_sesiones_idusuario_apertura_not_null NOT NULL idusuario_apertura,
	CONSTRAINT cajas_sesiones_monto_apertura_not_null NOT NULL monto_apertura,
	CONSTRAINT cajas_sesiones_pkey PRIMARY KEY (codigo),
	CONSTRAINT cajas_sesiones_idusuario_apertura_fkey FOREIGN KEY (idusuario_apertura) REFERENCES public.usuarios(idusuario),
	CONSTRAINT cajas_sesiones_idusuario_cierre_fkey FOREIGN KEY (idusuario_cierre) REFERENCES public.usuarios(idusuario)
);
CREATE UNIQUE INDEX ux_una_caja_abierta ON public.cajas_sesiones USING btree (estado) WHERE ((estado)::text = 'ABIERTA'::text);

-- Permissions

ALTER TABLE public.cajas_sesiones OWNER TO postgres;
GRANT ALL ON TABLE public.cajas_sesiones TO postgres;


-- public.contactos definition

-- Drop table

-- DROP TABLE public.contactos;

CREATE TABLE public.contactos (
	cto_cod int4 NOT NULL,
	cto_razonsocial varchar(120) NOT NULL,
	cto_ruc varchar(30) NOT NULL,
	cto_direccion varchar(150) NULL,
	cto_telef varchar(30) NULL,
	codigo varchar DEFAULT '1'::character varying NOT NULL,
	gcto_cod int4 DEFAULT 1 NOT NULL,
	CONSTRAINT contactos_codigo_not_null NOT NULL codigo,
	CONSTRAINT contactos_cto_cod_not_null NOT NULL cto_cod,
	CONSTRAINT contactos_cto_razonsocial_not_null NOT NULL cto_razonsocial,
	CONSTRAINT contactos_cto_ruc_not_null NOT NULL cto_ruc,
	CONSTRAINT contactos_gcto_cod_not_null NOT NULL gcto_cod,
	CONSTRAINT contactos_pkey PRIMARY KEY (cto_cod),
	CONSTRAINT contactos_codigo_fkey FOREIGN KEY (codigo) REFERENCES public.grupo_contacto(codigo),
	CONSTRAINT contactos_gcto_cod_fkey FOREIGN KEY (gcto_cod) REFERENCES public.grupocto(gcto_cod)
);

-- Permissions

ALTER TABLE public.contactos OWNER TO postgres;
GRANT ALL ON TABLE public.contactos TO postgres;


-- public.item definition

-- Drop table

-- DROP TABLE public.item;

CREATE TABLE public.item (
	codigo int4 NOT NULL,
	descripcion varchar(120) NOT NULL,
	codigo_categoria int4 NOT NULL,
	codigo_editorial int4 NOT NULL,
	codigo_mecanica int4 NOT NULL,
	activo bool DEFAULT true NOT NULL,
	precio numeric(12, 2) DEFAULT 0 NOT NULL,
	porcentaje_iva numeric(5, 2) DEFAULT 10 NOT NULL,
	fecha_alta date DEFAULT CURRENT_DATE NOT NULL,
	cantidad_min_jugadores int4 NULL,
	cantidad_max_jugadores int4 NULL,
	edad_minima int4 NULL,
	duracion_minutos int4 NULL,
	idioma_dependencia varchar(100) NULL,
	stock_actual int4 DEFAULT 0 NOT NULL,
	CONSTRAINT item_activo_not_null NOT NULL activo,
	CONSTRAINT item_codigo_grupo_not_null NOT NULL codigo_categoria,
	CONSTRAINT item_codigo_marca_not_null NOT NULL codigo_editorial,
	CONSTRAINT item_codigo_not_null NOT NULL codigo,
	CONSTRAINT item_codigo_sector_not_null NOT NULL codigo_mecanica,
	CONSTRAINT item_descripcion_not_null NOT NULL descripcion,
	CONSTRAINT item_fecha_alta_not_null NOT NULL fecha_alta,
	CONSTRAINT item_pkey PRIMARY KEY (codigo),
	CONSTRAINT item_porcentaje_iva_not_null NOT NULL porcentaje_iva,
	CONSTRAINT item_precio_not_null NOT NULL precio,
	CONSTRAINT item_stock_actual_not_null NOT NULL stock_actual,
	CONSTRAINT item_codigo_grupo_fkey FOREIGN KEY (codigo_categoria) REFERENCES public.categorias(codigo),
	CONSTRAINT item_codigo_marca_fkey FOREIGN KEY (codigo_editorial) REFERENCES public.editoriales(codigo),
	CONSTRAINT item_codigo_sector_fkey FOREIGN KEY (codigo_mecanica) REFERENCES public.mecanicas(codigo)
);

-- Permissions

ALTER TABLE public.item OWNER TO postgres;
GRANT ALL ON TABLE public.item TO postgres;


-- public.movimientos_stock definition

-- Drop table

-- DROP TABLE public.movimientos_stock;

CREATE TABLE public.movimientos_stock (
	codigo bigserial NOT NULL,
	fecha timestamp DEFAULT now() NOT NULL,
	codigo_item int4 NOT NULL,
	tipo varchar(20) NOT NULL,
	cantidad int4 NOT NULL,
	stock_resultante int4 NOT NULL,
	idusuario int4 NULL,
	referencia_codigo int4 NULL,
	observacion text NULL,
	CONSTRAINT movimientos_stock_cantidad_not_null NOT NULL cantidad,
	CONSTRAINT movimientos_stock_codigo_item_not_null NOT NULL codigo_item,
	CONSTRAINT movimientos_stock_codigo_not_null NOT NULL codigo,
	CONSTRAINT movimientos_stock_fecha_not_null NOT NULL fecha,
	CONSTRAINT movimientos_stock_pkey PRIMARY KEY (codigo),
	CONSTRAINT movimientos_stock_stock_resultante_not_null NOT NULL stock_resultante,
	CONSTRAINT movimientos_stock_tipo_not_null NOT NULL tipo,
	CONSTRAINT movimientos_stock_codigo_item_fkey FOREIGN KEY (codigo_item) REFERENCES public.item(codigo),
	CONSTRAINT movimientos_stock_idusuario_fkey FOREIGN KEY (idusuario) REFERENCES public.usuarios(idusuario)
);

-- Permissions

ALTER TABLE public.movimientos_stock OWNER TO postgres;
GRANT ALL ON TABLE public.movimientos_stock TO postgres;


-- public.pedidos_venta definition

-- Drop table

-- DROP TABLE public.pedidos_venta;

CREATE TABLE public.pedidos_venta (
	codigo serial4 NOT NULL,
	fecha date NOT NULL,
	cod_cliente int4 NOT NULL,
	idusuario int4 NOT NULL,
	estado varchar(10) DEFAULT 'PENDIENTE'::character varying NOT NULL,
	observacion varchar(250) NULL,
	total float8 DEFAULT 0 NOT NULL,
	CONSTRAINT pedidos_venta_cod_cliente_not_null NOT NULL cod_cliente,
	CONSTRAINT pedidos_venta_codigo_not_null NOT NULL codigo,
	CONSTRAINT pedidos_venta_estado_not_null NOT NULL estado,
	CONSTRAINT pedidos_venta_fecha_not_null NOT NULL fecha,
	CONSTRAINT pedidos_venta_idusuario_not_null NOT NULL idusuario,
	CONSTRAINT pedidos_venta_pkey PRIMARY KEY (codigo),
	CONSTRAINT pedidos_venta_total_not_null NOT NULL total,
	CONSTRAINT fk_pedido_cliente FOREIGN KEY (cod_cliente) REFERENCES public.contactos(cto_cod),
	CONSTRAINT fk_pedido_usuario FOREIGN KEY (idusuario) REFERENCES public.usuarios(idusuario)
);

-- Permissions

ALTER TABLE public.pedidos_venta OWNER TO postgres;
GRANT ALL ON TABLE public.pedidos_venta TO postgres;


-- public.pedidos_venta_det definition

-- Drop table

-- DROP TABLE public.pedidos_venta_det;

CREATE TABLE public.pedidos_venta_det (
	codigo_pedido int4 NOT NULL,
	nro_item int4 NOT NULL,
	codigo_item int4 NOT NULL,
	cantidad float8 NOT NULL,
	precio_unitario float8 NOT NULL,
	CONSTRAINT pedidos_venta_det_cantidad_not_null NOT NULL cantidad,
	CONSTRAINT pedidos_venta_det_codigo_item_not_null NOT NULL codigo_item,
	CONSTRAINT pedidos_venta_det_codigo_pedido_not_null NOT NULL codigo_pedido,
	CONSTRAINT pedidos_venta_det_nro_item_not_null NOT NULL nro_item,
	CONSTRAINT pedidos_venta_det_pkey PRIMARY KEY (codigo_pedido, nro_item),
	CONSTRAINT pedidos_venta_det_precio_unitario_not_null NOT NULL precio_unitario,
	CONSTRAINT fk_pedido_det_cabecera FOREIGN KEY (codigo_pedido) REFERENCES public.pedidos_venta(codigo),
	CONSTRAINT fk_pedido_det_item FOREIGN KEY (codigo_item) REFERENCES public.item(codigo)
);

-- Permissions

ALTER TABLE public.pedidos_venta_det OWNER TO postgres;
GRANT ALL ON TABLE public.pedidos_venta_det TO postgres;


-- public.timbrados definition

-- Drop table

-- DROP TABLE public.timbrados;

CREATE TABLE public.timbrados (
	codigo int4 NOT NULL,
	numero_timbrado int4 NOT NULL,
	codigo_tipo_documento int4 NOT NULL,
	fecha_inicio date NOT NULL,
	fecha_fin date NOT NULL,
	establecimiento varchar(3) NOT NULL,
	punto_expedicion varchar(3) NOT NULL,
	numero_desde int4 NOT NULL,
	numero_hasta int4 NOT NULL,
	ultimo_numero int4 DEFAULT 0 NOT NULL,
	activo bool DEFAULT true NOT NULL,
	CONSTRAINT timbrados_activo_not_null NOT NULL activo,
	CONSTRAINT timbrados_codigo_not_null NOT NULL codigo,
	CONSTRAINT timbrados_codigo_tipo_documento_not_null NOT NULL codigo_tipo_documento,
	CONSTRAINT timbrados_establecimiento_not_null NOT NULL establecimiento,
	CONSTRAINT timbrados_fecha_fin_not_null NOT NULL fecha_fin,
	CONSTRAINT timbrados_fecha_inicio_not_null NOT NULL fecha_inicio,
	CONSTRAINT timbrados_numero_desde_not_null NOT NULL numero_desde,
	CONSTRAINT timbrados_numero_hasta_not_null NOT NULL numero_hasta,
	CONSTRAINT timbrados_numero_timbrado_not_null NOT NULL numero_timbrado,
	CONSTRAINT timbrados_pkey PRIMARY KEY (codigo),
	CONSTRAINT timbrados_punto_expedicion_not_null NOT NULL punto_expedicion,
	CONSTRAINT timbrados_ultimo_numero_not_null NOT NULL ultimo_numero,
	CONSTRAINT fk_timbrado_tipo_documento FOREIGN KEY (codigo_tipo_documento) REFERENCES public.tipos_documentos(codigo)
);

-- Permissions

ALTER TABLE public.timbrados OWNER TO postgres;
GRANT ALL ON TABLE public.timbrados TO postgres;


-- public.cobros definition

-- Drop table

-- DROP TABLE public.cobros;

CREATE TABLE public.cobros (
	codigo serial4 NOT NULL,
	fecha timestamp DEFAULT now() NOT NULL,
	codigo_pedido int4 NOT NULL,
	codigo_sesion int4 NOT NULL,
	codigo_medio_pago int4 NOT NULL,
	monto numeric(14, 2) NOT NULL,
	referencia varchar(50) NULL,
	idusuario int4 NOT NULL,
	anulado bool DEFAULT false NOT NULL,
	observacion text NULL,
	CONSTRAINT cobros_anulado_not_null NOT NULL anulado,
	CONSTRAINT cobros_codigo_medio_pago_not_null NOT NULL codigo_medio_pago,
	CONSTRAINT cobros_codigo_not_null NOT NULL codigo,
	CONSTRAINT cobros_codigo_pedido_not_null NOT NULL codigo_pedido,
	CONSTRAINT cobros_codigo_sesion_not_null NOT NULL codigo_sesion,
	CONSTRAINT cobros_fecha_not_null NOT NULL fecha,
	CONSTRAINT cobros_idusuario_not_null NOT NULL idusuario,
	CONSTRAINT cobros_monto_check CHECK ((monto > (0)::numeric)),
	CONSTRAINT cobros_monto_not_null NOT NULL monto,
	CONSTRAINT cobros_pkey PRIMARY KEY (codigo),
	CONSTRAINT cobros_codigo_medio_pago_fkey FOREIGN KEY (codigo_medio_pago) REFERENCES public.medios_pago(codigo),
	CONSTRAINT cobros_codigo_pedido_fkey FOREIGN KEY (codigo_pedido) REFERENCES public.pedidos_venta(codigo),
	CONSTRAINT cobros_codigo_sesion_fkey FOREIGN KEY (codigo_sesion) REFERENCES public.cajas_sesiones(codigo),
	CONSTRAINT cobros_idusuario_fkey FOREIGN KEY (idusuario) REFERENCES public.usuarios(idusuario)
);
CREATE INDEX ix_cobros_pedido ON public.cobros USING btree (codigo_pedido);

-- Permissions

ALTER TABLE public.cobros OWNER TO postgres;
GRANT ALL ON TABLE public.cobros TO postgres;




-- Permissions

GRANT ALL ON SCHEMA public TO pg_database_owner;
GRANT USAGE ON SCHEMA public TO public;