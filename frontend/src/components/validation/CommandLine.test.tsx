import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CommandLine from './CommandLine';

describe('CommandLine', () => {
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

  it('renders copy button with command text', () => {
    render(<CommandLine command="make operator-review-status" label="Exact command" manualCopy />);
    expect(screen.getByRole('button', { name: /copy exact command/i })).toBeTruthy();
    expect(screen.getByText('make operator-review-status')).toBeTruthy();
    expect(screen.getByText(/does not run commands/i)).toBeTruthy();
  });

  it('copies command to clipboard without executing it', async () => {
    render(<CommandLine command="make operator-workflow-presets" />);
    fireEvent.click(screen.getByRole('button', { name: /copy/i }));
    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith('make operator-workflow-presets');
    });
    expect(writeText).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /copy/i }).textContent).toBe('Copied');
    });
  });
});
