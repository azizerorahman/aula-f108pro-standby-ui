"""Browser regression checks for the public offline preview; no device access."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
errors=[];network=[];checks=0
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--disable-gpu','--renderer-process-limit=2'])
 page=browser.new_page(viewport={'width':1280,'height':950},reduced_motion='reduce')
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:network.append(r.url) if r.url.startswith(('https:','http:')) else None)
 page.goto((ROOT/'docs/index.html').as_uri())
 page.wait_for_function("document.querySelector('#screen').complete && document.querySelector('#screen').naturalWidth===240")
 for locale in ['en','cn']:
  page.select_option('#locale',locale)
  for group,count in [('clock',10),('menu',8),('connect',5),('system',4),('effect',20),('colour',9),('brightness',6),('speed',6),('volume',3),('language',2),('status',10),('boot',20)]:
   page.click(f'#tabs button[data-group="{group}"]')
   seen=[]
   for i in range(count):
    seen.append(page.locator('#screen').get_attribute('data-id'))
    assert page.locator('#screen').evaluate('(im)=>im.complete && im.naturalWidth===240')
    page.click('#next');checks+=1
   assert len(set(seen))==count,(group,locale,seen)
   assert page.locator('#screen').get_attribute('data-id')==seen[0]
 page.click('#home');page.click('#press');assert page.locator('#screen').get_attribute('data-id')=='menu_0';checks+=1
 page.click('#press');assert page.locator('#screen').get_attribute('data-id')=='connect_0';checks+=1
 page.click('#back');assert page.locator('#screen').get_attribute('data-id')=='menu_0';checks+=1
 page.click('#tabs button[data-group="effect"]');page.click('#previous');assert page.locator('#screen').get_attribute('data-id')=='effect_cn_19';checks+=1
 page.select_option('#locale','en');page.select_option('#filter','effect');assert page.locator('#gallery figure').count()==20;checks+=1
 page.check('#native');assert page.locator('#device').evaluate('(e)=>e.getBoundingClientRect().width')==264;checks+=1
 page.uncheck('#native');page.click('#home')
 page.screenshot(path=str(ROOT/'build/preview-desktop.png'),full_page=False)
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');checks+=1
 page.screenshot(path=str(ROOT/'build/preview-mobile.png'),full_page=False)
 assert not errors,errors
 assert not network,network
 browser.close()
print(json.dumps({'browser_checks':checks,'javascript_errors':len(errors),'external_requests':len(network),'device_opened':False}))
