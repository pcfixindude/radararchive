import type { DecodedOverlayInfo } from '../api/client';

export type PlaybackFrameStatus =
  | 'idle'
  | 'playing'
  | 'paused'
  | 'decoding'
  | 'frame_ready'
  | 'frame_missing'
  | 'decode_failed';

export function overlayToFrameStatus(overlay: DecodedOverlayInfo | null): PlaybackFrameStatus {
  if (!overlay) {
    return 'frame_missing';
  }
  if (overlay.sync_status === 'matched' && overlay.overlay_visible) {
    return 'frame_ready';
  }
  if (overlay.sync_status === 'decode_failed' || overlay.sync_status === 'decoder_missing') {
    return 'decode_failed';
  }
  return 'frame_missing';
}

export function combinePlaybackStatus(
  playing: boolean,
  frameStatus: PlaybackFrameStatus,
): PlaybackFrameStatus {
  if (frameStatus === 'decoding') {
    return 'decoding';
  }
  if (playing) {
    return 'playing';
  }
  if (
    frameStatus === 'frame_ready' ||
    frameStatus === 'frame_missing' ||
    frameStatus === 'decode_failed'
  ) {
    return frameStatus;
  }
  return 'paused';
}

export function playbackStatusLabel(status: PlaybackFrameStatus): string {
  switch (status) {
    case 'playing':
      return 'playing';
    case 'paused':
      return 'paused';
    case 'decoding':
      return 'decoding';
    case 'frame_ready':
      return 'frame ready';
    case 'frame_missing':
      return 'frame missing';
    case 'decode_failed':
      return 'decode failed';
    default:
      return 'idle';
  }
}

export function adjacentTimestamps(times: string[], selectedTime: string): string[] {
  const index = times.indexOf(selectedTime);
  if (index < 0) {
    return [];
  }
  return [times[index - 1], times[index + 1]].filter((value): value is string => Boolean(value));
}

export type FrameCacheState =
  | 'ready'
  | 'missing_raw'
  | 'cold_decodable'
  | 'failed'
  | 'stub';

export function cacheStateLabel(state: FrameCacheState | string): string {
  switch (state) {
    case 'ready':
      return 'cached';
    case 'missing_raw':
      return 'no raw';
    case 'cold_decodable':
      return 'cold';
    case 'failed':
      return 'failed';
    case 'stub':
      return 'stub';
    default:
      return state;
  }
}

export function cacheStateClass(state: FrameCacheState | string): string {
  return `slider-cache--${state}`;
}
