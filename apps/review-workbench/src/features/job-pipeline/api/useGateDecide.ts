import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { GateDecisionPayload, CommandResponse } from '../../../types/api.types';

export function useGateDecide(source: string, jobId: string, gateName: string) {
  return useMutation<CommandResponse, Error, GateDecisionPayload>({
    mutationFn: (payload) => apiClient.commands.jobs.decideGate(source, jobId, gateName, payload),
  });
}
