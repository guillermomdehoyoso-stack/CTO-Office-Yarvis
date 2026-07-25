import { useQuery } from '@tanstack/react-query';
import { getTimeline } from '../../api/workspacePlatform';

export function TimelinePage({ workspaceId }: { workspaceId: string }) {
  const timeline = useQuery({ queryKey: ['timeline', workspaceId], queryFn: () => getTimeline(workspaceId), retry: false });

  if (timeline.isLoading) return <p>Loading timeline...</p>;
  if (timeline.error || !timeline.data) return <p>Timeline unavailable.</p>;

  return (
    <section>
      <h1>Timeline</h1>
      <p>{timeline.data.current_sprint}</p>
      <div className="list-panel">
        {timeline.data.events.slice(0, 30).map((event) => (
          <div className="list-row" key={`${event.path}-${event.modified_at}`}>
            <span>{event.path}</span>
            <span>{new Date(event.modified_at).toLocaleString()}</span>
            <span>{event.kind}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
