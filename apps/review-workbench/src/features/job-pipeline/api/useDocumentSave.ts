import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { CommandResponse } from '../../../types/api.types';

interface SaveDocArgs {
  docKey: string;
  markdown: string;
}

export function useDocumentSave(source: string, jobId: string) {
  return useMutation<CommandResponse, Error, SaveDocArgs>({
    mutationFn: ({ docKey, markdown }) =>
      apiClient.commands.jobs.saveDocument(source, jobId, docKey, markdown),
  });
}
