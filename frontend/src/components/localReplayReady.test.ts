import { describe, expect, it } from 'vitest';
import { primarySetupCommand, setupChecklistClass } from './localReplayReady';
import type { LocalReplayReadyStatus } from './localReplayReady';

const readyStatus: LocalReplayReadyStatus = {
  ran_at: '2026-06-28T15:00:00Z',
  ready: true,
  ready_label: 'Ready to replay',
  dry_run: true,
  frame_count: 8,
  checklist: [],
  next_command: 'make backend && make frontend',
  next_commands: ['make backend && make frontend'],
  suggested_run_command: 'make local-replay-ready RUN=1',
  does_not_run_real_ingest: true,
};

describe('setupChecklistClass', () => {
  it('maps ok status', () => {
    expect(setupChecklistClass('ok')).toBe('session-ok');
  });

  it('maps missing status to warn style', () => {
    expect(setupChecklistClass('missing')).toBe('session-warn');
  });
});

describe('primarySetupCommand', () => {
  it('returns default command when status is null', () => {
    expect(primarySetupCommand(null)).toBe('make local-replay-ready');
  });

  it('returns ui command when ready', () => {
    expect(primarySetupCommand(readyStatus)).toBe('make backend && make frontend');
  });
});
