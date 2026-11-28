-- Fiabilidad de los justificantes pendientes y pequeñas mejoras de consulta.
-- Los datos siguen siendo privados: estas columnas solo organizan reintentos
-- efectuados desde el servidor de Streamlit.

alter table safara.justificantes_pendientes
  add column if not exists ultimo_intento_en timestamptz,
  add column if not exists proximo_intento_en timestamptz;

create index if not exists justificantes_pendientes_reintento_idx
  on safara.justificantes_pendientes (proximo_intento_en asc, actualizado_en asc);

-- Índices que cubren las dos referencias administrativas detectadas por el
-- asesor de rendimiento, sin alterar permisos ni datos existentes.
create index if not exists ensayos_asistencias_confirmado_por_idx
  on safara.ensayos_asistencias (confirmado_por);

create index if not exists ensayos_planificacion_actualizado_por_idx
  on safara.ensayos_planificacion (actualizado_por);
