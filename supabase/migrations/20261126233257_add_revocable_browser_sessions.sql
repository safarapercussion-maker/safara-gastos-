create table safara.sesiones_navegador (
  token_hash text primary key check (token_hash ~ '^[0-9a-f]{64}$'),
  usuario_id uuid not null references safara.usuarios(id) on delete cascade,
  password_hash_al_crear text not null,
  creado_en timestamptz not null default now(),
  ultimo_uso timestamptz not null default now(),
  caduca_en timestamptz not null,
  check (caduca_en > creado_en)
);
create index sesiones_navegador_usuario_idx on safara.sesiones_navegador (usuario_id);
create index sesiones_navegador_caducidad_idx on safara.sesiones_navegador (caduca_en);
alter table safara.sesiones_navegador enable row level security;
revoke all on safara.sesiones_navegador from public, anon, authenticated;
