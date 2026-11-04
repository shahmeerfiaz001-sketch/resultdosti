# ResultDosti Setup

## 1. GitHub
1. GitHub par nayi **public** repository banayen: `resultdosti` (public = Actions free aur unlimited).
2. Is folder ki saari files us repo mein upload/push karen (node_modules aur dist ke baghair).
3. Repo > Settings > Actions > General > Workflow permissions: **Read and write permissions** select karen > Save.

## 2. Cloudflare Pages
1. Naya Cloudflare account > resultdosti.in add karen (nameservers registrar par lagayen).
2. Workers & Pages > Create > Pages > Connect to Git > `resultdosti` repo select.
3. Build settings:
   - Framework preset: Astro
   - Build command: `npm run build`
   - Build output directory: `dist`
4. Environment variables (Production):
   - `NODE_VERSION` = `22`
   - `GOOGLE_SITE_VERIFICATION` = Search Console ka HTML tag code (sirf content wali value)
   - `GA_ID` = Google Analytics ID (optional, e.g. G-XXXXXXX)
5. Deploy ke baad Custom domains > `resultdosti.in` aur `www.resultdosti.in` add karen.
6. Rules > Redirect Rules: `www.resultdosti.in/*` → `https://resultdosti.in/${1}` (301).
7. SSL/TLS > Edge Certificates: Always Use HTTPS = On.

## 3. Telegram
1. Telegram par @BotFather > /newbot > token copy karen.
2. Ek private group ya apni chat "alerts" ke liye: bot ko usmein add karen, phir `https://api.telegram.org/bot<TOKEN>/getUpdates` khol kar chat id note karen.
3. Public channel banayen (e.g. @resultdosti), bot ko channel ka **admin** banayen.
4. `site.config.json` mein `"telegram": "https://t.me/resultdosti"` likh den (header mein Join button aa jayega).

## 4. Google Indexing API (jobs ke liye fast indexing)
1. console.cloud.google.com > New project > "Web Search Indexing API" enable.
2. IAM > Service Accounts > Create > Keys > Add key > JSON download.
3. Search Console > resultdosti.in property > Settings > Users and permissions > service account ka email **Owner** ke taur par add karen.

## 5. GitHub Secrets
Repo > Settings > Secrets and variables > Actions > New repository secret:
| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather wala token |
| `TELEGRAM_ALERT_CHAT` | alerts chat id |
| `TELEGRAM_CHANNEL` | `@resultdosti` |
| `GOOGLE_SA_JSON` | service account JSON file ka poora text |

IndexNow key pehle se `site.config.json` aur `public/` mein maujood hai, kuch karne ki zaroorat nahi.

## 6. Pehli baar chalana
1. Actions > **Probe sources** > Run workflow. Yeh har official site check karke `data/probe/report.md` bana dega.
2. Actions > **Update data** > Run workflow. Pehli run mein saara data aayega, Telegram par post nahi hoga. Naya source baad mein add karen to uska purana data bhi post nahi hoga.
3. Uske baad har 2 ghante bot khud chalega. Koi source fail ho to Telegram alert aayega.

## 7. Search Console
1. Property add karen, verify karen.
2. Sitemaps > `https://resultdosti.in/sitemap-index.xml` submit.
3. Bing Webmaster Tools mein Search Console se import kar len.

## 8. AdSense (approval ke baad)
`src/data/ads.json` mein:
- `"enabled": true`
- `"adsenseClient": "ca-pub-XXXXXXXX"`
- har slot ka `adsenseSlot` id
`ads.txt` khud ban jayega.

## Limits
- Cloudflare Pages free: 500 builds/month. Bot sirf tab build karata hai jab koi naya update ya status change ho (zyada se zyada 12/day = 360/month).
- Purane updates (notice/admit/answer 1 saal, baqi 18 mahine) khud site se hat jate hain taa ke files ki limit (20,000) cross na ho.
- GitHub 60 din tak repo mein koi activity na ho to scheduled workflow band kar deta hai; bot ki commits activity shumar hoti hain, lekin agar kabhi band ho jaye to Actions tab mein "Enable workflow" daba den.
