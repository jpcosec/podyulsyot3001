import { Group, Panel, Separator } from 'react-resizable-panels';
import { cn } from '../../utils/cn';

interface Props {
  orientation?: 'horizontal' | 'vertical';
  defaultSizes?: [number, number];   // percentages 0–100
  minSizes?: [number, number];
  className?: string;
  children: [React.ReactNode, React.ReactNode];
}

export function SplitPane({
  orientation = 'horizontal',
  defaultSizes = [50, 50],
  minSizes = [20, 20],
  className,
  children,
}: Props) {
  return (
    <Group
      orientation={orientation}
      defaultLayout={{ start: defaultSizes[0], end: defaultSizes[1] }}
      className={cn('h-full w-full', className)}
    >
      <Panel id="start" defaultSize={defaultSizes[0]} minSize={minSizes[0]}>
        {children[0]}
      </Panel>
      <Separator className={cn(
        orientation === 'horizontal'
          ? 'w-px bg-outline/20 hover:bg-primary/40 transition-colors cursor-col-resize'
          : 'h-px bg-outline/20 hover:bg-primary/40 transition-colors cursor-row-resize'
      )} />
      <Panel id="end" defaultSize={defaultSizes[1]} minSize={minSizes[1]}>
        {children[1]}
      </Panel>
    </Group>
  );
}
