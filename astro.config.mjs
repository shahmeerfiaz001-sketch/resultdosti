import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readFileSync, existsSync } from 'node:fs';
import { indexable, hubCounts, istTodayIso, ageDays } from './src/lib/indexable.mjs';

const site = JSON.parse(readFileSync('./site.config.json', 'utf8'));
const noindex = new Set();
if (existsSync('./data/items.json')) {
  const db = JSON.parse(readFileSync('./data/items.json', 'utf8'));
  const ex = existsSync('./data/exams.json') ? JSON.parse(readFileSync('./data/exams.json', 'utf8')).exams || [] : [];
  const today = istTodayIso();
  const liveIds = new Set((db.items || []).filter((i) => i.tier >= 1 && ageDays(i, today) <= (['notice', 'admit', 'answer'].includes(i.type) ? 365 : 548)).map((i) => i.id));
  const hubs = hubCounts(ex, liveIds);
  for (const it of db.items || []) if (!indexable(it, today, hubs)) noindex.add(`/${site.paths[it.type]}/${it.slug}/`);
}

export default defineConfig({
  site: site.url,
  trailingSlash: 'always',
  build: { format: 'directory' },
  compressHTML: true,
  integrations: [
    sitemap({
      filter: (page) => {
        const p = new URL(page).pathname;
        return !p.startsWith('/search') && !p.startsWith('/404') && !noindex.has(p);
      },
      changefreq: 'hourly',
      entryLimit: 5000
    })
  ]
});
