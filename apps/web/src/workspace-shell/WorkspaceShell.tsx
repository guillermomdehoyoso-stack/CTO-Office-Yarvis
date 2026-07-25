import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import {
  getWorkspace,
  getWorkspaceAccessToken,
  getWorkspaces,
  setWorkspaceAccessToken,
} from '../api/workspacePlatform';
import { ObserverPanel } from './ObserverPanel';
import { SidebarNav, type NavEntry } from './SidebarNav';
import { StatusBar } from './StatusBar';
import { WorkspaceHeader } from './WorkspaceHeader';
import { DashboardPage } from './pages/DashboardPage';
import { HealthPage } from './pages/HealthPage';
import { RepositoryPage } from './pages/RepositoryPage';
import { SearchBackedPage } from './pages/SearchBackedPage';
import { TimelinePage } from './pages/TimelinePage';
import "./workspace.css";

const PAGE_NAV: NavEntry[] = [
  { path: 'dashboard', label: 'Dashboard' },
  { path: 'timeline', label: 'Timeline' },
  { path: 'repository', label: 'Repository' },
  { path: 'roadmap', label: 'Roadmap' },
  { path: 'reviews', label: 'Reviews' },
  { path: 'prompts', label: 'Prompts' },
  { path: 'architecture', label: 'Architecture' },
  { path: 'health', label: 'Health' },
];

export function WorkspaceShell() {
  const [workspaceId, setWorkspaceId] = useState('');
  const [searchText, setSearchText] = useState('');
  const [accessToken, setAccessToken] = useState(getWorkspaceAccessToken);

  const workspaces = useQuery({ queryKey: ['workspaces', accessToken], queryFn: getWorkspaces, retry: false });
  const workspace = useQuery({
    queryKey: ['workspace', workspaceId, accessToken],
    queryFn: () => getWorkspace(workspaceId),
    enabled: workspaceId.length > 0,
    retry: false,
  });

  useEffect(() => {
    if (workspaceId.length > 0) {
      return;
    }
    const firstId = workspaces.data?.items[0]?.workspace_id;
    if (firstId) {
      setWorkspaceId(firstId);
    }
  }, [workspaceId, workspaces.data]);

  const sprintAndGate = useMemo(() => {
    if (!workspace.data) {
      return { sprint: 'Loading...', gate: 'Loading...' };
    }
    return {
      sprint: workspace.data.state.current_sprint,
      gate: workspace.data.state.current_gate,
    };
  }, [workspace.data]);

  return (
    <div className="workspace-surface">
      <div className="workspace-layout">
      <SidebarNav entries={PAGE_NAV} />

      <section className="workspace-main">
        <WorkspaceHeader
          workspaceId={workspaceId}
          onWorkspaceChange={setWorkspaceId}
          searchText={searchText}
          onSearchChange={setSearchText}
          accessToken={accessToken}
          onAccessTokenChange={(token) => {
            setAccessToken(token);
            setWorkspaceAccessToken(token);
          }}
          workspaces={workspaces.data}
        />

        <StatusBar sprint={sprintAndGate.sprint} gate={sprintAndGate.gate} />

        <div className="content-grid">
          <section className="content-area">
            {workspaceId.length === 0 ? (
              <p>Loading workspace...</p>
            ) : (
              <Routes>
                <Route index element={<Navigate to="dashboard" replace />} />
                <Route path="dashboard" element={<DashboardPage workspaceId={workspaceId} />} />
                <Route path="timeline" element={<TimelinePage workspaceId={workspaceId} />} />
                <Route path="repository" element={<RepositoryPage workspaceId={workspaceId} searchText={searchText} />} />
                <Route path="roadmap" element={<SearchBackedPage workspaceId={workspaceId} title="Roadmap" query="ROADMAP" />} />
                <Route path="reviews" element={<SearchBackedPage workspaceId={workspaceId} title="Reviews" query="REVIEW" />} />
                <Route path="prompts" element={<SearchBackedPage workspaceId={workspaceId} title="Prompts" query="PROMPT" />} />
                <Route path="architecture" element={<SearchBackedPage workspaceId={workspaceId} title="Architecture" query="architecture" />} />
                <Route path="health" element={<HealthPage workspaceId={workspaceId} />} />
              </Routes>
            )}
          </section>

          <ObserverPanel workspace={workspace.data} isLoading={workspace.isLoading} isError={workspace.isError} />
        </div>
      </section>
      </div>
    </div>
  );
}
