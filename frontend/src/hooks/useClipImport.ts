import { useCallback, useState } from 'react';
import { fetchClipImport, type ClipImportReport } from '../api/client';
import {
  buildApplyPayload,
  parseClipManifestJson,
  validateClipManifestShape,
  type ClipImportApplyPayload,
} from '../components/clipImport';

export function useClipImport() {
  const [rawInput, setRawInput] = useState('');
  const [report, setReport] = useState<ClipImportReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [applyNotice, setApplyNotice] = useState('');

  const validateImport = useCallback(async () => {
    setLoading(true);
    setError('');
    setApplyNotice('');
    try {
      const { manifest, error: parseError } = parseClipManifestJson(rawInput);
      if (parseError || manifest === null) {
        setReport(null);
        setError(parseError ?? 'Clip manifest is empty.');
        return null;
      }
      const shapeError = validateClipManifestShape(manifest);
      if (shapeError) {
        setReport(null);
        setError(shapeError);
        return null;
      }
      const payload = await fetchClipImport(manifest as Record<string, unknown>);
      setReport(payload);
      if (!payload.valid) {
        setError(payload.errors.join(' '));
      }
      return payload;
    } catch (err) {
      setReport(null);
      setError(err instanceof Error ? err.message : 'Failed to validate clip import');
      return null;
    } finally {
      setLoading(false);
    }
  }, [rawInput]);

  const loadFromFile = useCallback(async (file: File) => {
    setApplyNotice('');
    setError('');
    try {
      const text = await file.text();
      setRawInput(text);
    } catch {
      setError('Could not read the selected file.');
    }
  }, []);

  const clearImport = useCallback(() => {
    setRawInput('');
    setReport(null);
    setError('');
    setApplyNotice('');
  }, []);

  const buildApply = useCallback((): ClipImportApplyPayload | null => {
    if (!report) {
      return null;
    }
    return buildApplyPayload(report);
  }, [report]);

  const markApplied = useCallback((message = 'Clip range applied to replay.') => {
    setApplyNotice(message);
  }, []);

  return {
    rawInput,
    report,
    loading,
    error,
    applyNotice,
    setRawInput,
    validateImport,
    loadFromFile,
    clearImport,
    buildApply,
    markApplied,
  };
}

export type ClipImportHookState = ReturnType<typeof useClipImport>;
