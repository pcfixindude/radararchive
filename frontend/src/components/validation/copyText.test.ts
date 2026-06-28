import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { copyTextToClipboard } from './copyText';

describe('copyTextToClipboard', () => {
  const writeText = vi.fn();

  beforeEach(() => {
    writeText.mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('uses clipboard API only', async () => {
    const result = await copyTextToClipboard('make test');
    expect(result).toBe(true);
    expect(writeText).toHaveBeenCalledWith('make test');
  });
});
