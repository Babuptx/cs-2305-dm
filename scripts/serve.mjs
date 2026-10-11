import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve, extname} from 'node:path';
const root = resolve('.'), port = Number(process.env.PORT || 8080);
const types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml'};
http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(root + '/') && !file.startsWith(root + '\\')) { res.writeHead(403); return res.end(); }
    if (!types[extname(file)]) { res.writeHead(404); return res.end('Not found'); }
    const data = await readFile(file); res.writeHead(200, {'Content-Type': types[extname(file)] + '; charset=utf-8', 'Cache-Control': 'no-store'}); res.end(data);
  } catch { res.writeHead(404); res.end('Not found'); }
}).listen(port, '127.0.0.1', () => console.log(`Quiz available at http://127.0.0.1:${port}`));
