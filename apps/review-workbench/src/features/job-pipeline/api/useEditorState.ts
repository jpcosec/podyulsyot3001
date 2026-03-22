import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { CommandResponse } from '../../../types/api.types';

interface SaveEditorStateArgs {
  state: Record<string, unknown>;
}

export function useEditorState(source: string, jobId: string, nodeName: string) {
  return useMutation<CommandResponse, Error, SaveEditorStateArgs>({
    mutationFn: ({ state }) => apiClient.commands.jobs.saveEditorState(source, jobId, nodeName, state),
  });
}
