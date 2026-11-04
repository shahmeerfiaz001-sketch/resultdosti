import rss from '@astrojs/rss';
import site from '../../site.config.json';
import { live, itemPath, displayTitle, TYPES, fmt } from '../lib/data';

export function GET() {
  const items = live().slice(0, 60);
  return rss({
    title: `${site.name}: Sarkari Result, Latest Jobs, Admit Card`,
    description: site.tagline,
    site: site.url,
    items: items.map((i) => ({
      title: displayTitle(i),
      link: itemPath(i),
      pubDate: new Date(i.first_seen),
      description: `${TYPES[i.type].short} by ${i.org}. Published ${fmt(i.list_date || i.first_seen)}.`
    })),
    customData: '<language>en-in</language>'
  });
}
