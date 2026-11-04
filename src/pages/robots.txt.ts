import site from '../../site.config.json';
export function GET() {
  return new Response(`User-agent: *\nAllow: /\nDisallow: /search/\n\nSitemap: ${site.url}/sitemap-index.xml\n`, { headers: { 'Content-Type': 'text/plain' } });
}
