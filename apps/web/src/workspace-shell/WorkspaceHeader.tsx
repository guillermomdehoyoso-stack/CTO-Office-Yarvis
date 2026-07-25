import type { WorkspacesResponse } from '../types/workspacePlatform';

export function WorkspaceHeader({
  workspaceId,
  onWorkspaceChange,
  searchText,
  onSearchChange,
  accessToken,
  onAccessTokenChange,
  workspaces,
}: {
  workspaceId: string;
  onWorkspaceChange: (value: string) => void;
  searchText: string;
  onSearchChange: (value: string) => void;
  accessToken: string;
  onAccessTokenChange: (value: string) => void;
  workspaces: WorkspacesResponse | undefined;
}) {
  return (
    <header className="workspace-header">
      <div>
        <label htmlFor="workspace-selector">Workspace</label>
        <select
          id="workspace-selector"
          value={workspaceId}
          onChange={(event) => onWorkspaceChange(event.target.value)}
        >
          {(workspaces?.items || []).map((item) => (
            <option key={item.workspace_id} value={item.workspace_id}>
              {item.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="workspace-access-token">Workspace access token</label>
        <input
          id="workspace-access-token"
          type="password"
          value={accessToken}
          onChange={(event) => onAccessTokenChange(event.target.value)}
          autoComplete="off"
        />
      </div>
      <div>
        <label htmlFor="workspace-search">Search</label>
        <input
          id="workspace-search"
          value={searchText}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search repository..."
        />
      </div>
    </header>
  );
}
