import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import './yarvisExperiencePrototype.css';

type Attention = 'stable' | 'active' | 'attention' | 'critical';
type Health = 'steady' | 'watch' | 'strained';

type Area = {
  id: string;
  name: string;
  classification: string;
  critical: number;
  active: number;
};

type Space = {
  id: string;
  name: string;
  initials: string;
  health: Health;
  attention: Attention;
  active: number;
  critical: number;
  recent: string;
  lastActivity: string;
  areas: Area[];
};

type Scenario = 'stable' | 'energy_attention' | 'multi_active';

const areaCatalog: Record<string, Area[]> = {
  energy: [
    ['commercial', 'Commercial', 'Navigation grouping'], ['engineering', 'Engineering', 'Navigation grouping'],
    ['procurement', 'Procurement', 'Navigation grouping'], ['installation', 'Installation', 'Vertical capability'],
    ['regulatory', 'CFE / Regulatory', 'Navigation grouping'], ['documents', 'Documents', 'Read-model surface'],
    ['economics', 'Economics', 'Bounded context'], ['om', 'O&M', 'Navigation grouping'],
  ].map(([id, name, classification], index) => ({ id, name, classification, critical: index === 3 ? 2 : 0, active: 3 + (index % 4) })),
  netpay: [
    ['merchant', 'Merchant Operations', 'Bounded context'], ['recovery', 'Recovery', 'Read-model surface'],
    ['intelligence', 'Store Intelligence', 'Read-model surface'], ['documents', 'Documents', 'Read-model surface'],
    ['economics', 'Economics', 'Bounded context'], ['support', 'Support', 'Read-model surface'],
  ].map(([id, name, classification], index) => ({ id, name, classification, critical: index === 1 ? 1 : 0, active: 2 + index })),
  trading: [
    ['market-watch', 'Market Watch', 'Vertical capability'], ['signals', 'Signals', 'Vertical capability'],
    ['strategies', 'Strategies', 'Vertical capability'], ['orders', 'Orders', 'Vertical capability'],
    ['positions', 'Positions', 'Vertical capability'], ['risk', 'Risk', 'Transversal projection'],
    ['performance', 'Performance', 'Vertical capability'],
  ].map(([id, name, classification], index) => ({ id, name, classification, critical: index === 5 ? 1 : 0, active: 2 + (index % 3) })),
};

function scenarioSpaces(scenario: Scenario): Space[] {
  const base: Space[] = [
    { id: 'energy', name: 'Energía Fotónica', initials: 'EF', health: 'steady', attention: 'stable', active: 14, critical: 1, recent: '2 updates today', lastActivity: '18 min ago', areas: areaCatalog.energy },
    { id: 'netpay', name: 'NetPay', initials: 'NP', health: 'steady', attention: 'active', active: 11, critical: 1, recent: '5 updates today', lastActivity: '7 min ago', areas: areaCatalog.netpay },
    { id: 'trading', name: 'Trading / Finance', initials: 'TF', health: 'watch', attention: 'active', active: 9, critical: 1, recent: '4 updates today', lastActivity: '12 min ago', areas: areaCatalog.trading },
  ];
  if (scenario === 'energy_attention') {
    return base.map((space) => space.id === 'energy'
      ? { ...space, health: 'strained', attention: 'critical', active: 21, critical: 5, recent: '8 updates in the last hour', lastActivity: '2 min ago' }
      : space);
  }
  if (scenario === 'multi_active') {
    return base.map((space, index) => ({ ...space, health: 'watch', attention: 'active', active: space.active + 7 + index, critical: 2, recent: `${6 + index} updates today`, lastActivity: `${3 + index * 3} min ago` }));
  }
  return base;
}

function labelFor(space: Space): string {
  return `${space.name}. ${space.active} active work items. ${space.critical} critical actions. Health: ${space.health}. Attention: ${space.attention}. Last activity ${space.lastActivity}.`;
}

export function YarvisExperiencePrototype() {
  const [scenario, setScenario] = useState<Scenario>('stable');
  const [motion, setMotion] = useState(true);
  const [structured, setStructured] = useState(false);
  const [spaceId, setSpaceId] = useState<string | null>(null);
  const [areaId, setAreaId] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const spaces = useMemo(() => scenarioSpaces(scenario), [scenario]);
  const selectedSpace = spaces.find((space) => space.id === spaceId) ?? null;
  const selectedArea = selectedSpace?.areas.find((area) => area.id === areaId) ?? null;

  useEffect(() => {
    headingRef.current?.focus();
  }, [spaceId, areaId, workspace]);

  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') goBack();
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  });

  function goBack() {
    if (workspace) { setWorkspace(false); return; }
    if (areaId) { setAreaId(null); return; }
    if (spaceId) setSpaceId(null);
  }

  const globalCritical = spaces.reduce((sum, space) => sum + space.critical, 0);
  const isHome = !selectedSpace;

  return <section className={`yarvis-prototype ${motion ? 'motion-enabled' : 'motion-reduced'} ${structured ? 'structured-preferred' : ''}`} aria-label="YARVIS interactive experience prototype">
    <header className="prototype-controls">
      <div><strong>UX-002 prototype</strong><span>Static data only · not a production route</span></div>
      <label>Scenario<select aria-label="Scenario" value={scenario} onChange={(event) => { setScenario(event.target.value as Scenario); setSpaceId(null); setAreaId(null); setWorkspace(false); }}>
        <option value="stable">Stable day</option><option value="energy_attention">Energía Fotónica needs attention</option><option value="multi_active">Multi-space active day</option>
      </select></label>
      <button type="button" aria-pressed={!motion} onClick={() => setMotion((value) => !value)}>{motion ? 'Reduce motion' : 'Enable motion'}</button>
      <button type="button" aria-pressed={structured} onClick={() => setStructured((value) => !value)}>{structured ? 'Show spatial field' : 'Show structured fallback'}</button>
    </header>

    <p className="prototype-status" aria-live="polite">Scenario: {scenario.replaceAll('_', ' ')}. Motion: {motion ? 'normal' : 'reduced'}. {globalCritical} global critical actions.</p>

    {!isHome && <button className="prototype-back" type="button" onClick={goBack}>← Back {workspace ? 'to area' : areaId ? 'to space' : 'to YARVIS Home'}</button>}

    {isHome && <Home headingRef={headingRef} spaces={spaces} critical={globalCritical} structured={structured} onSelect={setSpaceId} />}
    {selectedSpace && !selectedArea && <SpaceView headingRef={headingRef} space={selectedSpace} structured={structured} onSelectArea={setAreaId} />}
    {selectedSpace && selectedArea && !workspace && <AreaView headingRef={headingRef} space={selectedSpace} area={selectedArea} onWorkspace={() => setWorkspace(true)} />}
    {selectedSpace && selectedArea && workspace && <WorkspaceView headingRef={headingRef} space={selectedSpace} area={selectedArea} />}
  </section>;
}

function Home({ headingRef, spaces, critical, structured, onSelect }: { headingRef: RefObject<HTMLHeadingElement>; spaces: Space[]; critical: number; structured: boolean; onSelect: (id: string) => void }) {
  return <main>
    <div className="prototype-intro"><p className="eyebrow">YARVIS Home</p><h1 ref={headingRef} tabIndex={-1}>Your operational universe, at a glance.</h1><p>Three visible Operational Spaces. State is expressed through labelled, explainable categories—not a hidden score.</p></div>
    <aside className="yarvis-presence" aria-label={`YARVIS global briefing: ${critical} critical actions`}><strong>Y</strong><div><span>Global Critical Actions</span><b>{critical}</b><p>Review the spaces with explicit attention markers first.</p></div></aside>
    <SpaceNavigator spaces={spaces} structured={structured} onSelect={onSelect} />
  </main>;
}

function SpaceView({ headingRef, space, structured, onSelectArea }: { headingRef: RefObject<HTMLHeadingElement>; space: Space; structured: boolean; onSelectArea: (id: string) => void }) {
  return <main>
    <div className="prototype-intro"><p className="eyebrow">Operational Space</p><h1 ref={headingRef} tabIndex={-1}>{space.name}</h1><p><b>{space.critical} Critical Actions</b> · {space.active} active work · Health: {space.health} · Last activity: {space.lastActivity}</p></div>
    <section className="space-summary" aria-label={`${space.name} summary`}><span>Recent activity: {space.recent}</span><span>Attention: {space.attention}</span><span>Area cells are navigation only; structured Workspace follows.</span></section>
    <AreaNavigator areas={space.areas} spaceName={space.name} structured={structured} onSelect={onSelectArea} />
  </main>;
}

function AreaView({ headingRef, space, area, onWorkspace }: { headingRef: RefObject<HTMLHeadingElement>; space: Space; area: Area; onWorkspace: () => void }) {
  return <main className="area-view"><p className="eyebrow">Operational Area · {space.name}</p><h1 ref={headingRef} tabIndex={-1}>{area.name}</h1><p>{area.classification}. {area.critical} local Critical Actions and {area.active} active work items are represented with explicit counters.</p><section className="area-action"><h2>Move into the Structured Operational Workspace</h2><p>The cellular metaphor stops here so work can be read and acted on precisely.</p><button type="button" onClick={onWorkspace}>Open structured workspace preview</button></section></main>;
}

function WorkspaceView({ headingRef, space, area }: { headingRef: RefObject<HTMLHeadingElement>; space: Space; area: Area }) {
  const taskCount = Math.max(3, area.active);
  return <main className="structured-workspace"><p className="eyebrow">Structured Operational Workspace · {space.name} / {area.name}</p><h1 ref={headingRef} tabIndex={-1}>Operational workspace preview</h1><section className="metric-grid" aria-label="Workspace metrics"><Metric label="Active tasks" value={String(taskCount)} /><Metric label="Blocked tasks" value={String(area.critical)} /><Metric label="Active processes" value="3" /><Metric label="Recent activity" value={space.recent.split(' ')[0]} /></section><section className="workspace-columns"><article><h2>Active Tasks</h2><ul>{Array.from({ length: Math.min(taskCount, 4) }, (_, index) => <li key={index}>#{index + 1} Review {area.name.toLowerCase()} operational item <span>ready</span></li>)}</ul></article><article><h2>Blocked Tasks</h2><ul>{area.critical ? Array.from({ length: area.critical }, (_, index) => <li key={index}>Dependency review required <span>critical</span></li>) : <li>No blocked tasks</li>}</ul></article><article><h2>Active Processes</h2><ul><li>Operational review <span>active</span></li><li>Evidence follow-up <span>active</span></li><li>Context confirmation <span>waiting</span></li></ul></article><article><h2>Recent Activity</h2><ol><li>{space.lastActivity}: update received</li><li>Today: work item reassessed</li><li>Yesterday: process moved forward</li></ol></article></section></main>;
}

function Metric({ label, value }: { label: string; value: string }) { return <article className="metric"><span>{label}</span><strong>{value}</strong></article>; }

function SpaceNavigator({ spaces, structured, onSelect }: { spaces: Space[]; structured: boolean; onSelect: (id: string) => void }) {
  return <section className={structured ? 'structured-list' : 'cell-field'} aria-label="Operational Spaces">{spaces.map((space) => <button key={space.id} type="button" className={`space-cell attention-${space.attention} health-${space.health}`} aria-label={labelFor(space)} onClick={() => onSelect(space.id)}><span className="cell-initials" aria-hidden="true">{space.initials}</span><span className="cell-name">{space.name}</span><span className="cell-state">{space.attention} · {space.health}</span><span className="cell-counters"><b>{space.active} active</b><b>{space.critical} critical</b></span><span className="cell-recent">{space.recent} · {space.lastActivity}</span></button>)}</section>;
}

function AreaNavigator({ areas, spaceName, structured, onSelect }: { areas: Area[]; spaceName: string; structured: boolean; onSelect: (id: string) => void }) {
  return <section className={structured ? 'structured-list area-list' : 'area-field'} aria-label={`${spaceName} Operational Areas`}>{areas.map((area) => <button key={area.id} type="button" className={`area-cell ${area.critical ? 'area-attention' : ''}`} aria-label={`${area.name}. ${area.classification}. ${area.active} active work items. ${area.critical} critical actions.`} onClick={() => onSelect(area.id)}><span>{area.name}</span><small>{area.classification}</small><b>{area.active} active · {area.critical} critical</b></button>)}</section>;
}
