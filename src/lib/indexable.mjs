export const INDEX_DAYS = 120;

export function ageDays(item, todayIso) {
  const d = item.list_date || item.first_seen.slice(0, 10);
  return Math.round((Date.parse(todayIso) - Date.parse(d.slice(0, 10))) / 86400000);
}

export function hubCounts(exams, liveIds) {
  const m = new Map();
  for (const e of exams) {
    const n = e.items.filter((x) => liveIds.has(x)).length;
    m.set(e.key, n);
  }
  return m;
}

export function indexable(item, todayIso, hubs) {
  if (!item.tier || item.tier < 1) return false;
  const inHub = (hubs.get(item.group) || 0) >= 2;
  if (item.type === 'job') return item.tier >= 2 || ageDays(item, todayIso) <= INDEX_DAYS || inHub;
  if (item.type === 'notice') return inHub && ageDays(item, todayIso) <= INDEX_DAYS;
  return ageDays(item, todayIso) <= INDEX_DAYS || inHub;
}

export function istTodayIso() {
  return new Date(Date.now() + 5.5 * 3600 * 1000).toISOString().slice(0, 10);
}
