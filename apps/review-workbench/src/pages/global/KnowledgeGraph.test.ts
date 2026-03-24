import { describe, test, expect } from 'vitest';
import { deduplicateByEndpoints } from './KnowledgeGraph';

describe('deduplicateByEndpoints', () => {
  test('removes duplicate source+target pairs, keeps first', () => {
    const edges = [
      { id: 'e1', source: 'a', target: 'b' },
      { id: 'e2', source: 'a', target: 'b' },
      { id: 'e3', source: 'a', target: 'c' },
    ];
    const result = deduplicateByEndpoints(edges);
    expect(result).toHaveLength(2);
    expect(result.map((e) => e.id)).toEqual(['e1', 'e3']);
  });

  test('keeps all edges when no duplicates', () => {
    const edges = [
      { id: 'e1', source: 'a', target: 'b' },
      { id: 'e2', source: 'b', target: 'c' },
      { id: 'e3', source: 'c', target: 'a' },
    ];
    expect(deduplicateByEndpoints(edges)).toHaveLength(3);
  });

  test('direction matters — a→b and b→a are not duplicates', () => {
    const edges = [
      { id: 'e1', source: 'a', target: 'b' },
      { id: 'e2', source: 'b', target: 'a' },
    ];
    expect(deduplicateByEndpoints(edges)).toHaveLength(2);
  });

  test('returns empty array for empty input', () => {
    expect(deduplicateByEndpoints([])).toEqual([]);
  });
});
