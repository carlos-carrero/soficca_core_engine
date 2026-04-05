import { VERSION_METADATA } from '@/lib/cardio-ui-adapter';

export function Header() {
  return (
    <header className="border-b border-border bg-card/50">
      <div className="mx-auto max-w-[1600px] px-6 py-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-0.5">
            <h1 className="text-base font-semibold tracking-tight text-foreground">Soficca</h1>
            <p className="text-[11px] text-muted-foreground/70">Clinical Decision Infrastructure</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <VersionBadge label="Engine" version={VERSION_METADATA.engineVersion} />
            <VersionBadge label="Ruleset" version={VERSION_METADATA.rulesetVersion} />
            <VersionBadge label="Safety" version={VERSION_METADATA.safetyPolicyVersion} />
            <VersionBadge label="Contract" version={VERSION_METADATA.contractVersion} />
          </div>
        </div>
      </div>
    </header>
  );
}

function VersionBadge({ label, version }: { label: string; version: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground/50">{label}</span>
      <span className="font-mono text-[10px] text-muted-foreground">{version}</span>
    </div>
  );
}
