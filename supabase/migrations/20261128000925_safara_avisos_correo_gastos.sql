alter table safara.gastos
  add column aviso_correo_estado text
    check (aviso_correo_estado in ('PENDIENTE', 'EN_CURSO', 'ENVIADO', 'ERROR')),
  add column aviso_correo_intento uuid,
  add column aviso_correo_reserva_hasta timestamptz;

create index gastos_historial_fecha_id_idx on safara.gastos (fecha desc, id desc);
