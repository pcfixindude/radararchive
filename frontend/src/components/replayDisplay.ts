import type { DecodedOverlayInfo, PlaybackCacheStatus } from '../api/client';
import { cacheStateLabel } from '../hooks/framePlayback';

export const GUIDED_INGEST_COMMAND = 'make mrms-ingest-window PRESET=last_3h LIMIT=8';

export type ReplayDisplayState = {
  showDecodedOverlay: boolean;
  showBoundsOutline: boolean;
  showGeorefDebug: boolean;
  showFrameQualityDetails: boolean;
};

export const DEFAULT_REPLAY_DISPLAY: ReplayDisplayState = {
  showDecodedOverlay: true,
  showBoundsOutline: true,
  showGeorefDebug: false,
  showFrameQualityDetails: false,
};

export function hasValidOverlayBounds(bounds?: number[] | null): boolean {
  if (!bounds || bounds.length !== 4) {
    return false;
  }
  const [west, south, east, north] = bounds;
  return west < east && south < north;
}

export function selectedFrameSummary(
  overlay: DecodedOverlayInfo | null,
  selectedTime: string,
  selectedCacheState?: string,
): string {
  if (!selectedTime) {
    return 'No frame selected';
  }
  if (!overlay) {
    return 'Loading overlay status…';
  }
  if (overlay.sync_status === 'matched' && overlay.overlay_visible) {
    const cache = selectedCacheState ? ` · cache ${cacheStateLabel(selectedCacheState)}` : '';
    return `Decoded overlay ready for ${selectedTime}${cache}`;
  }
  if (overlay.sync_status === 'decoding' || overlay.frame_status === 'matched') {
    return `Selected ${selectedTime} — checking decode…`;
  }
  if (overlay.sync_status === 'no_local_candidate') {
    return `No local MRMS file for ${selectedTime}`;
  }
  if (overlay.sync_status === 'decode_failed') {
    return `Decode failed for ${selectedTime}`;
  }
  if (overlay.sync_status === 'mismatch') {
    return `Selected ${selectedTime} does not match decoded candidate`;
  }
  return `Selected ${selectedTime} — no decoded overlay yet`;
}

export function suggestNextCommand(
  overlay: DecodedOverlayInfo | null,
  cacheStatus: PlaybackCacheStatus | null,
): string | null {
  if (overlay?.sync_status === 'no_local_candidate') {
    return GUIDED_INGEST_COMMAND;
  }
  if (overlay?.sync_status === 'decode_failed' || overlay?.sync_status === 'decoder_missing') {
    return 'make decode-retry';
  }
  if (!cacheStatus?.playback_ready && cacheStatus?.next_commands?.length) {
    const warm = cacheStatus.next_commands.find((cmd) => cmd.includes('warm'));
    if (warm) {
      return warm;
    }
    return cacheStatus.next_commands[0];
  }
  if (!overlay?.artifact_available) {
    return GUIDED_INGEST_COMMAND;
  }
  if (overlay?.sync_status !== 'matched') {
    return 'make decode-retry';
  }
  return null;
}

export function overlayReadyForMap(overlay: DecodedOverlayInfo | null): boolean {
  return Boolean(
    overlay?.overlay_visible &&
      overlay.sync_status === 'matched' &&
      hasValidOverlayBounds(overlay.bounds),
  );
}
