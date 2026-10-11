import assert from 'node:assert/strict';
import {mkdir,readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}}), errors=[];
page.setDefaultTimeout(15000);
page.on('pageerror',e=>errors.push(e.message));
page.on('dialog',dialog=>dialog.accept());
const base=process.env.QUIZ_URL || 'http://127.0.0.1:8080';
await mkdir('test-results',{recursive:true});
try {
  await page.goto(base);await page.waitForFunction(()=>!document.getElementById('start').disabled);
  assert.match(await page.locator('#status').innerText(),/1000 questions/);
  assert.equal(await page.locator('#pillar option').count(),7);
  await page.locator('#start').click();await page.locator('input[name=answer]').first().waitFor();
  assert.equal(await page.locator('#navigation button').count(),50);
  assert.equal(await page.locator('#explanation').isVisible(),false);
  await page.locator('input[name=answer]').nth(0).check();
  await page.locator('input[name=answer]').nth(1).check();
  assert.equal(await page.locator('input[name=answer]').nth(1).isChecked(),true);
  assert.equal(await page.evaluate(()=>document.activeElement.name),'answer');
  await page.locator('#flag').click();assert.equal(await page.locator('#flag').getAttribute('aria-pressed'),'true');
  await page.locator('#flag').click();assert.equal(await page.locator('#flag').getAttribute('aria-pressed'),'false');
  await page.locator('#hint').click();assert.equal(await page.locator('#hints li').count(),1);
  await page.locator('#reveal').click();assert.equal(await page.locator('#explanation').isVisible(),true);
  assert.equal(await page.locator('input[name=answer]:disabled').count(),4);
  await page.screenshot({path:'test-results/desktop.png',fullPage:true});
  await page.locator('#next').click();assert.equal(await page.locator('#explanation').isVisible(),false);
  await page.locator('#shuffle').click();assert.match(await page.locator('#answered').innerText(),/1 \/ 50/);
  await page.locator('#finish').click();assert.match(await page.locator('#result').innerText(),/49 unanswered/);
  assert.equal(await page.locator('#explanation').isVisible(),true);
  const saved=JSON.parse(await page.evaluate(()=>localStorage.getItem('dm:stats:v1')));assert.equal(saved.completedAttempts,1);
  await page.reload();await page.locator('#resume').waitFor();await page.locator('#resume').click();await page.waitForFunction(()=>!document.getElementById('result').hidden);
  assert.equal(JSON.parse(await page.evaluate(()=>localStorage.getItem('dm:stats:v1'))).completedAttempts,1);
  await page.locator('#theme').click();const theme=await page.locator('html').getAttribute('data-theme');await page.reload();await page.waitForFunction(()=>!document.getElementById('start').disabled);assert.equal(await page.locator('html').getAttribute('data-theme'),theme);
  await page.locator('#mode').selectOption('exam');await page.locator('#duration').selectOption('1800');await page.locator('#start').click();await page.locator('input[name=answer]').first().waitFor();
  assert.equal(await page.locator('#reveal').isVisible(),false);assert.equal(await page.locator('#hint').isDisabled(),true);assert.equal(await page.locator('#explanation').isVisible(),false);
  // Force the browser's saved deadline to an expired time, then exercise real
  // recovery/expiry instead of waiting thirty minutes for the UI duration.
  await page.evaluate(()=>{const s=JSON.parse(localStorage.getItem('dm:session:v1'));s.state.deadline=s.state.started;localStorage.setItem('dm:session:v1',JSON.stringify(s));});
  await page.reload();await page.locator('#resume').waitFor();await page.locator('#resume').click();await page.waitForFunction(()=>!document.getElementById('result').hidden);
  assert.equal(JSON.parse(await page.evaluate(()=>localStorage.getItem('dm:stats:v1'))).completedAttempts,2);
  await page.locator('#pillar').selectOption('counting');await page.locator('#mode').selectOption('study');await page.locator('#duration').selectOption('0');await page.locator('#start').click();await page.waitForFunction(()=>document.getElementById('block-title').textContent.includes('Counting'));
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile horizontal overflow');
  await page.locator('input[name=answer]').first().check();await page.screenshot({path:'test-results/mobile.png',fullPage:true});
  await page.locator('#reference').click();assert.equal(await page.locator('#reference-dialog').isVisible(),true);await page.keyboard.press('Escape');assert.equal(await page.locator('#reference-dialog').isVisible(),false);
  // Select and fetch all blocks through the actual manifest-driven UI.
  const manifest=JSON.parse(await readFile('data/manifest.json','utf8'));
  for(const pillar of manifest.pillars){
    await page.locator('#pillar').selectOption(pillar.id);
    for(const b of pillar.blocks){
      await page.locator('#block').selectOption(b.path);await page.locator('#start').click();
      await page.waitForFunction(id=>JSON.parse(localStorage.getItem('dm:session:v1')).blockId===id,b.id);
      assert.equal(await page.locator('#navigation button').count(),50);
      if(pillar.id==='utd-fall-midterm'){
        assert.equal(await page.locator('#choices input').count(),4);
        await page.locator('#navigation button').last().click();await page.locator('#reveal').click();
        assert.match(await page.locator('#explanation').innerText(),/Related study: Rosen/);
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Midterm mobile horizontal overflow');
      }
    }
  }
  await page.locator('#duration').selectOption('5400');
  await page.locator('#block').selectOption('data/utd-fall-midterm/block-07.json');
  await page.locator('#start').click();
  await page.waitForFunction(()=>document.getElementById('block-title').textContent.includes('Growth rates'));
  assert.match(await page.locator('#timer').innerText(),/89:|90:/);
  await page.screenshot({path:'test-results/midterm-mobile.png',fullPage:true});
  for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
    await page.setViewportSize(viewport);
    await page.locator('#reference').click();
    assert.equal(await page.locator('#reference-scope').inputValue(),'midterm');
    assert.equal(await page.locator('#reference-general').isVisible(),false);
    assert.equal(await page.locator('#reference-midterm').isVisible(),true);
    assert.ok(await page.locator('#reference-scroll').evaluate(e=>e.scrollHeight>e.clientHeight),'Reference must scroll');
    assert.ok(await page.locator('#reference-scroll').evaluate(e=>e.scrollWidth<=e.clientWidth),'Reference horizontal overflow');
    await page.screenshot({path:`test-results/reference-${viewport.width}.png`});
    await page.locator('.reference-jumps a[href="#ref-primes"]').click();
    assert.ok(await page.locator('#reference-scroll').evaluate(e=>e.scrollTop>0));
    const primeBox=await page.locator('#ref-primes h3').boundingBox();
    assert.ok(primeBox.y>0&&primeBox.y<viewport.height,'Reference jump remains inside viewport');
    assert.match(await page.locator('#ref-primes').innerText(),/0 and 1 are neither prime nor composite/);
    await page.locator('#reference-scope').selectOption('general');
    assert.equal(await page.locator('#reference-general').isVisible(),true);
    assert.match(await page.locator('#reference-general').innerText(),/Induction/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#reference-dialog').isVisible(),false);
    assert.equal(await page.evaluate(()=>document.activeElement.id),'reference');
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:'test-results/midterm-desktop.png',fullPage:true});
  await page.locator('#reset').click();await page.waitForFunction(()=>!document.getElementById('start').disabled);assert.equal(await page.evaluate(()=>localStorage.getItem('dm:stats:v1')),null);assert.equal(await page.evaluate(()=>localStorage.getItem('dm:session:v1')),null);
  await page.route('**/data/logic/block-01.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{"questions":[]}'}));await page.locator('#start').click();await page.waitForFunction(()=>document.getElementById('status').classList.contains('error'));assert.equal(await page.locator('#choices input').count(),0);await page.unroute('**/data/logic/block-01.json');
  await page.route('**/data/logic/block-01.json',route=>route.fulfill({status:404,body:'missing'}));await page.locator('#start').click();await page.waitForFunction(()=>document.getElementById('status').textContent.includes('404'));assert.equal(await page.locator('#finish').isDisabled(),true);
  assert.deepEqual(errors,[]);console.log('Browser checks passed: study/exam, all 20 blocks, 90-minute timer, persistence/reset, desktop/mobile references, source notes, malformed data and fetch errors.');
} catch (e) {console.error('Browser failure:',e.message,'Page errors:',errors,'Status:',await page.locator('#status').textContent().catch(()=>'(unavailable)'));await page.screenshot({path:'test-results/failure.png',fullPage:true}).catch(()=>{});throw e;} finally {await browser.close();}
