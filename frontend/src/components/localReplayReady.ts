export type LocalReplayReadyChecklistItem = {
  id: string;
  label: string;
  status: string;
  message: string;
  next_command?: string | null;
  details?: Record<string, unknown>;
};

export type LocalReplayReadyStatus = {
  ran_at: string;
  ready: boolean;
  ready_label: string;
  dry_run: boolean;
  frame_count: number;
  checklist: LocalReplayReadyChecklistItem[];
  next_command: string | null;
  next_commands: string[];
  suggested_run_command: string;
  does_not_run_real_ingest: boolean;
};

export function setupChecklistClass(status: string): string {
  switch (status) {
    case 'ok':
      return 'session-ok';
    case 'warning':
      return 'session-warn';
    case 'error':
      return 'session-warn';
    default:
      return 'session-warn';
  }
}

export function primarySetupCommand(status: LocalReplayReadyStatus | null): string | null {
  if (!status) {
    return 'make local-replay-ready';
  }
  if (status.ready) {
    return status.next_command;
  }
  return status.next_command ?? status.suggested_run_command;
}
