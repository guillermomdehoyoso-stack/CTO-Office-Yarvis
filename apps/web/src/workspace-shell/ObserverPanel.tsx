import type { WorkspaceDetailResponse } from '../types/workspacePlatform';

export function ObserverPanel({
  workspace,
  isLoading,
  isError,
}: {
  workspace: WorkspaceDetailResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  return (
    <aside className="ai-panel">
      <h2>Engineering Observer</h2>
      {isLoading && <p>Analyzing workspace...</p>}
      {isError && <p>Observer unavailable.</p>}
      {workspace && (
        <>
          <h3>Observations</h3>
          <ul>
            {workspace.observer.observations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3>Recommendations</h3>
          <ul>
            {workspace.observer.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3>Blockers</h3>
          {workspace.observer.blockers.length === 0 ? (
            <p>No blockers detected.</p>
          ) : (
            <ul>
              {workspace.observer.blockers.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
          <p className="next-action">Next Action: {workspace.observer.next_action}</p>
        </>
      )}
    </aside>
  );
}
