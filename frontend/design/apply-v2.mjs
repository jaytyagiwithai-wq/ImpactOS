// Rebuild the standalone concept from the revised homepage and styles.
import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
const base = new URL('./', import.meta.url);
let html = await readFile(new URL('concept.html', base), 'utf8');
await mkdir(new URL('archive/', base), { recursive: true });
if (!html.includes('REVISED_DESIGN_START')) await copyFile(new URL('concept.html', base), new URL('archive/concept-v1.html', base));
const fonts = [['DM Sans',400,'dm-sans-regular.ttf'],['DM Sans',500,'dm-sans-medium.ttf'],['DM Sans',600,'dm-sans-semibold.ttf'],['IBM Plex Mono',400,'ibm-plex-mono.ttf']];
let fontCss = '';
for (const [name, weight, file] of fonts) {
  const data = await readFile(new URL(`fonts/${file}`, base));
  fontCss += `@font-face{font-family:'${name}';font-style:normal;font-weight:${weight};font-display:swap;src:url(data:font/ttf;base64,${data.toString('base64')}) format('truetype')}\n`;
}
const css = await readFile(new URL('v2.css', base), 'utf8');
html = html.replace(/\/\* REVISED_DESIGN_START \*\/[\s\S]*?\/\* REVISED_DESIGN_END \*\//, '');
html = html.replace('</style>', `/* REVISED_DESIGN_START */\n${fontCss}\n${css}\n/* REVISED_DESIGN_END */\n</style>`);
const template = await readFile(new URL('home-v2.template', base), 'utf8');
const start = html.includes('function heroStage()') ? html.indexOf('function heroStage()') : html.indexOf('function home()');
html = html.slice(0, start) + template + '\n' + html.slice(html.indexOf('function side(route)', start));
if (!html.includes("let heroStep=")) html = html.replace("let selected=0, activeTab='findings';", "let selected=0, activeTab='findings';\nlet heroStep='report';");
if (!html.includes('data-hero-step handler')) {
  html = html.replace("document.addEventListener('click',e=>{const f=", `document.addEventListener('click',e=>{\n// data-hero-step handler\nconst skip=e.target.closest('.skip');if(skip){e.preventDefault();const m=document.getElementById('main');m.setAttribute('tabindex','-1');m.focus();m.scrollIntoView();return}\nconst h=e.target.closest('[data-hero-step]');if(h){heroStep=h.dataset.heroStep;document.getElementById('hero-stage-content').innerHTML=heroStage();document.querySelectorAll('[data-hero-step]').forEach(b=>{b.classList.toggle('active',b===h);b.setAttribute('aria-pressed',String(b===h))});return}\nconst motion=e.target.closest('[data-motion]');if(motion){const paused=document.body.classList.toggle('motion-paused');motion.textContent=paused?'▶ Play motion':'Ⅱ Pause motion';motion.setAttribute('aria-pressed',String(paused));return}\nconst f=`);
}
html=html.replace('const route=location.hash.slice(1)', "heroStep='report';const route=location.hash.slice(1)");
await writeFile(new URL('concept.html', base), html);
console.log('Revised concept written with embedded local fonts.');
