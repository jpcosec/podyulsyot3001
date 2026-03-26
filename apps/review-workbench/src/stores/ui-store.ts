import { create } from 'zustand';

export type EditorState = 'browse' | 'focus' | 'edit_node' | 'edit_relation';

export interface FilterState {
  hiddenRelationTypes: string[];
  filterText: string;
  attributeFilter: { key: string; value: string } | null;
  hideNonNeighbors: boolean;
}

export interface UIStore {
  editorState: EditorState;
  focusedNodeId: string | null;
  focusedEdgeId: string | null;
  sidebarOpen: boolean;
  filters: FilterState;
  copiedNodeId: string | null;

  setEditorState: (state: EditorState) => void;
  setFocusedNode: (id: string | null) => void;
  setFocusedEdge: (id: string | null) => void;
  toggleSidebar: () => void;
  setFilter: (patch: Partial<FilterState>) => void;
  clearFilters: () => void;
  copyNode: (id: string) => void;
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
}));
