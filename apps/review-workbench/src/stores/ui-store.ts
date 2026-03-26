import { create } from 'zustand';

export type EditorState = 'browse' | 'focus' | 'edit_node' | 'edit_relation';

export interface FilterState {
  hiddenRelationTypes: string[];
  filterText: string;
  attributeFilter: { key: string; value: string } | null;
  hideNonNeighbors: boolean;
}

export interface DeleteTarget {
  kind: "node" | "edge";
  title: string;
  description: string;
}

export interface UIStore {
  editorState: EditorState;
  focusedNodeId: string | null;
  focusedEdgeId: string | null;
  sidebarOpen: boolean;
  filters: FilterState;
  copiedNodeId: string | null;
  deleteConfirmOpen: boolean;
  deleteTarget: DeleteTarget | null;
  pendingDeleteNodeIds: string[];
  pendingDeleteEdgeIds: string[];
  commandDialogOpen: boolean;

  setEditorState: (state: EditorState) => void;
  setFocusedNode: (id: string | null) => void;
  setFocusedEdge: (id: string | null) => void;
  toggleSidebar: () => void;
  setFilter: (patch: Partial<FilterState>) => void;
  clearFilters: () => void;
  copyNode: (id: string) => void;
  openDeleteConfirm: (target: DeleteTarget, nodeIds?: string[], edgeIds?: string[]) => void;
  closeDeleteConfirm: () => void;
  executePendingDelete: (removeElements: (nodeIds: string[], edgeIds: string[]) => void) => void;
  openCommandDialog: () => void;
  closeCommandDialog: () => void;
}

const defaultFilters: FilterState = {
  hiddenRelationTypes: [],
  filterText: '',
  attributeFilter: null,
  hideNonNeighbors: true,
};

export const useUIStore = create<UIStore>((set) => ({
  editorState: 'browse',
  focusedNodeId: null,
  focusedEdgeId: null,
  sidebarOpen: true,
  filters: defaultFilters,
  copiedNodeId: null,
  deleteConfirmOpen: false,
  deleteTarget: null,
  pendingDeleteNodeIds: [],
  pendingDeleteEdgeIds: [],
  commandDialogOpen: false,

  setEditorState: (editorState) => set({ editorState }),
  setFocusedNode: (focusedNodeId) => set({ focusedNodeId }),
  setFocusedEdge: (focusedEdgeId) => set({ focusedEdgeId }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setFilter: (patch) =>
    set((state) => ({
      filters: {
        ...state.filters,
        ...patch,
      },
    })),
  clearFilters: () => set({ filters: defaultFilters }),
  copyNode: (copiedNodeId) => set({ copiedNodeId }),
  openDeleteConfirm: (target, nodeIds = [], edgeIds = []) => 
    set({ 
      deleteConfirmOpen: true, 
      deleteTarget: target,
      pendingDeleteNodeIds: nodeIds,
      pendingDeleteEdgeIds: edgeIds,
    }),
  closeDeleteConfirm: () => 
    set({ 
      deleteConfirmOpen: false, 
      deleteTarget: null,
      pendingDeleteNodeIds: [],
      pendingDeleteEdgeIds: [],
    }),
  executePendingDelete: (removeElements) => 
    set((state) => {
      const nodeIds = state.pendingDeleteNodeIds;
      const edgeIds = state.pendingDeleteEdgeIds;
      removeElements(nodeIds, edgeIds);
      return {
        deleteConfirmOpen: false,
        deleteTarget: null,
        pendingDeleteNodeIds: [],
        pendingDeleteEdgeIds: [],
      };
    }),
  openCommandDialog: () => set({ commandDialogOpen: true }),
  closeCommandDialog: () => set({ commandDialogOpen: false }),
}));
