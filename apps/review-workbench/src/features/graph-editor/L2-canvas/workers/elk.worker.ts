interface WorkerPingMessage {
  type: 'ping';
}

interface WorkerPongMessage {
  type: 'pong';
}

self.onmessage = (event: MessageEvent<WorkerPingMessage>) => {
  if (event.data.type !== 'ping') {
    return;
  }

  const response: WorkerPongMessage = { type: 'pong' };
  self.postMessage(response);
};

export {};
