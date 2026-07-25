export function StatusBar({ sprint, gate }: { sprint: string; gate: string }) {
  return (
    <div className="status-bar">
      <span>Sprint: {sprint}</span>
      <span>Gate: {gate}</span>
    </div>
  );
}
