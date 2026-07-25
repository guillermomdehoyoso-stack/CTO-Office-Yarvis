import { useQuery } from '@tanstack/react-query';
import { getRepository, searchRepository } from '../../api/workspacePlatform';
import { MetricCard } from '../MetricCard';

export function RepositoryPage({ workspaceId, searchText }: { workspaceId: string; searchText: string }) {
  const repository = useQuery({ queryKey: ['repository', workspaceId], queryFn: () => getRepository(workspaceId), retry: false });
  const search = useQuery({
    queryKey: ['repository-search', workspaceId, searchText],
    queryFn: () => searchRepository(workspaceId, searchText),
    enabled: searchText.trim().length > 0,
    retry: false,
  });

  if (repository.isLoading) return <p>Loading repository health...</p>;
  if (repository.error || !repository.data) return <p>Repository health unavailable.</p>;

  const extensionRows = Object.entries(repository.data.health.by_extension)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15);

  return (
    <section>
      <h1>Repository</h1>
      <div className="metrics-grid">
        <MetricCard metric="Total Files" value={repository.data.health.total_files} />
        <MetricCard metric="Reference Nodes" value={repository.data.document_reference_graph.node_count} />
        <MetricCard metric="Reference Edges" value={repository.data.document_reference_graph.edge_count} />
        <MetricCard metric="Authority Mode" value={repository.data.health.read_only_authority} />
      </div>
      <h2>Top Extensions</h2>
      <div className="list-panel compact">
        {extensionRows.map(([extension, count]) => (
          <div className="list-row" key={extension}>
            <span>{extension}</span>
            <span>{count}</span>
          </div>
        ))}
      </div>
      {searchText.trim().length > 0 && (
        <>
          <h2>Search Results</h2>
          {search.isLoading && <p>Searching repository...</p>}
          {search.error && <p>Repository search unavailable.</p>}
          {search.data && (
            <div className="list-panel">
              {search.data.results.map((result) => (
                <div className="search-row" key={result.path + String(result.score)}>
                  <h3>{result.path}</h3>
                  <p>{result.snippet || 'Path match.'}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
