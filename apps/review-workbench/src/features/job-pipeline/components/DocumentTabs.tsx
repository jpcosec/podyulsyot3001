import { cn } from '../../../utils/cn';

export type DocKey = 'cv' | 'motivation_letter' | 'application_email';

const TAB_LABELS: Record<DocKey, string> = {
  cv: 'CV',
  motivation_letter: 'COVER LETTER',
  application_email: 'EMAIL',
};

interface TabState {
  isDirty: boolean;
  isApproved: boolean;
}

interface Props {
  activeTab: DocKey;
  tabStates: Record<DocKey, TabState>;
  onTabChange: (key: DocKey) => void;
}

export function DocumentTabs({ activeTab, tabStates, onTabChange }: Props) {
  const tabs: DocKey[] = ['cv', 'motivation_letter', 'application_email'];

  return (
    <div className="flex border-b border-outline/20 bg-surface-container">
      {tabs.map(key => {
        const state = tabStates[key];
        const isActive = activeTab === key;
        return (
          <button
            key={key}
            onClick={() => onTabChange(key)}
            className={cn(
              'px-4 py-2.5 font-headline text-xs uppercase tracking-widest transition-colors flex items-center gap-1.5',
              isActive
                ? 'text-primary border-b-2 border-primary'
                : 'text-on-muted hover:text-on-surface'
            )}
          >
            {state.isApproved && <span className="text-primary">✓</span>}
            {state.isDirty && !state.isApproved && <span className="text-secondary">●</span>}
            {TAB_LABELS[key]}
          </button>
        );
      })}
    </div>
  );
}
