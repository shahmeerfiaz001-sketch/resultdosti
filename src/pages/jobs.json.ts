import { fresh as live, itemPath, displayTitle, fieldsOf, istToday } from '../lib/data';

export function GET() {
  const jobs = live()
    .filter((i) => i.type === 'job' && (i.status === 'open' || (i.status !== 'closed' && (Date.parse(istToday()) - Date.parse(i.list_date || i.first_seen.slice(0, 10))) / 86400000 <= 30)))
    .slice(0, 600)
    .map((i) => {
      const f = fieldsOf(i);
      return { t: displayTitle(i), u: itemPath(i), s: i.scope, o: i.short, l: i.last_date || null, a: f.age ? [f.age.min ?? null, f.age.max ?? null] : null, p: f.posts ? f.posts.value : null, d: i.list_date || i.first_seen.slice(0, 10) };
    });
  return new Response(JSON.stringify(jobs), { headers: { 'Content-Type': 'application/json' } });
}
