import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const dist = 'dist';
const site = JSON.parse(readFileSync('site.config.json', 'utf8')).url;
let kept = 0;
let removed = 0;
for (const f of readdirSync(dist).filter((n) => /^sitemap-\d+\.xml$/.test(n))) {
  const xml = readFileSync(join(dist, f), 'utf8');
  const out = xml.replace(/<url>([\s\S]*?)<\/url>/g, (block, inner) => {
    const loc = (inner.match(/<loc>(.*?)<\/loc>/) || [])[1] || '';
    const path = loc.replace(site, '');
    const file = join(dist, path, 'index.html');
    if (existsSync(file)) {
      const head = readFileSync(file, 'utf8').split('</head>')[0];
      if (/name="robots" content="noindex/.test(head)) {
        removed++;
        return '';
      }
    }
    kept++;
    return block;
  });
  writeFileSync(join(dist, f), out);
}
console.log(`sitemap: kept ${kept}, removed ${removed}`);
