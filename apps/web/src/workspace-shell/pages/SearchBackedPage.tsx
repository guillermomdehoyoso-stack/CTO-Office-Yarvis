import { useQuery } from '@tanstack/react-query';
import { searchRepository } from '../../api/workspacePlatform';

export function SearchBackedPage({ workspaceId, title, query }: { workspaceId: string; title: string; query: string }) {
  const search = useQuery({ queryKey: ['search-page', workspaceId, query], queryFn: () => searchRepository(workspaceId, query), retry: false });

  if (search.isLoading) return <p>Loading {title.toLowerCase()}...</p>;
  if (search.error || !search.data) return <p>{title} unavailable.</p>;

  return (
    <section>
      <h1>{title}</h1>
      <div className="list-panel">
        {search.data.results.slice(0, 20).map((result) => (
          <div className="search-row" key={result.path + title}>
            <h3>{result.path}</h3>
            <p>{result.snippet || 'Path match.'}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
