// Optional local static preview: node design/serve.mjs
import http from 'node:http';
import { readFile } from 'node:fs/promises';
const page = new URL('./concept.html', import.meta.url);
const server = http.createServer(async (req, res) => {
  if (req.url !== '/' && req.url !== '/concept.html') {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
    return;
  }
  try {
    const html = await readFile(page);
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(html);
  } catch {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Preview file unavailable');
  }
});
server.listen(4178, '127.0.0.1', () => console.log('Local: http://127.0.0.1:4178'));
