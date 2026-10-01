/* German source keys; English is bundled locally. No external translation service. */
const [labels, messages] = await Promise.all(['strings.en.json','messages.en.json'].map(async file => {
  const response = await fetch(new URL(`./${file}?v=1.5.0`, import.meta.url));
  if (!response.ok) throw new Error(`Could not load translations: ${file}`);
  return response.json();
}));
export const language = value => String(value || 'en').toLowerCase().split(/[-_]/)[0] === 'de' ? 'de' : 'en';
export function translate(key, locale, values = {}) {
  const text = language(locale) === 'de' ? key : labels[key] || key;
  return text.replace(/\{(\w+)\}/g, (match, name) => Object.hasOwn(values,name) ? String(values[name]) : match);
}
const escapeRegExp = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Old stored log entries and probe results contain rendered German messages.
// Match only known messages, and never translate names, hosts or arbitrary values.
const patterns = Object.entries(messages).filter(([key]) => key.includes('{')).sort((a,b) => b[0].replace(/\{\w+\}/g,'').length-a[0].replace(/\{\w+\}/g,'').length).map(([key,value]) => {
  const names = [...key.matchAll(/\{(\w+)\}/g)].map(match=>match[1]);
  const parts = key.split(/\{\w+\}/g);
  return {pattern:new RegExp('^'+parts.map(escapeRegExp).join('([\\s\\S]*?)')+'$'),names,value};
});
export function translateMessage(text, locale, depth=0) {
  if (!text || language(locale)==='de' || depth>6) return text;
  if (Object.hasOwn(messages,text)) return messages[text];
  if (/^(Ping|Web|TCP): /.test(text) && / · (Ping|Web|TCP): /.test(text)) return text.split(/ · (?=(?:Ping|Web|TCP): )/).map(part=>translateMessage(part,locale,depth+1)).join(' · ');
  for (const {pattern,names,value} of patterns) {
    const match = text.match(pattern);
    if (!match) continue;
    const values = Object.fromEntries(names.map((name,index)=>[name,
      ['detail','error','title'].includes(name) ? translateMessage(match[index+1],locale,depth+1) : match[index+1]]));
    return value.replace(/\{(\w+)\}/g,(_,name)=>values[name]);
  }
  return text;
}
