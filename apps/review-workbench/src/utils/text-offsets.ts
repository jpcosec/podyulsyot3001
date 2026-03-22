/**
 * Compute the character offset of a DOM range endpoint within a root element.
 * Uses a TreeWalker to sum text-node lengths until reaching the target node.
 */
export function toOffset(root: HTMLElement, targetNode: Node, nodeOffset: number): number {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let total = 0;
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const length = node.textContent?.length ?? 0;
    if (node === targetNode) {
      return total + nodeOffset;
    }
    total += length;
  }
  return total;
}
