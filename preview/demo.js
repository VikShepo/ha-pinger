// Isolated, explicitly labelled UI fixture. Never loaded by the integration.
import '../custom_components/ha_pinger/frontend/ha-pinger.js';

const now = Date.now()/1000;
const seed = [
  ['192.168.0.1','Puli WAN'],['192.168.0.2','Speedport WAN'],['192.168.1.1','Gateway'],
  ['192.168.1.2','Puli'],['192.168.1.3','Speedport'],['192.168.1.4','Repeater'],
  ['192.168.1.5','LAN-Switch'],['192.168.1.6','Powerline Main'],
  ['192.168.1.7','Powerline Lager'],['192.168.1.8','Powerline Büro'],
];
const data = {
  available:true,
  settings:{interval_minutes:5,offline_after_seconds:300,timeout_seconds:2,attempts:2,notify_service:'notify.mobile_app_demo_phone',sort_by:'manual',sort_desc:false},
  active_network:'',networks:[],vpn:{agent_url:'http://local-ncc-vpn:8099',token_set:false},
  notify_services:['notify.mobile_app_demo_phone'],
  groups:[{id:'wan',name:'Internet & WAN',icon:'globe'},{id:'lan',name:'Heimnetz',icon:'router'},{id:'power',name:'Powerline',icon:'wifi'}],
  targets:seed.map(([host,name],i)=>createTarget({id:`demo-${i}`,host,name,group_id:i<2?'wan':i<7?'lan':'power',method:i<5?'both':'icmp',favorite:[0,2,4].includes(i),notify:[0,2,4,8].includes(i)},i===8?'offline':'online',i)),
  events:[
    {time:now-720,kind:'online',name:'Repeater',message:'Wieder erreichbar'},
    {time:now-620,kind:'online',name:'Speedport WAN',message:'Wieder erreichbar'},
    {time:now-350,kind:'offline',name:'Powerline Lager',message:'Keine Antwort'},
    {time:now-40,kind:'push',name:'Powerline Lager',message:'Ausfallmeldung gesendet'},
  ],
};
// The normal preview matches a fresh installation. Populated fixtures are
// explicitly enabled only by browser tests and never ship in the ZIP.
if(!new URLSearchParams(location.search).has('fixtures')) {
  data.targets=[]; data.groups=[]; data.events=[];
  data.settings.notify_service=''; data.notify_services=[];
}

function createTarget(target,status='unknown',i=0) {
  const checks=status==='unknown'?{}:{ping:{online:status==='online'&&i!==1,latency_ms:1.2,detail:i===1?'Keine ICMP-Antwort; der Webdienst antwortet trotzdem.':status==='online'?'Erreichbar':'Keine ICMP-Antwort.'},...(['web','both'].includes(target.method)?{web:{online:true,latency_ms:18,http_status:200,url:`http://${target.host}/`,detail:'Webdienst antwortet mit HTTP 200.'}}:{})};
  return {kind:'ip',method:'icmp',port:443,interval_minutes:0,enabled:true,favorite:false,group_id:'',network_id:'',icon:'auto',image_id:'',notification_status:'Bereit für Ausfallmeldungen',
    web_scheme:'http',web_port:80,web_path:'/',verify_tls:true,availability_mode:'any',checks,
    notify:false,notify_recovery:true,notify_dns:false,status,checking:false,
    online:status==='online',latency_ms:status==='online'?0.8+i*.6:null,
    last_checked:status==='unknown'?null:now-15,last_online:now-(status==='offline'?350:15),
    next_check:now+285,offline_since:status==='offline'?now-350:null,error:null,notification_error:null,
    resolved_ips:status==='unknown'?[]:[target.host],
    history:status==='unknown'?[]:Array.from({length:48},(_,j)=>({time:now-(48-j)*300,online:!(status==='offline'&&j>45)})),
    availability:status==='offline'?95.8:100,...target};
}
const subscribers = new Set();
const handlers = new Map();
const emit=()=>subscribers.forEach(callback=>callback(structuredClone(data)));
const commands=[];
const images=new Map(),logs=new Map();
const hass={
  themes:{darkMode:new URLSearchParams(location.search).get('theme')==='dark'},
  user:{is_admin:!new URLSearchParams(location.search).has('readonly')},
  connection:{
    addEventListener:(type,handler)=>{const listeners=handlers.get(type)||new Set();listeners.add(handler);handlers.set(type,listeners);},
    removeEventListener:(type,handler)=>handlers.get(type)?.delete(handler),
    subscribeMessage:async(callback)=>{subscribers.add(callback);callback(structuredClone(data));return()=>subscribers.delete(callback);},
  },
  callWS:async(message)=>{
    if(message.type==='ha_pinger/get')return structuredClone(data);
    if(message.type==='ha_pinger/image')return images.get(message.image_id)||'';
    if(message.type==='ha_pinger/history'){
      const day=Math.floor(now/86400)*86400;
      return {now,timeline:{[String(day)]:'1'.repeat(90)+'2'.repeat(8)+'1'.repeat(190)},log:logs.get(message.target_id)||[{time:now-900,kind:'offline',message:'Keine Antwort'},{time:now-300,kind:'online',message:'Wieder erreichbar'}]};
    }
    if(!hass.user.is_admin)throw new Error('Administratorrechte erforderlich.');
    commands.push(structuredClone(message));
    const target=data.targets.find(t=>t.id===message.target_id);
    if(message.action==='preview_group_range'){
      // The demo exercises IPv4 examples; the production parser also supports IPv6.
      const value=message.data.ip_range.trim();
      const ipv4=text=>{const parts=text.trim().split('.');if(parts.length!==4||parts.some(p=>!/^\d{1,3}$/.test(p)||Number(p)>255))throw new Error('Ungültiger IP-Bereich.');return parts.reduce((n,p)=>n*256+Number(p),0);};
      const format=n=>[24,16,8,0].map(shift=>(n>>>shift)&255).join('.');
      let first,last,canonical=value;
      if(value.includes('/')){const [address,prefix]=value.split('/');const bits=Number(prefix);if(!/^\d+$/.test(prefix)||bits<0||bits>32)throw new Error('Ungültiger IP-Bereich.');const size=2**(32-bits),base=Math.floor(ipv4(address)/size)*size;first=base+(bits<31?1:0);last=base+size-1-(bits<31?1:0);canonical=`${format(base)}/${bits}`;}
      else{const [start,end]=value.split('-');first=ipv4(start);last=end?ipv4(end):first;canonical=end?`${format(first)}-${format(last)}`:format(first);}
      const count=last-first+1;if(count<1||count>256)throw new Error('Ungültiger IP-Bereich: aufsteigend und höchstens 256 Adressen.');
      const members=data.targets.filter(t=>message.target_id&&t.group_id===message.target_id&&t.kind==='ip');
      const outside=members.filter(t=>{const host=ipv4(t.host);return host<first||host>last;}).map(t=>({name:t.name,host:t.host}));
      return {range:canonical,count,first:format(first),last:format(last),version:4,outside,inside_count:members.length-outside.length};
    }
    if(message.action==='settings')Object.assign(data.settings,message.data);
    else if(message.action==='save'){
      if(message.data.image_data){message.data.image_id=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(message.data.image_data))),b=>b.toString(16).padStart(2,'0')).join('');images.set(message.data.image_id,message.data.image_data);delete message.data.image_data;}
      if(target){Object.assign(target,message.data);if(!target.enabled)target.status='paused';}
      else data.targets.push(createTarget({id:crypto.randomUUID(),...message.data}));
    }else if(message.action==='preview_range'||message.action==='add_range'){
      const [first,last]=message.data.range.split('-');const prefix=first.split('.').slice(0,3).join('.');const begin=Number(first.split('.').at(-1)),end=Number((last||first).split('.').at(-1));
      if(message.action==='preview_range')return {first,last:last||first,count:end-begin+1,skipped:0};
      for(let i=begin;i<=end;i++)data.targets.push(createTarget({id:crypto.randomUUID(),...message.data,host:`${prefix}.${i}`,name:`${message.data.name} ${prefix}.${i}`}));
    }else if(message.action==='clear_log')logs.set(message.target_id,[]);
    else if(message.action==='select_network')data.active_network=message.target_id||'';
    else if(message.action==='agent_settings')Object.assign(data.vpn,{agent_url:message.data.agent_url,token_set:true});
    else if(message.action==='save_network'){
      const network=data.networks.find(n=>n.id===message.target_id);
      if(network)network.name=message.data.name;else data.networks.push({id:crypto.randomUUID(),name:message.data.name});
    }else if(message.action==='delete_network')data.networks=data.networks.filter(n=>n.id!==message.target_id);
    else if(message.action==='delete')data.targets=data.targets.filter(t=>t.id!==message.target_id);
    else if(message.action==='save_group'){
      const group=data.groups.find(g=>g.id===message.target_id);
      if(group)Object.assign(group,message.data);else data.groups.push({id:crypto.randomUUID(),...message.data});
    }else if(message.action==='delete_group'){
      data.groups=data.groups.filter(g=>g.id!==message.target_id);
      for(const t of data.targets)if(t.group_id===message.target_id)t.group_id='';
    }else if(message.action==='move'){
      const items=data[message.data.scope];
      const item=items.find(t=>t.id===message.target_id);
      const siblings=message.data.scope==='groups'?items:items.filter(t=>t.kind===item.kind&&t.group_id===item.group_id);
      const other=siblings[siblings.indexOf(item)+message.data.direction];
      if(other){const a=items.indexOf(item),b=items.indexOf(other);[items[a],items[b]]=[items[b],items[a]];}
    }
    else if(message.action==='check'){
      await new Promise(resolve=>setTimeout(resolve,120));
      for(const t of data.targets.filter(t=>t.enabled&&(!message.target_id||t.id===message.target_id))){t.last_checked=Date.now()/1000;t.next_check=t.last_checked+300;}
    }
    emit();return structuredClone(data);
  },
};
const compact=new URLSearchParams(location.search).has('compact');
const card=document.createElement(compact?'ha-pinger-card':'ha-pinger-panel');
if(compact){document.querySelector('#app').className='compact-preview';card.setConfig({compact:true});}
card.hass=hass;
document.querySelector('#app').append(card);
function setTheme(dark) {
  document.documentElement.dataset.theme=dark?'dark':'light';
  hass.themes.darkMode=dark;
  card.hass=hass;
  document.querySelector('#theme-toggle').textContent=dark?'Hellmodus':'Dunkelmodus';
}
setTheme(hass.themes.darkMode);
document.querySelector('#theme-toggle').addEventListener('click',()=>setTheme(!hass.themes.darkMode));
// Exposed only in this fixture for deterministic browser tests.
window.pingerDemo={data,hass,card,emit,commands,disconnect:()=>handlers.get('disconnected')?.forEach(handler=>handler())};
