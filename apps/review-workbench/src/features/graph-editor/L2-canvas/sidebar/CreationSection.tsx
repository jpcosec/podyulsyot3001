import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { registry } from '@/schema/registry';
import { useGraphStore } from '@/stores/graph-store';
import type { ASTNode } from '@/stores/types';

function getDefaultPayloadValue(label: string): Record<string, string> {
  return { name: label };
}

export function CreationSection() {
  const [open, setOpen] = useState(false);
  const addElements = useGraphStore((state) => state.addElements);

  const nodeTypes = registry.getAll();

  const handleCreate = (typeId: string) => {
    const definition = registry.get(typeId);
    if (!definition) {
      return;
    }

    const newNode: ASTNode = {
      id: `node-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'node',
      position: {
        x: 160 + Math.random() * 400,
        y: 120 + Math.random() * 320,
      },
      data: {
        typeId,
        payload: {
          typeId,
          value: getDefaultPayloadValue(definition.label),
        },
        properties: {},
        visualToken: definition.colorToken,
      },
    };

    addElements([newNode], []);
    setOpen(false);
  };

  return (
    <div className="px-3 pb-3">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="w-full">
            Add Node +
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[260px] p-0" side="left" align="start">
          <Command>
            <CommandInput placeholder="Search node types..." />
            <CommandList>
              <CommandEmpty>No node type found.</CommandEmpty>
              <CommandGroup heading="Node Types">
                {nodeTypes.map((nodeType) => (
                  <CommandItem
                    key={nodeType.typeId}
                    value={`${nodeType.label} ${nodeType.category}`}
                    onSelect={() => handleCreate(nodeType.typeId)}
                  >
                    <span>{nodeType.label}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{nodeType.category}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
