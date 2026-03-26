import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

export function FiltersSection() {
  const edges = useGraphStore((state) => state.edges);
  const filters = useUIStore((state) => state.filters);
  const setFilter = useUIStore((state) => state.setFilter);
  const clearFilters = useUIStore((state) => state.clearFilters);

  const relationTypes = useMemo(() => {
    return [...new Set(edges.map((edge) => edge.data?.relationType ?? 'linked'))].sort();
  }, [edges]);

  const [attrFilterOpen, setAttrFilterOpen] = useState(false);
  const [attrKey, setAttrKey] = useState(filters.attributeFilter?.key ?? '');
  const [attrValue, setAttrValue] = useState(filters.attributeFilter?.value ?? '');

  const applyAttributeFilter = () => {
    const key = attrKey.trim();
    const value = attrValue.trim();

    setFilter({
      attributeFilter: key || value ? { key, value } : null,
    });
    setAttrFilterOpen(false);
  };

  const resetAllFilters = () => {
    clearFilters();
    setAttrKey('');
    setAttrValue('');
  };

  return (
    <div className="space-y-2 px-3 pb-3">
      <Input
        placeholder="Search nodes..."
        value={filters.filterText}
        onChange={(event) => setFilter({ filterText: event.target.value })}
      />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="w-full justify-between">
            Relation Types
            <span className="text-[10px] text-muted-foreground">{relationTypes.length}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuLabel>Visible Relations</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {relationTypes.length === 0 && <div className="px-2 py-1 text-xs text-muted-foreground">No relation types</div>}
          {relationTypes.map((type) => {
            const visible = !filters.hiddenRelationTypes.includes(type);
            return (
              <DropdownMenuCheckboxItem
                key={type}
                checked={visible}
                onCheckedChange={(checked) => {
                  const shouldShow = checked === true;
                  const hiddenRelationTypes = shouldShow
                    ? filters.hiddenRelationTypes.filter((current) => current !== type)
                    : [...filters.hiddenRelationTypes, type];
                  setFilter({ hiddenRelationTypes });
                }}
              >
                {type}
              </DropdownMenuCheckboxItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      <Popover open={attrFilterOpen} onOpenChange={setAttrFilterOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="w-full">
            Filter by Attribute
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-56" align="start">
          <div className="space-y-2">
            <Input
              placeholder="Attribute key"
              value={attrKey}
              onChange={(event) => setAttrKey(event.target.value)}
            />
            <Input
              placeholder="Attribute value contains"
              value={attrValue}
              onChange={(event) => setAttrValue(event.target.value)}
            />
            <div className="flex gap-1">
              <Button size="sm" onClick={applyAttributeFilter} className="flex-1">
                Apply
              </Button>
              <Button size="sm" variant="outline" onClick={resetAllFilters} className="flex-1">
                Clear
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      <label className="flex items-center gap-2 text-xs text-muted-foreground">
        <input
          type="checkbox"
          checked={filters.hideNonNeighbors}
          onChange={(event) => setFilter({ hideNonNeighbors: event.target.checked })}
        />
        Hide non-neighbors in focus mode
      </label>
    </div>
  );
}
