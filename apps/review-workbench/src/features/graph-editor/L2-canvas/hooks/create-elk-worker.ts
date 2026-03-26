export function createElkWorker(): Worker {
  return new Worker(new URL('../workers/elk.worker.ts', import.meta.url), {
    type: 'module',
  });
}
