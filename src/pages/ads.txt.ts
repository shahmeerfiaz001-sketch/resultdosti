import ads from '../data/ads.json';
export function GET() {
  const pub = ads.adsenseClient ? ads.adsenseClient.replace(/^ca-/, '') : '';
  const body = ads.adsTxt || (pub ? `google.com, ${pub}, DIRECT, f08c47fec0942fa0\n` : '');
  return new Response(body, { headers: { 'Content-Type': 'text/plain' } });
}
