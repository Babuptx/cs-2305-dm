import assert from 'node:assert/strict';
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
import {chromium} from 'playwright';

const root=resolve('dist');
const published=await readFile(resolve(root,'index.html'),'utf8');
const version=published.match(/href="(assets\/[a-f0-9]{16})\/styles.css"/)?.[1];
assert.ok(version,'Built CSS must have a content-versioned URL');
assert.ok(published.includes(`src="${version}/js/app.js"`));
const legacy={
  '/styles.css':['text/css','h1{font-size:64px}'],
  '/js/app.js':['text/javascript',"import './reference.js';window.legacyLoaded=true;"],
  '/js/reference.js':['text/javascript',"document.getElementById('reference-scope').addEventListener('change',()=>{});"],
};
let upgraded=false;
const server=http.createServer(async(req,res)=>{
  const pathname=new URL(req.url,'http://localhost').pathname;
  if(pathname==='/'){
    res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'});
    return res.end(upgraded?published:'<!doctype html><link rel="stylesheet" href="styles.css"><select id="reference-scope"></select><script type="module" src="js/app.js"></script>');
  }
  if(legacy[pathname]){
    res.writeHead(200,{'Content-Type':legacy[pathname][0],'Cache-Control':'public,max-age=86400'});
    return res.end(legacy[pathname][1]);
  }
  try{
    const file=resolve(root,'.'+pathname);
    if(!file.startsWith(root+sep))throw Error('Invalid path');
    const data=await readFile(file);
    const type={'.css':'text/css','.js':'text/javascript','.json':'application/json'}[extname(file)];
    res.writeHead(200,{'Content-Type':type||'application/octet-stream'});res.end(data);
  }catch{res.writeHead(404);res.end('Not found');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  const errors=[],assets=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(upgraded&&/\.(?:js|css)$/.test(new URL(request.url()).pathname))assets.push(new URL(request.url()).pathname);});
  const base=`http://127.0.0.1:${server.address().port}/`;
  // Seed a real browser cache with the retired stylesheet and dropdown module.
  await page.goto(base);await page.waitForFunction(()=>window.legacyLoaded===true);
  upgraded=true;
  await page.goto(base+'?updated');
  await page.waitForFunction(()=>!document.getElementById('start').disabled);
  assert.equal(await page.locator('#pillar option').count(),7);
  assert.equal(await page.locator('header .brand').innerText(),'Discrete Mathematics Quiz');
  await page.locator('button[data-reading-size="large"]').click();
  assert.equal(await page.locator('#context').evaluate(e=>getComputedStyle(e).fontSize),'21px');
  await page.locator('#reference').click();
  assert.equal(await page.locator('#reference-dialog select').count(),0);
  assert.equal(await page.locator('#reference-general').isVisible(),true);
  assert.equal(await page.locator('#reference-midterm').isVisible(),true);
  assert.ok(assets.length>=5,'Stylesheet and all four JS modules must load');
  assert.ok(assets.every(path=>path.startsWith('/'+version+'/')),JSON.stringify(assets));
  assert.deepEqual(errors,[]);
  console.log('Deployment regression passed: a browser with cached retired assets loads all 7 pillars, working reading controls, and the unified reference.');
}finally{
  await browser?.close();
  await new Promise(resolve=>server.close(resolve));
}
