# Component Templates — Terran Command UI

Plantillas estándar para cada capa del Diseño Atómico.
**Regla universal:** todo componente acepta `className` y propaga `...props`.
Usar siempre `cn()` de `src/utils/cn.ts`.

---

## 1. Átomo (Atom)

Elementos indivisibles: Button, Badge, Tag, Kbd, Spinner.

**Reglas:**
- Siempre `forwardRef` — librerías de D&D, tooltips y focus management lo necesitan
- Sin estado complejo, sin llamadas a API
- La prop `className` siempre va al final del `cn()` para que el padre pueda sobrescribir

```tsx
import { forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface ComponentNameProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  // className y children vienen incluidos en HTMLAttributes
}

export const ComponentName = forwardRef<HTMLDivElement, ComponentNameProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {

    const baseStyles = 'inline-flex items-center justify-center transition-colors';

    const variants = {
      primary:   'bg-primary/10 text-primary border border-primary/30',
      secondary: 'bg-secondary/10 text-secondary border border-secondary/30',
      ghost:     'bg-transparent text-on-muted hover:text-on-surface',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-[10px]',
      md: 'px-4 py-2 text-xs',
      lg: 'px-6 py-3 text-sm',
    };

    return (
      <div
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ComponentName.displayName = 'ComponentName';
```

---

## 2. Molécula (Molecule)

Agrupación simple de átomos. SplitPane, DiagnosticCard, ControlPanel.

**Reglas:**
- Componente "tonto" — recibe datos por props, no hace `useQuery`
- Puede tener micro-estado visual local (hover, open/closed)
- Siempre exporta la interface de props (la necesitarán los tests)

```tsx
import { cn } from '@/utils/cn';
import { Badge } from '@/components/atoms/Badge';
import { Button } from '@/components/atoms/Button';

export interface MoleculeNameProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  status: 'verified' | 'pending' | 'error';
  onAction?: () => void;
}

export function MoleculeName({ title, status, onAction, className, ...props }: MoleculeNameProps) {
  return (
    <div
      className={cn('flex flex-col gap-3 p-4 bg-surface-high panel-border', className)}
      {...props}
    >
      <div className="flex justify-between items-center">
        <h3 className="font-headline text-sm font-bold text-on-surface">{title}</h3>
        <Badge variant={status === 'error' ? 'danger' : status === 'verified' ? 'success' : 'muted'}>
          {status}
        </Badge>
      </div>
      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={onAction}>
          Revisar
        </Button>
      </div>
    </div>
  );
}
```

---

## 3. Organismo (Organism)

Secciones complejas: IntelligentEditor, GraphCanvas, RequirementList, EvidenceBankSidebar.

**Reglas:**
- Pueden vivir en `src/features/.../components/`
- Pueden tener `useState` para estado UI local (tabs, acordeones, hover)
- Reciben datos complejos como props — no hacen `useQuery` directamente
- Delegan mutaciones al hook padre vía callbacks
- Early returns para `isLoading` y `isEmpty`

```tsx
import { useState } from 'react';
import { cn } from '@/utils/cn';
import { MoleculeName } from '@/components/molecules/MoleculeName';

export interface OrganismNameProps {
  items: Array<{ id: string; title: string; status: 'verified' | 'pending' | 'error' }>;
  isLoading?: boolean;
  onItemUpdate: (id: string, data: unknown) => void;
  className?: string;
}

export function OrganismName({ items, isLoading, onItemUpdate, className }: OrganismNameProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className={cn('p-8 flex justify-center text-on-muted font-mono text-sm', className)}>
        Loading...
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className={cn('p-8 text-center border border-dashed border-outline/30 text-on-muted font-mono text-sm', className)}>
        No items.
      </div>
    );
  }

  return (
    <section className={cn('flex flex-col gap-2 w-full', className)}>
      {items.map((item) => (
        <MoleculeName
          key={item.id}
          title={item.title}
          status={item.status}
          onAction={() => {
            setExpandedId(item.id === expandedId ? null : item.id);
            onItemUpdate(item.id, { viewed: true });
          }}
          className={item.id === expandedId ? 'border-primary tactical-glow' : ''}
        />
      ))}
    </section>
  );
}
```

---

## 4. Layout / Shell

AppShell, JobWorkspaceShell, SplitPane.

**Reglas:**
- Sin conocimiento de datos de negocio
- Su trabajo: Grid/Flexbox + `<Outlet />` o `children`
- Pueden recibir slots nombrados (`leftPanel`, `rightPanel`) para composición flexible

```tsx
import { cn } from '@/utils/cn';

export interface ShellNameProps {
  children?: React.ReactNode;
  leftPanel?: React.ReactNode;
  className?: string;
}

export function ShellName({ children, leftPanel, className }: ShellNameProps) {
  return (
    <div className={cn('flex h-screen w-full bg-background text-on-surface overflow-hidden', className)}>

      {leftPanel && (
        <aside className="w-64 shrink-0 border-r border-outline/10 bg-surface z-10">
          {leftPanel}
        </aside>
      )}

      <main className="flex-1 relative flex flex-col min-w-0 overflow-y-auto">
        {children}
      </main>

    </div>
  );
}
```

---

## Anti-patrones prohibidos

| Prohibido | Correcto |
|-----------|----------|
| `style={{ color: '#00f2ff' }}` | `className="text-primary"` |
| `useEffect + fetch` para datos del servidor | `useQuery` de React Query |
| Lógica de negocio en `pages/` | Todo en `features/` |
| `className="bg-blue-500"` en un átomo sin `cn()` | `cn('bg-primary', className)` |
| Crear un archivo `.css` nuevo | Tailwind utilities o `@layer utilities` en `styles.css` |
| Datos literales hardcodeados en componentes (`const jobs = [...]`) | Todo dato viene del mock/API via `useQuery` — nunca arrays estáticos en el render |
