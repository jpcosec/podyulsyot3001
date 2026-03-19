import { useEffect, useMemo, useRef, useState } from "react";

import {
  DndContext,
  PointerSensor,
  type DragEndEvent,
  type DragStartEvent,
  DragOverlay,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

type MainCategory = "requirement" | "info";

interface CategoryConfig {
  label: string;
  color: string;
}

interface SubcategoryOption {
  value: string;
  label: string;
}

interface HighlightNote {
  id: string;
  start: number;
  end: number;
  capturedText: string;
  mainCategory: MainCategory;
  subcategory: string;
  customSubcategory: string;
  nodeLabel: string;
  details: string;
}

interface Segment {
  start: number;
  end: number;
  text: string;
  noteId?: string;
  mainCategory?: MainCategory;
  subcategory?: string;
}

interface RichTextPaneProps {
  initialText?: string;
}

type DragState =
  | { kind: "selection"; text: string }
  | { kind: "note"; noteId: string; label: string }
  | null;

const CATEGORY_ORDER: MainCategory[] = ["requirement", "info"];

const CATEGORY_CONFIG: Record<MainCategory, CategoryConfig> = {
  requirement: { label: "Requirement", color: "#b91c1c" },
  info: { label: "Info", color: "#0369a1" },
};

const SUBCATEGORY_COLORS: Record<MainCategory, Record<string, string>> = {
  requirement: {
    important: "#ef4444",
    less_important: "#f87171",
    blocker: "#991b1b",
    other: "#dc2626",
  },
  info: {
    publication_date: "#7c3aed",
    deadline: "#c026d3",
    description: "#64748b",
    name: "#4338ca",
    payment: "#059669",
    contact: "#b45309",
    institution: "#0369a1",
    other: "#6b7280",
  },
};

const SUBCATEGORY_OPTIONS: Record<MainCategory, SubcategoryOption[]> = {
  requirement: [
    { value: "important", label: "Important" },
    { value: "less_important", label: "Less important" },
    { value: "blocker", label: "Blocker" },
    { value: "other", label: "Other" },
  ],
  info: [
    { value: "publication_date", label: "Publication date" },
    { value: "deadline", label: "Deadline" },
    { value: "description", label: "Description" },
    { value: "name", label: "Name" },
    { value: "payment", label: "Payment" },
    { value: "contact", label: "Contact" },
    { value: "institution", label: "Institution" },
    { value: "other", label: "Other" },
  ],
};

const DEFAULT_TEXT = `# Job Posting IV-81/26

Faculty IV - Electrical Engineering and Computer Science
Research Assistant (PhD candidate)

Required:
- Master's degree in Computer Science or related field
- Strong SQL and distributed systems knowledge

Salary grade: E13 TV-L Berliner Hochschulen
Application deadline: 27.03.2026
Contact: Prof. Dr. Abedjan (sekr@d2ip.tu-berlin.de)`;

function byStart(a: HighlightNote, b: HighlightNote): number {
  return a.start - b.start;
}

function toOffset(root: HTMLElement, targetNode: Node, nodeOffset: number): number {
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

function buildSegments(text: string, notes: HighlightNote[]): Segment[] {
  if (notes.length === 0) {
    return [{ start: 0, end: text.length, text }];
  }

  const segments: Segment[] = [];
  let cursor = 0;

  for (const note of [...notes].sort(byStart)) {
    if (cursor < note.start) {
      segments.push({
        start: cursor,
        end: note.start,
        text: text.slice(cursor, note.start),
      });
    }

    segments.push({
      start: note.start,
      end: note.end,
      text: text.slice(note.start, note.end),
      noteId: note.id,
      mainCategory: note.mainCategory,
      subcategory: note.subcategory,
    });
    cursor = note.end;
  }

  if (cursor < text.length) {
    segments.push({
      start: cursor,
      end: text.length,
      text: text.slice(cursor),
    });
  }

  return segments;
}

function shortPreview(text: string): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= 72) {
    return clean;
  }
  return `${clean.slice(0, 72)}...`;
}

function effectiveSubcategory(note: HighlightNote): string {
  if (note.subcategory !== "other") {
    return note.subcategory;
  }
  return note.customSubcategory.trim() || "other";
}

function categoryColor(mainCategory: MainCategory, subcategory: string): string {
  return SUBCATEGORY_COLORS[mainCategory][subcategory] ?? CATEGORY_CONFIG[mainCategory].color;
}

function EditableField(props: {
  label: string;
  value: string;
  onCommit: (next: string) => void;
  multiline?: boolean;
  placeholder?: string;
}): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(props.value);

  useEffect(() => {
    setDraft(props.value);
  }, [props.value]);

  const commit = (): void => {
    setEditing(false);
    props.onCommit(draft.trim());
  };

  if (!editing) {
    return (
      <div className="note-field" onDoubleClick={() => setEditing(true)}>
        <strong>{props.label}</strong>
        <p>{props.value || props.placeholder || "Double-click to edit"}</p>
      </div>
    );
  }

  return (
    <div className="note-field">
      <strong>{props.label}</strong>
      {props.multiline ? (
        <textarea
          className="note-field-input note-field-input-multiline"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={commit}
          onPointerDown={(event) => event.stopPropagation()}
          autoFocus
        />
      ) : (
        <input
          className="note-field-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={commit}
          onPointerDown={(event) => event.stopPropagation()}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commit();
            }
            if (event.key === "Escape") {
              setEditing(false);
              setDraft(props.value);
            }
          }}
          autoFocus
        />
      )}
    </div>
  );
}

function SelectionChip(props: { text: string }): JSX.Element {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: "selected-text",
    data: { kind: "selection" },
  });

  return (
    <button
      ref={setNodeRef}
      type="button"
      className="selection-chip"
      style={{ transform: CSS.Translate.toString(transform) }}
      {...listeners}
      {...attributes}
    >
      {isDragging ? "Dragging..." : "Drag selected text"}: {shortPreview(props.text)}
    </button>
  );
}

function MainCategoryBox(props: {
  category: MainCategory;
  count: number;
  isActive: boolean;
  hasSelection: boolean;
  shortcut: string;
  onSelect: () => void;
}): JSX.Element {
  const { setNodeRef, isOver } = useDroppable({ id: `cat-${props.category}` });
  const config = CATEGORY_CONFIG[props.category];

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={`main-category-tab${props.isActive ? " main-category-tab-active" : ""}${
        isOver ? " category-box-over" : ""
      }`}
      style={{ borderColor: config.color }}
      onClick={props.onSelect}
    >
      <header>
        <strong>{config.label}</strong>
        <span className="category-box-count">{props.count}</span>
      </header>
      {props.hasSelection ? (
        <p className="category-box-hint">
          <span className="category-box-shortcut">{props.shortcut}</span> Click or press {props.shortcut}
        </p>
      ) : (
        <p>Active tab</p>
      )}
    </button>
  );
}

function SubcategoryBox(props: {
  category: MainCategory;
  subcategory: SubcategoryOption;
  count: number;
  firstText: string;
  isActive: boolean;
  hasSelection: boolean;
  shortcut: string;
  onSelect: () => void;
}): JSX.Element {
  const { setNodeRef, isOver } = useDroppable({
    id: `sub-${props.category}-${props.subcategory.value}`,
  });
  const color = categoryColor(props.category, props.subcategory.value);

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={`subcategory-box${props.isActive ? " subcategory-box-active" : ""}${
        isOver ? " subcategory-box-over" : ""
      }`}
      style={{ borderColor: color }}
      onClick={props.onSelect}
    >
      <header>
        <strong>{props.subcategory.label}</strong>
        <span className="subcategory-box-count">{props.count}</span>
      </header>
      {props.hasSelection ? (
        <p className="subcategory-box-hint">
          <span className="category-box-shortcut">{props.shortcut}</span> Add to this subcategory
        </p>
      ) : (
        <p>{props.firstText || "No notes"}</p>
      )}
    </button>
  );
}

function NoteCard(props: {
  note: HighlightNote;
  isCollapsed: boolean;
  isActive: boolean;
  onCardClick: () => void;
  onUpdate: (patch: Partial<HighlightNote>) => void;
  onRemove: () => void;
}): JSX.Element {
  const color = categoryColor(props.note.mainCategory, props.note.subcategory);
  const options = SUBCATEGORY_OPTIONS[props.note.mainCategory];

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `note-${props.note.id}`,
    data: { kind: "note", noteId: props.note.id },
  });

  return (
    <article
      ref={setNodeRef}
      className={`highlight-note-card${props.isActive ? " highlight-note-card-active" : ""}${
        isDragging ? " highlight-note-card-dragging" : ""
      }`}
      style={{ borderLeftColor: color, transform: CSS.Translate.toString(transform) }}
      onClick={props.onCardClick}
      {...listeners}
      {...attributes}
    >
      <header>
        <strong>
          {CATEGORY_CONFIG[props.note.mainCategory].label} / {effectiveSubcategory(props.note)}
        </strong>
        <div className="note-card-head-actions" onPointerDown={(event) => event.stopPropagation()}>
          <button
            type="button"
            className="note-remove-button"
            aria-label="Remove note"
            onPointerDown={(event) => {
              event.stopPropagation();
              event.preventDefault();
              props.onRemove();
            }}
          >
            🗑
          </button>
        </div>
      </header>

      {props.isCollapsed ? (
        <p className="note-collapsed-preview">{shortPreview(props.note.capturedText)}</p>
      ) : (
        <div className="note-expanded-content">
          <div className="note-field">
            <strong>Exact text</strong>
            <p>{props.note.capturedText}</p>
          </div>

          <div className="note-field" onPointerDown={(event) => event.stopPropagation()}>
            <strong>Main category</strong>
            <select
              className="note-field-input"
              value={props.note.mainCategory}
              onChange={(event) => {
                const nextCategory = event.target.value as MainCategory;
                const firstSub = SUBCATEGORY_OPTIONS[nextCategory][0]?.value ?? "other";
                props.onUpdate({
                  mainCategory: nextCategory,
                  subcategory: firstSub,
                  customSubcategory: "",
                });
              }}
            >
              {CATEGORY_ORDER.map((category) => (
                <option key={category} value={category}>
                  {CATEGORY_CONFIG[category].label}
                </option>
              ))}
            </select>
          </div>

          <div className="note-field" onPointerDown={(event) => event.stopPropagation()}>
            <strong>Subcategory</strong>
            <select
              className="note-field-input"
              value={props.note.subcategory}
              onChange={(event) => {
                const value = event.target.value;
                props.onUpdate({
                  subcategory: value,
                  customSubcategory: value === "other" ? props.note.customSubcategory : "",
                });
              }}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {props.note.subcategory === "other" ? (
            <EditableField
              label="Other subcategory"
              value={props.note.customSubcategory}
              onCommit={(next) => props.onUpdate({ customSubcategory: next })}
              placeholder="Double-click to add other subcategory"
            />
          ) : null}

          <EditableField
            label="Node label"
            value={props.note.nodeLabel}
            onCommit={(next) => props.onUpdate({ nodeLabel: next })}
          />

          <EditableField
            label="Details"
            value={props.note.details}
            onCommit={(next) => props.onUpdate({ details: next })}
            multiline
            placeholder="Double-click to add context"
          />

          <small>
            Offsets: [{props.note.start}, {props.note.end}]
          </small>
        </div>
      )}
    </article>
  );
}

export function RichTextPane(props: RichTextPaneProps): JSX.Element {
  const text = props.initialText ?? DEFAULT_TEXT;
  const editorRef = useRef<HTMLDivElement | null>(null);

  const [notes, setNotes] = useState<HighlightNote[]>([]);
  const [selectedRange, setSelectedRange] = useState<{ start: number; end: number } | null>(null);
  const [selectedText, setSelectedText] = useState("");
  const [activeCategory, setActiveCategory] = useState<MainCategory>("requirement");
  const [activeSubcategory, setActiveSubcategory] = useState<string>(
    SUBCATEGORY_OPTIONS.requirement[0]?.value ?? "important",
  );
  const [activeNoteId, setActiveNoteId] = useState("");
  const [collapsedNoteIds, setCollapsedNoteIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [dragState, setDragState] = useState<DragState>(null);
  const [pendingKeyboardCategory, setPendingKeyboardCategory] = useState<MainCategory | null>(null);
  const [error, setError] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  const notesByCategory = useMemo(() => {
    const grouped: Record<MainCategory, HighlightNote[]> = {
      requirement: [],
      info: [],
    };
    for (const note of [...notes].sort(byStart)) {
      grouped[note.mainCategory].push(note);
    }
    return grouped;
  }, [notes]);

  const segments = useMemo(() => buildSegments(text, notes), [text, notes]);
  const activeSubOptions = SUBCATEGORY_OPTIONS[activeCategory];

  const captureSelection = (): void => {
    const root = editorRef.current;
    const selection = window.getSelection();
    if (!root || !selection || selection.rangeCount === 0) {
      setSelectedRange(null);
      setSelectedText("");
      setPendingKeyboardCategory(null);
      return;
    }

    const range = selection.getRangeAt(0);
    if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) {
      setSelectedRange(null);
      setSelectedText("");
      setPendingKeyboardCategory(null);
      return;
    }

    const start = toOffset(root, range.startContainer, range.startOffset);
    const end = toOffset(root, range.endContainer, range.endOffset);
    const realStart = Math.max(0, Math.min(start, end));
    const realEnd = Math.min(text.length, Math.max(start, end));

    if (realStart === realEnd) {
      setSelectedRange(null);
      setSelectedText("");
      setPendingKeyboardCategory(null);
      return;
    }

    setSelectedRange({ start: realStart, end: realEnd });
    setSelectedText(text.slice(realStart, realEnd));
    setError("");
  };

  const addNote = (mainCategory: MainCategory, subcategory: string): void => {
    if (!selectedRange) {
      setError("Select text first.");
      return;
    }

    const hasOverlap = notes.some(
      (note) => selectedRange.start < note.end && note.start < selectedRange.end,
    );
    if (hasOverlap) {
      setError("Selection overlaps an existing highlight.");
      return;
    }

    const note: HighlightNote = {
      id: `note_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      start: selectedRange.start,
      end: selectedRange.end,
      capturedText: selectedText,
      mainCategory,
      subcategory,
      customSubcategory: "",
      nodeLabel: CATEGORY_CONFIG[mainCategory].label,
      details: "",
    };

    setNotes((prev) => [...prev, note].sort(byStart));
    setCollapsedNoteIds((prev) => {
      const next = new Set(prev);
      next.delete(note.id);
      return next;
    });
    setActiveCategory(mainCategory);
    setActiveSubcategory(subcategory);
    setActiveNoteId(note.id);
    setPendingKeyboardCategory(null);
    setSelectedRange(null);
    setSelectedText("");
    setError("");
    window.getSelection()?.removeAllRanges();
  };

  const moveNote = (noteId: string, mainCategory: MainCategory, subcategory: string): void => {
    setNotes((prev) =>
      prev
        .map((note) => {
          if (note.id !== noteId) {
            return note;
          }
          return {
            ...note,
            mainCategory,
            subcategory,
            customSubcategory: subcategory === "other" ? note.customSubcategory : "",
          };
        })
        .sort(byStart),
    );
    setActiveCategory(mainCategory);
    setActiveSubcategory(subcategory);
    setActiveNoteId(noteId);
  };

  const parseDropTarget = (id: string): { mainCategory: MainCategory; subcategory: string } | null => {
    if (id.startsWith("sub-")) {
      const parts = id.split("-");
      const mainCategory = parts[1] as MainCategory;
      const subcategory = parts.slice(2).join("-");
      if (!CATEGORY_ORDER.includes(mainCategory)) {
        return null;
      }
      return { mainCategory, subcategory };
    }
    if (id.startsWith("cat-")) {
      const mainCategory = id.replace("cat-", "") as MainCategory;
      if (!CATEGORY_ORDER.includes(mainCategory)) {
        return null;
      }
      const fallbackSub = SUBCATEGORY_OPTIONS[mainCategory][0]?.value ?? "other";
      return { mainCategory, subcategory: fallbackSub };
    }
    return null;
  };

  const onDragStart = (event: DragStartEvent): void => {
    const kind = event.active.data.current?.kind;
    if (kind === "selection") {
      setDragState({ kind: "selection", text: selectedText });
      return;
    }
    if (kind === "note") {
      const noteId = event.active.data.current?.noteId as string | undefined;
      if (!noteId) {
        setDragState(null);
        return;
      }
      const note = notes.find((item) => item.id === noteId);
      if (!note) {
        setDragState(null);
        return;
      }
      setDragState({ kind: "note", noteId, label: note.nodeLabel || note.capturedText });
      return;
    }
    setDragState(null);
  };

  const onDragEnd = (event: DragEndEvent): void => {
    setDragState(null);
    const overId = event.over?.id;
    if (!overId || typeof overId !== "string") {
      return;
    }

    const parsed = parseDropTarget(overId);
    if (!parsed) {
      return;
    }

    const kind = event.active.data.current?.kind;
    if (kind === "selection") {
      addNote(parsed.mainCategory, parsed.subcategory);
      return;
    }
    if (kind === "note") {
      const noteId = event.active.data.current?.noteId as string | undefined;
      if (!noteId) {
        return;
      }
      moveNote(noteId, parsed.mainCategory, parsed.subcategory);
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if (!selectedRange) {
        return;
      }

      const target = event.target as HTMLElement | null;
      if (target) {
        const tag = target.tagName.toLowerCase();
        if (tag === "input" || tag === "textarea" || target.isContentEditable) {
          return;
        }
      }

      if (!pendingKeyboardCategory) {
        if (event.key === "1") {
          event.preventDefault();
          setActiveCategory("requirement");
          setPendingKeyboardCategory("requirement");
          setError("Requirement selected. Press 1-4 to choose subcategory.");
        } else if (event.key === "2") {
          event.preventDefault();
          setActiveCategory("info");
          setPendingKeyboardCategory("info");
          setError("Info selected. Press 1-8 to choose subcategory.");
        }
        return;
      }

      if (event.key === "Escape") {
        setPendingKeyboardCategory(null);
        setError("");
        return;
      }

      const options = SUBCATEGORY_OPTIONS[pendingKeyboardCategory];
      const index = Number(event.key) - 1;
      if (Number.isNaN(index) || index < 0 || index >= options.length) {
        return;
      }
      event.preventDefault();
      addNote(pendingKeyboardCategory, options[index].value);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedRange, selectedText, notes, pendingKeyboardCategory]);

  const updateNote = (id: string, patch: Partial<HighlightNote>): void => {
    setNotes((prev) =>
      prev.map((note) => {
        if (note.id !== id) {
          return note;
        }
        const merged = { ...note, ...patch };
        const validSub = SUBCATEGORY_OPTIONS[merged.mainCategory].some(
          (option) => option.value === merged.subcategory,
        );
        if (!validSub) {
          merged.subcategory = SUBCATEGORY_OPTIONS[merged.mainCategory][0]?.value ?? "other";
          merged.customSubcategory = "";
        }
        if (merged.subcategory !== "other") {
          merged.customSubcategory = "";
        }
        return merged;
      }),
    );
  };

  const removeNote = (id: string): void => {
    setNotes((prev) => prev.filter((note) => note.id !== id));
    setCollapsedNoteIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    if (activeNoteId === id) {
      setActiveNoteId("");
    }
  };

  const toggleCollapse = (id: string): void => {
    setCollapsedNoteIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const activeNotes = notesByCategory[activeCategory];
  const filteredNotes = activeNotes.filter((note) => {
    if (note.subcategory !== activeSubcategory) {
      return false;
    }
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      return true;
    }
    const haystack = [
      note.capturedText,
      note.nodeLabel,
      note.details,
      note.mainCategory,
      note.subcategory,
      note.customSubcategory,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });

  return (
    <DndContext sensors={sensors} onDragStart={onDragStart} onDragEnd={onDragEnd}>
      <section className="highlight-editor">
        <div className="highlight-toolbar">
          <span className="highlight-selection-preview">
            1) Select text 2) Choose main category (1=Requirement, 2=Info) 3) Pick subcategory (click/drag or number)
          </span>
          {selectedRange ? <SelectionChip text={selectedText} /> : null}
        </div>

        {error ? <p className="error">{error}</p> : null}

        <div className="highlight-body">
          <div
            ref={editorRef}
            className="highlight-canvas"
            onMouseUp={captureSelection}
            onKeyUp={captureSelection}
            role="textbox"
            aria-label="highlight editor"
            tabIndex={0}
          >
            {segments.map((segment) => {
              if (!segment.noteId || !segment.mainCategory) {
                return <span key={`${segment.start}-${segment.end}`}>{segment.text}</span>;
              }
              const isActive = activeNoteId === segment.noteId;
              return (
                <mark
                  key={segment.noteId}
                  className={`highlight-segment${isActive ? " highlight-segment-active" : ""}`}
                  style={{
                    backgroundColor: `${categoryColor(segment.mainCategory, segment.subcategory ?? "other")}33`,
                    borderColor: categoryColor(segment.mainCategory, segment.subcategory ?? "other"),
                  }}
                  onClick={() => setActiveNoteId(segment.noteId ?? "")}
                >
                  {segment.text}
                </mark>
              );
            })}
          </div>

          <aside className="highlight-sidebar">
            <h3>Category Boxes</h3>
            <div className="main-category-tabs">
              {CATEGORY_ORDER.map((category, index) => {
                const list = notesByCategory[category];
                const firstSub = SUBCATEGORY_OPTIONS[category][0]?.value ?? "other";
                return (
                  <MainCategoryBox
                    key={category}
                    category={category}
                    count={list.length}
                    isActive={activeCategory === category}
                    hasSelection={Boolean(selectedRange)}
                    shortcut={String(index + 1)}
                    onSelect={() => {
                      setActiveCategory(category);
                      setActiveSubcategory(firstSub);
                      if (selectedRange) {
                        setPendingKeyboardCategory(category);
                      }
                    }}
                  />
                );
              })}
            </div>

            <div className="subcategory-grid">
              {activeSubOptions.map((option, index) => {
                const list = activeNotes.filter((note) => note.subcategory === option.value);
                return (
                  <SubcategoryBox
                    key={option.value}
                    category={activeCategory}
                    subcategory={option}
                    count={list.length}
                    firstText={shortPreview(list[0]?.capturedText ?? "")}
                    isActive={activeSubcategory === option.value}
                    hasSelection={Boolean(selectedRange)}
                    shortcut={String(index + 1)}
                    onSelect={() => {
                      if (selectedRange) {
                        addNote(activeCategory, option.value);
                      } else {
                        setActiveSubcategory(option.value);
                      }
                    }}
                  />
                );
              })}
            </div>

            <section className="category-details">
              <div className="category-details-header">
                <h4>{CATEGORY_CONFIG[activeCategory].label} Notes</h4>
                <input
                  className="note-search-input"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search notes..."
                />
              </div>

              {filteredNotes.length === 0 ? <p>No highlights for this category/search.</p> : null}

              <div className="highlight-note-list note-list-scroll">
                {filteredNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    isCollapsed={collapsedNoteIds.has(note.id)}
                    isActive={activeNoteId === note.id}
                    onCardClick={() => {
                      setActiveNoteId(note.id);
                      toggleCollapse(note.id);
                    }}
                    onRemove={() => removeNote(note.id)}
                    onUpdate={(patch) => updateNote(note.id, patch)}
                  />
                ))}
              </div>
            </section>
          </aside>
        </div>

        <DragOverlay>
          {dragState?.kind === "selection" ? (
            <div className="selection-chip selection-chip-overlay">Drop into category/subcategory</div>
          ) : null}
          {dragState?.kind === "note" ? (
            <div className="selection-chip selection-chip-overlay">Move note: {shortPreview(dragState.label)}</div>
          ) : null}
        </DragOverlay>
      </section>
    </DndContext>
  );
}
