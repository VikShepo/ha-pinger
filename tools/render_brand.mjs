// Render our vector artwork as HA integration and app PNG assets.
import {chromium} from '../.test-output/tools/node_modules/playwright/index.mjs';
import {readFile,mkdir,copyFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const svg=await readFile(resolve(root,'custom_components/ha_pinger/frontend/brand.svg'),'utf8');
const directory=resolve(root,'custom_components/ha_pinger/brand');
await mkdir(directory,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.PINGER_CHROME||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'});
try{
  const page=await browser.newPage();
  for(const size of [256,512]){
    await page.setViewportSize({width:size,height:size});
    await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:100vw;height:100vh}</style>${svg}`);
    await page.screenshot({path:resolve(directory,size===256?'icon.png':'icon@2x.png'),omitBackground:true});
  }
  await copyFile(resolve(directory,'icon.png'),resolve(root,'addons/ncc_vpn/icon.png'));
  await copyFile(resolve(directory,'icon@2x.png'),resolve(root,'addons/ncc_vpn/logo.png'));
}finally{await browser.close();}
console.log('Rendered integration/app brand icons at 256 and 512 pixels.');
