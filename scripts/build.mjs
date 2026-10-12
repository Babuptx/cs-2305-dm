import {mkdir, cp, readFile, writeFile, readdir, realpath, lstat, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=await realpath(fileURLToPath(new URL('../',import.meta.url)));
const output=resolve(root,'dist');
// Clean only this repository's build directory; never follow a redirected dist.
if(dirname(output)!==root)throw Error('Build output must be inside the repository.');
const existing=await lstat(output).catch(error=>{if(error.code!=='ENOENT')throw error;});
if(existing?.isSymbolicLink())throw Error('Refusing to replace a linked build directory.');

// A shared content hash puts the stylesheet and every imported module in one
// immutable URL namespace. Cached modules from earlier releases cannot mix in.
const hash=createHash('sha256');
const modules=(await readdir(resolve(root,'js'),{recursive:true})).filter(p=>p.endsWith('.js')).sort();
for(const file of ['styles.css',...modules.map(p=>`js/${p.replaceAll('\\','/')}`)]){
  hash.update(file).update('\0').update(await readFile(resolve(root,file))).update('\0');
}
const assetPath=`assets/${hash.digest('hex').slice(0,16)}`;
let html=await readFile(resolve(root,'index.html'),'utf8');
if(!html.includes('href="styles.css"')||!html.includes('src="js/app.js"'))throw Error('Missing build asset entry points.');
html=html.replace('href="styles.css"',`href="${assetPath}/styles.css"`)
  .replace('src="js/app.js"',`src="${assetPath}/js/app.js"`);

await rm(output,{recursive:true,force:true});
await mkdir(resolve(output,assetPath),{recursive:true});
await cp(resolve(root,'styles.css'),resolve(output,assetPath,'styles.css'));
await cp(resolve(root,'js'),resolve(output,assetPath,'js'),{recursive:true});
await cp(resolve(root,'data'),resolve(output,'data'),{recursive:true});
await writeFile(resolve(output,'index.html'),html);
console.log(`Static site prepared in dist/ with versioned assets: ${assetPath}`);
