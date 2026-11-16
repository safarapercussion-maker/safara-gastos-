Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.
create schema if not exists safara;
revoke all on schema safara from public;
revoke all on schema safara from anon, authenticated;
alter default privileges in schema safara revoke all on tables from public;
alter default privileges in schema safara revoke all on sequences from public;
alter default privileges in schema safara revoke all on functions from public;

create extension if not exists pgcrypto with schema extensions;

create table safara.usuarios (
  id uuid primary key default gen_random_uuid(),
  nombre text not null check (length(btrim(nombre)) between 2 and 120),
  rol text not null check (rol in ('admin', 'usuario')),
  password_salt text not null check (length(password_salt) between 16 and 512),
  password_hash text not null check (length(password_hash) between 32 and 512),
  email text not null check (length(btrim(email)) between 3 and 254),
  telefono text not null check (length(btrim(telefono)) between 6 and 30),
  fecha_nacimiento date not null,
  instrumento text not null check (length(btrim(instrumento)) between 2 and 120),
  rgpd_aceptado_en timestamptz not null,
  activo boolean not null default true,
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
create unique index usuarios_nombre_normalizado_unico on safara.usuarios (lower(btrim(nombre)));
create unique index usuarios_email_normalizado_unico on safara.usuarios (lower(btrim(email)));
create index usuarios_activos_idx on safara.usuarios (activo) where activo;

create table safara.invitaciones (
  id uuid primary key default gen_random_uuid(),
  codigo_hash text not null unique check (codigo_hash ~ '^[0-9a-f]{64}$'),
  emitido_por uuid not null references safara.usuarios(id),
  creado_en timestamptz not null default now(), caduca_en timestamptz not null,
  usado_por uuid references safara.usuarios(id), usado_en timestamptz,
  check (caduca_en > creado_en), check ((usado_por is null) = (usado_en is null))
);
create index invitaciones_validas_idx on safara.invitaciones (caduca_en) where usado_por is null;

create table safara.actuaciones (
  id bigint generated always as identity primary key,
  titulo text not null check (length(btrim(titulo)) between 2 and 180), fecha date not null,
  hora text not null check (length(btrim(hora)) between 2 and 80),
  lugar text not null check (length(btrim(lugar)) between 2 and 180),
  estado text not null check (estado in ('CONFIRMADA', 'EVALUACION', 'STANDBY', 'ANULADA')),
  creado_por uuid references safara.usuarios(id), creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);
create unique index actuaciones_titulo_fecha_unico on safara.actuaciones (lower(btrim(titulo)), fecha);
create index actuaciones_fecha_idx on safara.actuaciones (fecha desc);

create table safara.votos (
  id bigint generated always as identity primary key,
  encuesta_id text not null check (length(btrim(encuesta_id)) between 2 and 180),
  ciclo_id text not null check (length(btrim(ciclo_id)) between 2 and 180),
  usuario_id uuid not null references safara.usuarios(id),
  respuesta text not null check (respuesta in ('SI', 'NO')),
  actualizado_en timestamptz not null default now(), unique (encuesta_id, ciclo_id, usuario_id)
);
create index votos_encuesta_idx on safara.votos (encuesta_id, ciclo_id);

create table safara.gastos (
  id bigint generated always as identity primary key, fecha date not null,
  usuario_id uuid not null references safara.usuarios(id),
  concepto text not null check (length(btrim(concepto)) between 2 and 500),
  importe numeric(12,2) not null check (importe > 0),
  fichero text not null check (length(btrim(fichero)) between 1 and 255),
  estado_reembolso text not null default 'PENDIENTE ABONO' check (estado_reembolso in ('PENDIENTE ABONO', 'ABONADO')),
  enlace_ticket text, drive_file_id text,
  mime_type text check (mime_type is null or mime_type in ('image/png', 'image/jpeg', 'application/pdf')),
  abonado_en timestamptz, abonado_por uuid references safara.usuarios(id),
  creado_en timestamptz not null default now(), actualizado_en timestamptz not null default now(),
  check ((estado_reembolso = 'ABONADO') = (abonado_en is not null))
);
create index gastos_usuario_idx on safara.gastos (usuario_id, fecha desc);
create index gastos_reembolso_idx on safara.gastos (estado_reembolso, fecha desc);

create table safara.confesionario (
  id bigint generated always as identity primary key, usuario_id uuid not null references safara.usuarios(id),
  mensaje text not null check (length(btrim(mensaje)) between 1 and 2000), creado_en timestamptz not null default now()
);
create index confesionario_creado_idx on safara.confesionario (creado_en desc);

create table safara.caja (
  clave text primary key check (clave = 'saldo_caja'), valor numeric(12,2) not null,
  version integer not null default 1 check (version > 0), actualizado_por uuid references safara.usuarios(id),
  actualizado_en timestamptz not null default now()
);
insert into safara.caja (clave, valor) values ('saldo_caja', 0) on conflict (clave) do nothing;

create table safara.auditoria (
  id bigint generated always as identity primary key, fecha_hora timestamptz not null default now(),
  evento text not null check (length(btrim(evento)) between 2 and 120),
  usuario_id uuid references safara.usuarios(id), detalle text not null default '' check (length(detalle) <= 2000)
);
create index auditoria_fecha_idx on safara.auditoria (fecha_hora desc);

create function safara.establecer_actualizado_en() returns trigger language plpgsql set search_path = safara, pg_temp as $$
begin new.actualizado_en = now(); return new; end;
$$;
create trigger usuarios_actualizado_en before update on safara.usuarios for each row execute function safara.establecer_actualizado_en();
create trigger actuaciones_actualizado_en before update on safara.actuaciones for each row execute function safara.establecer_actualizado_en();
create trigger gastos_actualizado_en before update on safara.gastos for each row execute function safara.establecer_actualizado_en();

alter table safara.usuarios enable row level security;
alter table safara.invitaciones enable row level security;
alter table safara.actuaciones enable row level security;
alter table safara.votos enable row level security;
alter table safara.gastos enable row level security;
alter table safara.confesionario enable row level security;
alter table safara.caja enable row level security;
alter table safara.auditoria enable row level security;

