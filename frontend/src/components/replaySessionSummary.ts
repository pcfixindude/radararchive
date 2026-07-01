import type { DecodedOverlayInfo, PlaybackCacheStatus } from '../api/client';
import { cacheStateLabel, type PlaybackFrameStatus } from '../hooks/framePlayback';
import { hasValidOverlayBounds, overlayReadyForMap, suggestNextCommand, GUIDED_INGEST_COMMAND } from './replayDisplay';

export type SessionReadiness = 'ready' | 'needs_action' | 'backend_down' | 'loading';

export type ReplaySessionSummary = {
  readiness: SessionReadiness;
  readinessLabel: string;
  selectedTime: string;
  hasDecodedOverlay: boolean;
  cacheStateLabel: string | null;
  frameQualityStatus: string | null;
  hasValidBounds: boolean;
  nextCommand: string | null;
  hints: string[];
  playbackLabel: string;
};

type LoadState = 'loading' | 'ready' | 'backend_down' | 'error';

export function buildReplaySessionSummary({
  loadState,
  selectedTime,
  overlay,
  cacheStatus,
  playbackFrameStatus,
  playing,
  frameCount,
}: {
  loadState: LoadState;
  selectedTime: string;
  overlay: DecodedOverlayInfo | null;
  cacheStatus: PlaybackCacheStatus | null;
  playbackFrameStatus: PlaybackFrameStatus;
  playing: boolean;
  frameCount: number;
}): ReplaySessionSummary {
  const selectedCacheState = cacheStatus?.frames.find((frame) => frame.timestamp === selectedTime)?.cache_state;
  const hasDecodedOverlay = overlayReadyForMap(overlay);
  const hasValidBounds = hasValidOverlayBounds(overlay?.bounds);
  const frameQualityStatus = overlay?.frame_quality?.status ?? null;
  const nextCommand = resolveSessionNextCommand(loadState, overlay, cacheStatus, frameCount);
  const hints = buildSessionHints(loadState, overlay, cacheStatus, frameCount, playing, hasDecodedOverlay);

  let readiness: SessionReadiness = 'needs_action';
  let readinessLabel = 'Needs setup';

  if (loadState === 'backend_down') {
    readiness = 'backend_down';
    readinessLabel = 'Backend offline';
  } else if (loadState === 'loading') {
    readiness = 'loading';
    readinessLabel = 'Loading…';
  } else if (hasDecodedOverlay && (cacheStatus?.playback_ready || selectedCacheState === 'ready')) {
    readiness = 'ready';
    readinessLabel = 'Ready to replay';
  } else if (hasDecodedOverlay && frameQualityStatus !== 'error') {
    readiness = 'needs_action';
    readinessLabel = 'Playable with warnings';
  } else if (nextCommand) {
    readiness = 'needs_action';
    readinessLabel = 'Action needed';
  } else if (frameCount === 0) {
    readiness = 'needs_action';
    readinessLabel = 'No frames loaded';
  }

  const playbackLabel = playing
    ? 'Playing'
    : playbackFrameStatus === 'decoding'
      ? 'Decoding frame…'
      : playbackFrameStatus === 'frame_missing'
        ? 'Frame unavailable'
        : hasDecodedOverlay
          ? 'Paused — overlay ready'
          : 'Paused';

  return {
    readiness,
    readinessLabel,
    selectedTime,
    hasDecodedOverlay,
    cacheStateLabel: selectedCacheState ? cacheStateLabel(selectedCacheState) : null,
    frameQualityStatus,
    hasValidBounds,
    nextCommand,
    hints,
    playbackLabel,
  };
}

function resolveSessionNextCommand(
  loadState: LoadState,
  overlay: DecodedOverlayInfo | null,
  cacheStatus: PlaybackCacheStatus | null,
  frameCount: number,
): string | null {
  if (loadState === 'backend_down') {
    return 'make backend';
  }
  if (loadState !== 'ready') {
    return null;
  }
  if (frameCount === 0) {
    return GUIDED_INGEST_COMMAND;
  }
  return suggestNextCommand(overlay, cacheStatus);
}

function buildSessionHints(
  loadState: LoadState,
  overlay: DecodedOverlayInfo | null,
  cacheStatus: PlaybackCacheStatus | null,
  frameCount: number,
  playing: boolean,
  hasDecodedOverlay: boolean,
): string[] {
  const hints: string[] = [];

  if (loadState === 'backend_down') {
    hints.push('Start the API with make backend, then refresh.');
    return hints;
  }
  if (frameCount === 0) {
    hints.push('Use Load frames to build a bounded ingest command, then run it in your terminal.');
    return hints;
  }
  if (overlay?.sync_status === 'no_local_candidate') {
    hints.push('No local MRMS file for this timestamp — use Load frames to ingest.');
  }
  if (!cacheStatus?.playback_ready && cacheStatus && cacheStatus.cold_count > 0) {
    hints.push('Cache is cold — warming speeds up frame stepping.');
  }
  if (!overlay?.artifact_available || overlay?.sync_status === 'decode_failed') {
    hints.push('Decoded artifacts missing or stale — run decode-retry.');
  }
  if (hasDecodedOverlay && !playing) {
    hints.push('Press Space to start playback.');
  }
  if (hasDecodedOverlay) {
    hints.push('Press F to fit the map to overlay bounds.');
  }

  return hints.slice(0, 4);
}

export function sessionReadinessClass(readiness: SessionReadiness): string {
  return `session-readiness--${readiness}`;
}
