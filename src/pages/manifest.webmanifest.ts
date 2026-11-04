import site from '../../site.config.json';
export function GET() {
  return new Response(JSON.stringify({ name: site.name, short_name: site.name, description: site.tagline, start_url: '/', display: 'standalone', background_color: '#F4F5F9', theme_color: '#2F3BBF', icons: [{ src: '/icon-192.png', sizes: '192x192', type: 'image/png' }, { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }] }), { headers: { 'Content-Type': 'application/manifest+json' } });
}
