import { useQuery } from '@tanstack/react-query';
import { getDashboard } from '../../api/workspacePlatform';
import type { DashboardResponse } from '../../types/workspacePlatform';
import { MetricCard } from '../MetricCard';

export function DashboardPage({ workspaceId }: { workspaceId: string }) {
  const dashboard = useQuery({ queryKey: ['dashboard', workspaceId], queryFn: () => getDashboard(workspaceId), retry: false });

  if (dashboard.isLoading) return <p>Loading dashboard...</p>;
  if (dashboard.error || !dashboard.data) return <p>Workspace dashboard unavailable.</p>;

  const model: DashboardResponse = dashboard.data;
  return (
    <section>
      <h1>{model.workspace_name}</h1>
      <p>WS-000 Development Workspace running on the reusable platform.</p>
      <div className="metrics-grid">
        <MetricCard metric="Current Sprint" value={model.current_sprint} />
        <MetricCard metric="Current Gate" value={model.current_gate} />
        <MetricCard metric="Files Indexed" value={model.repository_health.total_files} />
        <MetricCard metric="Docs Indexed" value={model.repository_health.documentation_files} />
        <MetricCard metric="Python Files" value={model.repository_health.python_files} />
        <MetricCard metric="TypeScript Files" value={model.repository_health.typescript_files} />
      </div>
    </section>
  );
}
