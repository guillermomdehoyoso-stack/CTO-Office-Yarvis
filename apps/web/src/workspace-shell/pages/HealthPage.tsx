import { useQuery } from '@tanstack/react-query';
import { getHealth } from '../../api/workspacePlatform';
import { MetricCard } from '../MetricCard';

export function HealthPage({ workspaceId }: { workspaceId: string }) {
  const health = useQuery({ queryKey: ['health', workspaceId], queryFn: () => getHealth(workspaceId), retry: false });

  if (health.isLoading) return <p>Loading health...</p>;
  if (health.error || !health.data) return <p>Health unavailable.</p>;

  return (
    <section>
      <h1>Health</h1>
      <div className="metrics-grid">
        <MetricCard metric="Workspace" value={health.data.workspace_id} />
        <MetricCard metric="Platform Status" value={health.data.status} />
        <MetricCard metric="Engineering Health" value={health.data.engineering_health} />
      </div>
      <h2>Service Status</h2>
      <div className="list-panel compact">
        {Object.entries(health.data.services).map(([service, state]) => (
          <div className="list-row" key={service}>
            <span>{service}</span>
            <span>{state}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
