import { describe, expect, it } from 'vitest';
import { qualityStatusLabel } from '../components/frameQualityDisplay';

describe('qualityStatusLabel', () => {
  it('labels quality statuses', () => {
    expect(qualityStatusLabel('ok')).toBe('ok');
    expect(qualityStatusLabel('warning')).toBe('warning');
    expect(qualityStatusLabel(undefined)).toBe('unavailable');
  });
});
