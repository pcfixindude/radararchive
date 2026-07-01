export const INGEST_WINDOW_PRESETS = {
  last_1h: 'Last 1 hour',
  last_3h: 'Last 3 hours',
  last_6h: 'Last 6 hours',
  custom: 'Custom start/end',
  replay_range: 'Current replay range',
} as const;

export type IngestWindowPreset = keyof typeof INGEST_WINDOW_PRESETS;

export type IngestWindowFormState = {
  preset: IngestWindowPreset;
  limit: number;
  warmCache: boolean;
  customStart: string;
  customEnd: string;
  replayStart: string | null;
  replayEnd: string | null;
};

export type IngestWindowPlan = {
  preset: string;
  preset_label: string;
  start_time: string | null;
  end_time: string | null;
  limit: number;
  warm_cache: boolean;
  estimated_frames_in_window: number | null;
  ready: boolean;
  warnings: string[];
  bulk_ingest_command: string | null;
  guided_command: string;
  next_commands: string[];
  operator_steps: string[];
  verified_mrms: boolean;
  requires_real_flag: boolean;
};

export const DEFAULT_INGEST_WINDOW_STATE: IngestWindowFormState = {
  preset: 'last_3h',
  limit: 8,
  warmCache: false,
  customStart: '',
  customEnd: '',
  replayStart: null,
  replayEnd: null,
};

export const GUIDED_INGEST_COMMAND = 'make mrms-ingest-window PRESET=last_3h LIMIT=8';

export function formatIngestWindowLabel(preset: string): string {
  return INGEST_WINDOW_PRESETS[preset as IngestWindowPreset] ?? preset;
}

export function ingestWindowQueryFromState(state: IngestWindowFormState): URLSearchParams {
  const query = new URLSearchParams({
    preset: state.preset,
    limit: String(state.limit),
    warm_cache: String(state.warmCache),
  });
  if (state.preset === 'custom') {
    if (state.customStart) {
      query.set('start', state.customStart);
    }
    if (state.customEnd) {
      query.set('end', state.customEnd);
    }
  }
  if (state.preset === 'replay_range') {
    if (state.replayStart) {
      query.set('replay_start', state.replayStart);
    }
    if (state.replayEnd) {
      query.set('replay_end', state.replayEnd);
    }
  }
  return query;
}

export function toDatetimeLocalValue(iso: string | null): string {
  if (!iso) {
    return '';
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}T${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
}

export function fromDatetimeLocalValue(value: string): string {
  if (!value) {
    return '';
  }
  const date = new Date(`${value}:00Z`);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toISOString().replace('.000Z', 'Z');
}
