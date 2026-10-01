/* Network Control Center. Native web components, no external scripts or fonts. */
const ICONS = {
  network: '<rect x="8" y="3" width="8" height="6" rx="1.5"/><path d="M12 9v5M5 14h14M5 14v3m14-3v3"/><rect x="2" y="17" width="6" height="4" rx="1"/><rect x="16" y="17" width="6" height="4" rx="1"/>',
  pulse: '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  cross: '<path d="m6 6 12 12M6 18 18 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  settings: '<path d="M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z"/><circle cx="12" cy="12" r="3"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 13 2M5 16a8 8 0 0 0 13 2"/>',
  search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6h14M5 18h14"/>',
  edit: '<path d="m15 4 5 5M4 20l5-1L21 7l-4-4L5 15Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  shield: '<path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6Z"/><path d="m8 12 3 3 5-6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  up: '<path d="m6 14 6-6 6 6"/>',
  down: '<path d="m6 10 6 6 6-6"/>',
  home: '<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8"/>',
  router: '<rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 13V4m10 9V4M7 17h.01M11 17h.01"/>',
  office: '<rect x="5" y="3" width="14" height="18" rx="1"/><path d="M9 7h1m4 0h1M9 11h1m4 0h1M10 21v-6h4v6"/>',
  server: '<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6h.01M7 17h.01M12 6h5m-5 11h5"/>',
  wifi: '<path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-11 4a6 6 0 0 1 8 0M12 20h.01"/>',
  storage: '<path d="M3 8 12 3l9 5v13H3ZM7 21V11h10v10M7 15h10m-10 3h10"/>',
  phone: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
  camera: '<path d="M8 5 6 8H3v12h18V8h-3l-2-3Z"/><circle cx="12" cy="13" r="4"/>',
  printer: '<path d="M7 8V3h10v5M7 17H3V8h18v9h-4M7 14h10v7H7Z"/>',
  tv: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/>',
  laptop: '<path d="M5 16V4h14v12M2 16h20l-2 4H4Z"/>',
  external: '<path d="M14 3h7v7m0-7L10 14M10 5H3v16h16v-7"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  moon: '<path d="M20 15.5A9 9 0 0 1 8.5 4 9 9 0 1 0 20 15.5Z"/>',
};
const GROUP_ICONS = {network:'Netzwerk',home:'Zuhause',router:'Router',office:'Büro',server:'Server',globe:'Internet',wifi:'WLAN',storage:'Lager'};
const TARGET_ICONS = {auto:'Automatisch',...GROUP_ICONS,phone:'Handy',camera:'Kamera',printer:'Drucker',tv:'Fernseher',laptop:'Laptop'};
const methodLabel = {icmp:'Ping',web:'Web',both:'Ping & Web',tcp:'TCP'};
let mdiCatalog=null, mdiPaths=new Map(), mdiLoading=null;
const loadIconCatalog=()=>mdiCatalog?Promise.resolve(mdiCatalog):(mdiLoading||=fetch(new URL('./icon-catalog.json?v=1.4.1',import.meta.url)).then(response=>{if(!response.ok)throw new Error('Icon-Katalog konnte nicht geladen werden.');return response.json();}).then(rows=>{mdiCatalog=rows;mdiPaths=new Map(rows.map(row=>['mdi:'+row[0],row[1]]));return rows;}).catch(error=>{mdiLoading=null;throw error;}));
const icon = (name, cls = '') => mdiPaths.has(name)
  ? `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="${mdiPaths.get(name)}"/></svg>`
  : `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.network}</svg>`;
const brand = () => `<img class="brand-icon" src="${new URL('./brand.svg',import.meta.url).href}" width="36" height="36" alt="">`;
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, s => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[s]));
const number = value => value == null ? '—' : new Intl.NumberFormat('de-DE', {maximumFractionDigits: 1}).format(value);
const time = value => value ? new Date(value * 1000).toLocaleTimeString('de-DE', {hour:'2-digit',minute:'2-digit',second:'2-digit'}) : 'Noch nicht geprüft';
const date = value => value ? new Date(value * 1000).toLocaleString('de-DE') : '—';
const statusLabel = {online:'Erreichbar', offline:'Nicht erreichbar', unknown:'Ungeprüft', error:'Prüffehler', paused:'Pausiert'};

const STYLESHEET_URL = new URL('./ha-pinger.css?v=1.4.1', import.meta.url).href;

class NetworkElement extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this._tab = 'ip'; this._filter = 'all'; this._search = ''; this._favorites = false;
    this._data = null; this._busy = false; this._connected = true; this._generation = 0;
    this._network=''; this._images=new Map(); this._imageLoading=new Set(); this._manualChecks=new Set(); this._checkingAll=false;
    try{this._themeOverride=localStorage.getItem('ha_pinger_theme');}catch{this._themeOverride=null;}
    this.shadowRoot.innerHTML = `<link rel="stylesheet" href="${escapeHTML(STYLESHEET_URL)}"><div id="content"></div><dialog aria-labelledby="dialog-title"></dialog><div id="toast" role="status"></div>`;
    this.shadowRoot.addEventListener('click', event => this._click(event));
    this.shadowRoot.addEventListener('input', event => {
      if (event.target.id === 'search') { this._search = event.target.value; this.render(); }
      if (event.target.name === 'icon_search') this._renderIconGrid(event.target.closest('.icon-selector'),0);
      if (event.target.name === 'ip_range') {
        const input=event.target,form=input.closest('form');
        input.setCustomValidity('');input.removeAttribute('aria-invalid');form.querySelector('.group-range-feedback').className='group-range-feedback hint full';
        clearTimeout(this._groupRangeTimer);
        form.querySelector('.group-range-feedback').textContent=input.value.trim()?'Bereich wird geprüft …':'Optional: Ohne Bereich können beliebige IP-Adressen zugeordnet werden.';
        this._groupRangeTimer=setTimeout(()=>this._validateGroupRange(form),350);
      }
    });
    this.shadowRoot.addEventListener('change', event => {
      if (event.target.id === 'filter') { this._filter = event.target.value; this.render(); }
      if (event.target.name === 'method') {
        this._syncMethodFields();
      }
      if (event.target.name === 'web_scheme') {
        const port = this.shadowRoot.querySelector('[name=web_port]');
        if (['80','443'].includes(port.value)) port.value = event.target.value === 'https' ? '443' : '80';
      }
      if (event.target.name === 'icon') {
        const preview=this.shadowRoot.querySelector('.icon-preview');
        if(preview)preview.innerHTML=icon(event.target.value);
      }
      if(event.target.name==='device_icon')this._updateDeviceIconPreview(event.target.closest('form'));
      if(event.target.name==='device_image')this._uploadImage(event.target);
      if(event.target.name==='use_range')this._syncRangeFields();
      if(event.target.name==='wireguard_file')this._readWireGuard(event.target);
      if(event.target.id==='sort-select')this._command('settings',{sort_by:event.target.value});
    });
    this.shadowRoot.addEventListener('submit', event => this._submit(event));
    this.shadowRoot.addEventListener('keydown', event => {
      if (event.target.getAttribute('role') !== 'tab' || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      this._tab = event.key === 'Home' ? 'ip' : event.key === 'End' ? 'ddns' : this._tab === 'ip' ? 'ddns' : 'ip';
      this._search = ''; this._filter = 'all'; this.render();
      this.shadowRoot.querySelector(`button[data-tab="${this._tab}"]`)?.focus();
    });
    this._readyHandler = () => { this._connected = true; this._refresh(); };
    this._disconnectHandler = () => { this._connected = false; this.render(); };
  }
  set hass(value) {
    this._hass = value;
    this._admin = Boolean(value?.user?.is_admin);
    // Theme colors are inherited CSS variables; only native form controls and
    // standalone fallbacks need the selected mode explicitly.
    this._applyTheme();
    this._ensureConnection();
    if(this._data)this.render();
  }
  get hass() { return this._hass; }
  _applyTheme(){
    const explicit=['dark','light'].includes(this._themeOverride)?this._themeOverride:'';
    this.setAttribute('data-theme',explicit);
    this.setAttribute('data-dark',String(explicit?explicit==='dark':Boolean(this._hass?.themes?.darkMode)));
  }
  setConfig(config) { this._config = config; this.render(); }
  getCardSize() { return this._config?.compact === false ? 12 : 5; }
  getGridOptions() { return {columns:12, rows:'auto', min_columns:6}; }
  static getStubConfig() { return {compact:true}; }
  connectedCallback() {
    this._ensureConnection();
    this._ticker = setInterval(() => this.render(), 15000);
    this.render();
  }
  disconnectedCallback() {
    this._generation++;
    this._detachConnection();
    clearInterval(this._ticker); clearTimeout(this._retry); clearTimeout(this._toastTimer); clearTimeout(this._groupRangeTimer);
  }
  _detachConnection() {
    if (this._unsubscribe) { Promise.resolve(this._unsubscribe()).catch(() => {}); this._unsubscribe = null; }
    if (this._connection) {
      this._connection.removeEventListener('ready', this._readyHandler);
      this._connection.removeEventListener('disconnected', this._disconnectHandler);
    }
    this._connection = null;
  }
  async _ensureConnection() {
    const connection = this._hass?.connection;
    if (!this.isConnected || !connection || connection === this._connection) return;
    this._detachConnection();
    const generation = ++this._generation;
    this._connection = connection;
    this._connected = connection.connected !== false;
    connection.addEventListener('ready', this._readyHandler);
    connection.addEventListener('disconnected', this._disconnectHandler);
    try {
      const unsubscribe = await connection.subscribeMessage(data => {
        if (generation !== this._generation) return;
        this._data = data; this._connectionError = ''; this.render();
      }, {type:'ha_pinger/subscribe'});
      if (generation !== this._generation || !this.isConnected) await unsubscribe();
      else this._unsubscribe = unsubscribe;
    } catch (error) {
      if (generation !== this._generation) return;
      this._connectionError = error.message || 'Verbindung zum Control Center nicht möglich.';
      this._detachConnection(); this.render();
      this._retry = setTimeout(() => this._ensureConnection(), 5000);
    }
  }
  async _refresh() {
    try { this._data = await this._hass.callWS({type:'ha_pinger/get'}); this._connectionError = ''; }
    catch (error) { this._connectionError = error.message || 'Verbindung unterbrochen.'; }
    this.render();
  }
  _button(action, label, image, extra = '') {
    return `<button data-action="${action}" ${extra}>${image ? icon(image) : ''}${label}</button>`;
  }
  _badge(target) { return `<span class="status ${target.status}"><span class="dot"></span>${statusLabel[target.status] || 'Unbekannt'}</span>`; }
  _history(target, length = 20) {
    const points = target.history.slice(-length);
    return `<div class="history" aria-label="${escapeHTML(`Letzte ${points.length} Prüfungen, ${number(target.availability)} Prozent erfolgreich`)}">${'<i></i>'.repeat(Math.max(0,length-points.length))}${points.map(p => `<i class="${p.online ? 'up' : 'down'}" title="${escapeHTML(date(p.time))}: ${p.online?'Erreichbar':'Keine Antwort'}"></i>`).join('')}</div>`;
  }
  _showToast(message) {
    const host = this.shadowRoot.querySelector('#toast');
    host.className = 'toast'; host.textContent = message;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => { host.className=''; host.textContent=''; }, 5500);
  }
  async _command(action, data = {}, target_id) {
    if(action==='check') {
      if(target_id?this._manualChecks.has(target_id):this._checkingAll)return false;
      if(target_id)this._manualChecks.add(target_id);else this._checkingAll=true;
      this.render();
      try{this._data=await this._hass.callWS({type:'ha_pinger/command',action,data,...(target_id?{target_id}:{})});return true;}
      catch(error){this._showToast(error.message||'Prüfung fehlgeschlagen.');return false;}
      finally{if(target_id)this._manualChecks.delete(target_id);else this._checkingAll=false;this.render();}
    }
    if (this._busy) return false;
    this._busy = true; this.render();
    const errorNode = this.shadowRoot.querySelector('.form-error');
    if (errorNode) errorNode.textContent = '';
    try {
      this._data = await this._hass.callWS({type:'ha_pinger/command', action, data, ...(target_id ? {target_id} : {})});
      return true;
    } catch (error) {
      const message = error.message || 'Aktion fehlgeschlagen. Verbindung und Berechtigungen prüfen.';
      if (errorNode) errorNode.textContent = message;
      this._showToast(message); return false;
    } finally { this._busy = false; this.render(); }
  }
  render() {
    const content = this.shadowRoot.querySelector('#content');
    if (!content) return;
    const focused = this.shadowRoot.activeElement;
    const focusId = content.contains(focused) ? focused?.id : null;
    const focusButton = content.contains(focused) && focused?.dataset.action ? {...focused.dataset} : null;
    const selection = focused?.tagName === 'INPUT' ? [focused.selectionStart, focused.selectionEnd] : null;
    if (!this._data?.available) {
      content.innerHTML = `<div class="compact"><h2>${icon('network')} Network Control Center</h2><p>${escapeHTML(this._connectionError || (this._data ? 'Integration ist nicht geladen. In den Home-Assistant-Einstellungen aktivieren.' : 'Verbindung wird hergestellt …'))}</p></div>`;
      return;
    }
    const isCompact = this.localName === 'ha-pinger-card' && this._config?.compact !== false;
    this._network=this._data.active_network||'';
    content.innerHTML = isCompact ? this._compact() : this._full();
    this._loadImages();
    if(!mdiCatalog&&!this._iconsLoading&&[...this._data.targets,...(this._data.groups||[])].some(item=>item.icon?.startsWith('mdi:'))){
      this._iconsLoading=true;
      loadIconCatalog().then(()=>{if(this.isConnected)this.render();}).catch(()=>{}).finally(()=>{this._iconsLoading=false;});
    }
    if (focusId) {
      const next = this.shadowRoot.getElementById(focusId);
      next?.focus();
      if (selection && next?.setSelectionRange) next.setSelectionRange(...selection);
    } else if (focusButton) {
      [...content.querySelectorAll('button[data-action]')].find(button =>
        button.dataset.action === focusButton.action && button.dataset.id === focusButton.id && button.dataset.tab === focusButton.tab)?.focus();
    }
    this.shadowRoot.querySelectorAll('dialog button[type=submit]').forEach(button => { button.disabled = this._busy || Boolean(button.closest('form')?.dataset.validating) || Number(button.closest('form')?.dataset.loading||0)>0; });
  }
  _compact() {
    const rows = this._data.targets.filter(t=>(t.network_id||'')===this._network);
    const online = rows.filter(t => t.status === 'online').length;
    const offline = rows.filter(t => t.status === 'offline').length;
    const favorites = this._grouped(rows).flatMap(g=>g.rows).filter(t => t.favorite).slice(0,5);
    return `<ha-card class="compact"><div class="compact-head"><div class="compact-title">${brand()}<div><h2>${escapeHTML(this._config?.title || 'Network Control Center')}</h2><p>Erreichbarkeit und Favoriten</p></div></div><span class="live" data-connected="${this._connected}"><span class="dot"></span>${this._connected?'LIVE':'GETRENNT'}</span></div>
      ${!this._connected ? '<p>Verbindung unterbrochen · letzte bekannte Werte</p>' : ''}
      <div class="compact-stats"><div><strong>${rows.length}</strong><span>Adressen</span></div><div><strong style="color:var(--green)">${online}</strong><span>Erreichbar</span></div><div><strong style="color:var(--red)">${offline}</strong><span>Offline</span></div><div><strong>${rows.length-online-offline}</strong><span>Offen / pausiert</span></div></div>
      ${favorites.map(t => `<div class="compact-target"><div><strong>${escapeHTML(t.name)}</strong><small class="mono">${escapeHTML(t.host)}</small></div>${this._badge(t)}</div>`).join('')}
      ${this._button('open', 'Control Center öffnen', 'arrow', 'class="compact-open"')}</ha-card>`;
  }
  _full() {
    const {settings} = this._data;
    const targets=this._data.targets.filter(t=>(t.network_id||'')===this._network);
    const ids=new Set(targets.map(t=>t.id));
    const events=this._data.events.filter(e=>!e.target_id||ids.has(e.target_id));
    const online = targets.filter(t => t.status === 'online').length;
    const offline = targets.filter(t => t.status === 'offline').length;
    const unresolved = targets.length - online - offline;
    const notifyCount = targets.filter(t => t.notify && t.enabled).length;
    const busy = this._checkingAll;
    const disable = !this._admin || this._busy || !this._connected || this._data.switching_network ? 'disabled' : '';
    const selectedTab = targets.filter(t => t.kind === this._tab);
    const rows = this._sortRows(selectedTab.filter(t => (!this._favorites || t.favorite) &&
      (this._filter === 'all' || (this._filter === 'attention' ? ['offline','error','unknown'].includes(t.status) : t.status === this._filter)) &&
      `${t.name} ${t.host}`.toLocaleLowerCase('de').includes(this._search.toLocaleLowerCase('de'))));
    const lastChecked = Math.max(...targets.map(t => t.last_checked || 0),0);
    const nextCheck = Math.min(...targets.filter(t => t.enabled).map(t => t.next_check || 0));
    const wait = Number.isFinite(nextCheck) ? Math.max(0,Math.ceil((nextCheck-Date.now()/1000)/60)) : null;
    return `<main class="shell"><div class="inner">
      ${this.localName === 'ha-pinger-panel' ? this._button('menu','Menü','menu','class="mobile-menu" aria-label="Home-Assistant-Seitenleiste öffnen"') : ''}
      <header class="head"><div class="title-line">${brand()}<h1>Network Control Center</h1><span class="live" data-connected="${this._connected}"><span class="dot"></span>${this._connected?'LIVE':'GETRENNT'}</span></div>
      <div class="head-actions">${this._button('check',`<span class="action-label">${busy?'Prüfung läuft':'Jetzt prüfen'}</span>`,'refresh',`${disable || (busy?'disabled':'')} title="Alle aktiven Adressen jetzt prüfen"`)}${this._button('settings','<span class="action-label">Einstellungen</span>','settings',`${disable} class="quiet" title="Einstellungen"`)}${this._button('theme','',this.getAttribute('data-dark')==='true'?'sun':'moon',`class="square quiet" aria-label="${this.getAttribute('data-dark')==='true'?'Hellmodus aktivieren':'Dunkelmodus aktivieren'}" title="${this.getAttribute('data-dark')==='true'?'Hellmodus':'Dunkelmodus'}"`)}</div></header>
      ${!this._connected || this._connectionError ? `<div class="banner" role="alert">Verbindung unterbrochen. Die angezeigten Werte sind möglicherweise veraltet. ${escapeHTML(this._connectionError || '')}</div>` : ''}
      ${!this._admin ? '<div class="banner">Leseansicht · Zum Ändern bitte mit einem Administratorkonto anmelden.</div>' : ''}
      <section class="stats" aria-label="Netzwerkübersicht">
        <ha-card class="stat"><div class="stat-top">Alle Adressen ${icon('network')}</div><div class="stat-value"><strong>${targets.length}</strong></div><div class="stat-bottom">${targets.filter(t=>t.kind==='ip').length} IP-Adressen · ${targets.filter(t=>t.kind==='ddns').length} DDNS</div></ha-card>
        <ha-card class="stat"><div class="stat-top">Erreichbar ${icon('check')}</div><div class="stat-value"><strong>${online}</strong><span>online</span></div><div class="stat-line"><span style="width:${targets.length?100*online/targets.length:0}%"></span></div></ha-card>
        <ha-card class="stat"><div class="stat-top">Nicht erreichbar ${icon('cross')}</div><div class="stat-value"><strong>${offline}</strong><span>offline</span></div><div class="stat-bottom">${unresolved ? `${unresolved} weitere ungeprüft, pausiert oder mit Fehler` : offline ? 'Details in der Adressübersicht' : 'Keine Ausfälle erkannt'}</div></ha-card>
        <ha-card class="stat"><div class="stat-top">Prüfintervall ${icon('clock')}</div><div class="stat-value"><strong>${settings.interval_minutes}</strong><span>Minuten</span></div><div class="stat-bottom">${wait === null ? 'Keine aktiven Adressen' : busy?'Prüfung läuft …':wait===0?'Nächste Prüfung in Kürze':`Nächste Prüfung in ca. ${wait} Min.`}</div></ha-card>
      </section><div class="workspace"><section aria-label="Adressen">
      <div class="network-strip"><div class="current-network">${icon('router')}<span>${escapeHTML(this._data.networks?.find(n=>n.id===this._network)?.name||'Heimnetz')}<small>${this._data.switching_network?'Netz wird gewechselt …':this._data.vpn?.error?'WireGuard-Status unbekannt':this._network?'WireGuard aktiv':'WireGuard deaktiviert'}</small></span></div>${this._button('networks','Netze','settings',`class="quiet" ${disable}`)}</div>
      ${this._data.vpn?.error?`<div class="banner" role="alert">${escapeHTML(this._data.vpn.error)}</div>`:''}
      <div class="tabs" role="tablist">${['ip','ddns'].map(tab=>`<button class="tab ${this._tab===tab?'active':''}" role="tab" aria-selected="${this._tab===tab}" data-action="tab" data-tab="${tab}">${icon(tab==='ip'?'network':'globe')}${tab==='ip'?'IP-Adressen':'DDNS'} <span class="count">${targets.filter(t=>t.kind===tab).length}</span></button>`).join('')}</div>
      <div class="toolbar filter-row">
      <select id="filter" aria-label="Nach Status filtern">${[['all','Alle Status'],['online','Erreichbar'],['offline','Nicht erreichbar'],['attention','Prüfen / Ausfall'],['paused','Pausiert']].map(([value,label])=>`<option value="${value}" ${this._filter===value?'selected':''}>${label}</option>`).join('')}</select>
      <label class="search">${icon('search')}<input id="search" placeholder="Filtern …" value="${escapeHTML(this._search)}" aria-label="Adressen durchsuchen"></label>
      <select id="sort-select" aria-label="Sortieren nach" ${disable}>${[['manual','Manuell'],['address','Adresse'],['name','Name'],['status','Status'],['last_checked','Letzte Prüfung']].map(([value,label])=>`<option value="${value}" ${settings.sort_by===value?'selected':''}>${label}</option>`).join('')}</select>${this._button('sort-direction','',settings.sort_desc?'down':'up',`class="square quiet" title="Sortierrichtung ändern" aria-label="Sortierrichtung ändern" ${disable||settings.sort_by==='manual'?'disabled':''}`)}</div>
      <div class="action-toolbar">${this._button('favorites','','star',`class="square toggle-filter ${this._favorites?'active':''}" aria-label="Nur Favoriten anzeigen" aria-pressed="${this._favorites}" title="Nur Favoriten"`)}${this._button('organize','Gruppe','menu',`class="quiet" ${disable}`)}${this._button('add','Hinzufügen','plus',`class="primary add" ${disable}`)}</div>
      <div class="section-heading"><div><h2>${this._favorites?icon('star'):''}${this._tab==='ip'?'Deine Geräte':'Deine Domains'}</h2><p>${rows.length} von ${selectedTab.length}</p></div></div>
      ${this._tab==='ddns'?'<p class="hint">DNS-Auflösung und Erreichbarkeit deiner Domains. Ein grüner Status bestätigt eine Antwort von mindestens einer aufgelösten Adresse.</p>':''}
      ${rows.length?this._grouped(rows).filter(g=>g.rows.length).map(g=>`<section class="target-group">${this._data.groups?.length?this._groupHeading(g):''}<div class="targets">${g.rows.map(t=>this._row(t,disable)).join('')}</div></section>`).join(''):`<div class="targets empty">${icon(this._tab==='ip'?'network':'globe')}<h3>${selectedTab.length?'Keine passenden Adressen':this._tab==='ddns'?'Deine Verbindung nach draußen':'Hier beginnt dein Netzwerk'}</h3><p>${selectedTab.length?'Passe die Suche oder den Filter an.':'Füge '+(this._tab==='ddns'?'deine erste DDNS-Domain':'eine IP-Adresse')+' hinzu und behalte ihre Erreichbarkeit im Blick.'}</p>${this._button(selectedTab.length?'reset':'add',selectedTab.length?'Filter zurücksetzen':'Adresse hinzufügen',selectedTab.length?'refresh':'plus',`${selectedTab.length?'':disable}`)}</div>`}
      <div class="foot"><span>${icon('shield')} ${this._network?'Geprüft über WireGuard':'Geprüft von deinem Home Assistant'}</span><span>Letzte Prüfung: ${time(lastChecked)}</span></div>
      </section><aside class="aside"><section class="aside-card"><h2>${icon('settings')} Überwachung</h2><div class="setting-line"><span>Standardintervall</span><strong>Alle ${settings.interval_minutes} Min.</strong></div><div class="setting-line"><span>Ausfallmeldung</span><strong>${settings.offline_after_seconds?`Nach ${settings.offline_after_seconds} Sek.`:'Sofort'}</strong></div><div class="setting-line"><span>Prüfversuche</span><strong>${settings.attempts} × ${settings.timeout_seconds} Sek.</strong></div><div class="setting-line"><span>Push aktiviert</span><strong>${notifyCount} Adressen</strong></div>
      ${this._button('settings','Überwachung anpassen','arrow',`class="quiet aside-link" ${disable}`)}
      ${!settings.notify_service?`<div class="notify-note">${icon('bell')}<p class="note">Wähle in den Einstellungen dein Handy, um Ausfallmeldungen zu erhalten.</p></div>`:''}</section>
      <section class="aside-card activity"><h2>${icon('clock')} Letzte Aktivitäten</h2>${events.length?events.slice(-6).reverse().map(e=>`<div class="event ${escapeHTML(e.kind)}"><span class="dot"></span><div><strong>${escapeHTML(e.name)}</strong><p>${escapeHTML(e.message)}</p></div><time title="${escapeHTML(date(e.time))}">${time(e.time).slice(0,5)}</time></div>`).join(''):'<p class="note">Hier erscheinen Statuswechsel und Benachrichtigungen nach der ersten Prüfung.</p>'}</section>
      </aside></div>
    </div></main>`;
  }
  _row(t, disable) {
    const latency = t.status==='online' ? `${number(t.latency_ms)} ms${t.method==='tcp'?' · TCP':''}` : t.status==='offline' ? `seit ${time(t.offline_since).slice(0,5)}` : t.status==='paused'?'Prüfung deaktiviert':t.error?'Details öffnen':'Warte auf Prüfung';
    return `<article class="target ${t.status}" data-target-id="${t.id}"><div class="device-icon">${this._deviceImage(t)}</div><div><div class="target-title"><strong title="${escapeHTML(t.name)}">${escapeHTML(t.name)}</strong>${t.favorite?icon('star'):''}</div><p class="address mono">${escapeHTML(t.host)}${t.method==='tcp'?` : ${t.port}`:''}</p>${this._checkBadges(t)}${t.notify&&['offline','error'].includes(t.status)?`<p class="row-push-status">${icon('bell')} ${escapeHTML(t.notification_status||'')}</p>`:''}${t.kind==='ddns'&&t.resolved_ips.length?`<p class="resolved mono">→ ${escapeHTML(t.resolved_ips.join(' · '))}</p>`:''}</div><div class="status-cell">${this._badge(t)}<div class="latency">${escapeHTML(latency)}</div></div><div class="trend">${this._history(t)}<div class="history-label"><span>Verlauf</span><span>${number(t.availability)} %</span></div></div><div class="row-actions">
      ${this._button('favorite','','star',`class="star ${t.favorite?'active':''}" data-id="${t.id}" title="${t.favorite?'Favorit entfernen':'Favorisieren'}" aria-label="${escapeHTML(t.name)} ${t.favorite?'aus Favoriten entfernen':'favorisieren'}" aria-pressed="${t.favorite}" ${disable}`)}
      ${this._button('notify','','bell',`class="bell ${t.notify?'active':''}" data-id="${t.id}" title="Push ${t.notify?'deaktivieren':'aktivieren'}" aria-label="Push für ${escapeHTML(t.name)}" aria-pressed="${t.notify}" ${disable}`)}
      ${['web','both'].includes(t.method)?`<a class="icon-button" href="${escapeHTML(this._webUrl(t))}" target="_blank" rel="noopener noreferrer" title="Weboberfläche im Browser öffnen" aria-label="Weboberfläche von ${escapeHTML(t.name)} öffnen">${icon('external')}</a>`:''}
      ${this._button('check-one','','refresh',`class="check-one ${t.checking||this._manualChecks.has(t.id)?'checking':''}" data-id="${t.id}" title="Diese Adresse jetzt prüfen" aria-label="${escapeHTML(t.name)} jetzt prüfen" ${!this._admin||!this._connected||!t.enabled||t.checking||this._manualChecks.has(t.id)?'disabled':''}`)}
      ${this._button('details','','pulse',`data-id="${t.id}" title="Details und Verlauf" aria-label="Details für ${escapeHTML(t.name)}"`)}
      ${this._button('edit','','edit',`data-id="${t.id}" title="Bearbeiten" aria-label="${escapeHTML(t.name)} bearbeiten" ${disable}`)}
      </div></article>`;
  }
  async _click(event) {
    const button = event.target.closest('button[data-action]');
    if (!button || button.disabled) return;
    const action = button.dataset.action;
    const target = this._data?.targets?.find(t=>t.id===button.dataset.id);
    const group = this._data?.groups?.find(g=>g.id===button.dataset.id);
    if (action==='tab') { this._tab=button.dataset.tab; this._search=''; this._filter='all'; this.render(); }
    else if(action==='theme'){this._themeOverride=this.getAttribute('data-dark')==='true'?'light':'dark';try{localStorage.setItem('ha_pinger_theme',this._themeOverride);}catch{}this._applyTheme();this.render();}
    else if (action==='favorites') { this._favorites=!this._favorites; this.render(); }
    else if (action==='reset') { this._search='';this._filter='all';this._favorites=false;this.render(); }
    else if (action==='add'||action==='edit') this._edit(target);
    else if (action==='settings') { await this._refresh(); if(this._data?.available) this._settings(); }
    else if (action==='details') this._details(target);
    else if (action==='browse-icons') this._browseIcons(button);
    else if (action==='icon-page') this._renderIconGrid(button.closest('.icon-selector'),Number(button.dataset.page));
    else if (action==='choose-icon') {
      const section=button.closest('.icon-selector'),select=section.querySelector('select');
      const name=button.dataset.icon;
      if(!mdiPaths.has(name))return;
      if(![...select.options].some(option=>option.value===name))select.add(new Option(name,name));
      select.value=name;select.dispatchEvent(new Event('change',{bubbles:true}));
      section.querySelector('.icon-picker').hidden=true;
      section.querySelector('[data-action=browse-icons]').setAttribute('aria-expanded','false');
      select.focus();
    }
    else if (action==='sort-direction') await this._command('settings',{sort_desc:!this._data.settings.sort_desc});
    else if (action==='remove-image'){this._editImageData=null;this._imageRemoved=true;this.shadowRoot.querySelector('[name=device_image]').value='';this._updateDeviceIconPreview(this.shadowRoot.querySelector('form[data-form=target]'));}
    else if (action==='preview-range') this._previewRange();
    else if (action==='group-range' && group) this._edit(undefined,{kind:'ip',name:group.name,group_id:group.id,range:group.ip_range});
    else if (action==='log' && target) this._log(target);
    else if (action==='time-slot' && target) this._showToast(`${date(Number(button.dataset.start))} – ${time(Number(button.dataset.end))}: ${button.title}`);
    else if (action==='clear-log' && target) this._dialog('Protokoll löschen?',`<p>Das Protokoll von <strong>${escapeHTML(target.name)}</strong> wird gelöscht. Status und 30-Tage-Verlauf bleiben erhalten.</p><div class="form-error"></div><div class="dialog-foot">${this._button('log','Abbrechen',null,`data-id="${target.id}"`)}${this._button('confirm-clear-log','Protokoll löschen',null,`class="danger" data-id="${target.id}"`)}</div>`);
    else if (action==='confirm-clear-log' && target){if(await this._command('clear_log',{},target.id))this._log(target);}
    else if (action==='networks') this._networks();
    else if (action==='select-network'){
      if(await this._command('select_network',{},button.dataset.id)){this._search='';this._filter='all';this._networks();this._showToast(this._network?'WireGuard-Netz aktiviert.':'Heimnetz aktiv. WireGuard deaktiviert.');}
    }
    else if (action==='agent-settings') this._agentSettings();
    else if (action==='test-agent'){if(await this._command('test_agent'))this._showToast('WireGuard-App erreichbar.');}
    else if (action==='new-network'||action==='edit-network') this._editNetwork(this._data.networks?.find(n=>n.id===button.dataset.id));
    else if (action==='delete-network')this._dialog('Netz löschen?',`<p>Die gespeicherte WireGuard-Konfiguration dieses Netzes wird entfernt. Das ist erst möglich, wenn dem Netz keine Adressen mehr zugeordnet sind.</p><div class="form-error"></div><div class="dialog-foot">${this._button('networks','Abbrechen',null)}${this._button('confirm-delete-network','Netz löschen',null,`class="danger" data-id="${button.dataset.id}"`)}</div>`);
    else if (action==='confirm-delete-network'){if(await this._command('delete_network',{},button.dataset.id)){if(this._network===button.dataset.id)this._network='';this._networks();this.render();}}
    else if (action==='generate-token'){this.shadowRoot.querySelector('[name=agent_token]').value=Array.from(crypto.getRandomValues(new Uint8Array(24)),b=>b.toString(16).padStart(2,'0')).join('');this._showToast('Schlüssel erzeugt. Für die App-Konfiguration kopieren und anschließend hier speichern.');}
    else if (action==='copy-token'){const input=this.shadowRoot.querySelector('[name=agent_token]');try{await navigator.clipboard.writeText(input.value);this._showToast('Schlüssel kopiert.');}catch{input.type='text';input.select();this._showToast('Bitte den markierten Schlüssel kopieren.');}}
    else if (action==='organize') { await this._refresh(); if(this._data?.available) this._organize(); }
    else if (action==='add-group'||action==='edit-group') this._editGroup(group);
    else if (action==='delete-group' && group) this._deleteGroup(group);
    else if (action==='confirm-delete-group' && group) {
      if(await this._command('delete_group',{},group.id)) this._organize();
    }
    else if (action==='move') {
      const scroll = this.shadowRoot.querySelector('dialog').scrollTop;
      if(await this._command('move',{scope:button.dataset.scope,direction:Number(button.dataset.direction)},button.dataset.id)) {
        this._organize();
        const dialog=this.shadowRoot.querySelector('dialog');
        requestAnimationFrame(()=>{
          const moved=[...dialog.querySelectorAll('[data-action=move]')].find(b=>b.dataset.id===button.dataset.id && b.dataset.direction===button.dataset.direction && !b.disabled);
          (moved || dialog.querySelector('[data-action=close]'))?.focus({preventScroll:true});
          dialog.scrollTop=scroll;
        });
      }
    }
    else if (action==='close') this.shadowRoot.querySelector('dialog').close();
    else if (action==='menu') this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    else if (action==='open') { history.pushState(null,'','/network-control'); window.dispatchEvent(new CustomEvent('location-changed')); }
    else if (action==='check'||action==='check-one') {
      if(await this._command('check',{},action==='check-one'?target?.id:undefined)) {
        this._showToast('Prüfung abgeschlossen.');
        const dialog = this.shadowRoot.querySelector('dialog');
        if (action==='check-one' && dialog.open && dialog.dataset.detailId === target?.id) this._details(this._data.targets.find(t=>t.id===target.id));
      }
    } else if (action==='favorite' && target) await this._command('save',{favorite:!target.favorite},target.id);
    else if (action==='notify' && target) {
      if(await this._command('save',{notify:!target.notify},target.id)) {
        if (!target.notify && !this._data.settings.notify_service) this._showToast('Push aktiviert. Bitte noch dein Handy in den Einstellungen auswählen.');
      }
    } else if (action==='delete' && target) this._delete(target);
    else if (action==='confirm-delete' && target) {
      if(await this._command('delete',{},target.id)) {this.shadowRoot.querySelector('dialog').close();this._showToast('Adresse gelöscht.');}
    } else if (action==='test-notify') {
      if(await this._command('test_notify')) this._showToast('Testnachricht an den gespeicherten Handy-Dienst gesendet.');
    }
  }
  _dialog(title, body) {
    const dialog = this.shadowRoot.querySelector('dialog');
    dialog.dataset.detailId = '';
    dialog.classList.remove('wide');
    dialog.innerHTML=`<div class="dialog-head"><h2 id="dialog-title">${escapeHTML(title)}</h2>${this._button('close','','cross','class="square quiet" aria-label="Schließen"')}</div><div class="dialog-body">${body}</div>`;
    if (!dialog.open) dialog.showModal();
    requestAnimationFrame(()=>dialog.querySelector('input:not([type=checkbox]),select,button')?.focus());
  }
  _field(label,name,value,type='text',extra='') {
    return `<label class="field">${label}<input name="${name}" type="${type}" value="${escapeHTML(value)}" ${extra}></label>`;
  }
  _checkbox(label,name,checked) {return `<label class="check"><input type="checkbox" name="${name}" ${checked?'checked':''}>${label}</label>`;}
  _iconSelector(label,name,value,choices){
    const options={...choices,...(value?.startsWith('mdi:')?{[value]:value}:{})};
    return `<div class="full icon-selector"><label class="field">${label}<select name="${name}" aria-label="${label}">${Object.entries(options).map(([key,title])=>`<option value="${escapeHTML(key)}" ${key===value?'selected':''}>${escapeHTML(title)}</option>`).join('')}</select></label>${this._button('browse-icons','Alle Symbole durchsuchen','search','type="button" class="quiet" aria-expanded="false"')}<div class="icon-picker" hidden><label class="field">Icons durchsuchen<input type="search" name="icon_search" placeholder="z. B. Router, Kamera, WLAN, Küche …" autocomplete="off"></label><p class="icon-results hint" role="status">Katalog wird geladen …</p><div class="icon-grid"></div><div class="icon-pages"></div></div></div>`;
  }
  async _browseIcons(button){
    const section=button.closest('.icon-selector'),picker=section.querySelector('.icon-picker');
    picker.hidden=!picker.hidden;button.setAttribute('aria-expanded',String(!picker.hidden));
    if(picker.hidden)return;
    try{await loadIconCatalog();if(!section.isConnected)return;this._renderIconGrid(section,0);section.querySelector('[name=icon_search]').focus();}
    catch(error){if(section.isConnected)section.querySelector('.icon-results').textContent=error.message;}
  }
  _renderIconGrid(section,page=0){
    if(!mdiCatalog||!section)return;
    const normalize=value=>value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    const query=normalize(section.querySelector('[name=icon_search]').value.trim()).replace(/^mdi:/,'').split(/\s+/).filter(Boolean);
    const rows=query.length?mdiCatalog.filter(row=>query.every(term=>normalize(row[2]).includes(term))):mdiCatalog;
    const size=48,pages=Math.max(1,Math.ceil(rows.length/size));page=Math.max(0,Math.min(page,pages-1));
    const selected=section.querySelector('select').value;
    section.querySelector('.icon-results').textContent=`${rows.length.toLocaleString('de-DE')} Symbole · Seite ${page+1} von ${pages}`;
    section.querySelector('.icon-grid').innerHTML=rows.slice(page*size,(page+1)*size).map(row=>this._button('choose-icon',`<span>${escapeHTML(row[0])}</span>`,'mdi:'+row[0],`type="button" data-icon="mdi:${row[0]}" title="mdi:${row[0]}" aria-label="mdi:${row[0]} wählen" aria-pressed="${selected==='mdi:'+row[0]}"`)).join('')||'<p class="hint">Keine passenden Symbole gefunden.</p>';
    section.querySelector('.icon-pages').innerHTML=`${this._button('icon-page','Zurück',null,`type="button" data-page="${page-1}" ${page===0?'disabled':''}`)}${this._button('icon-page','Weiter',null,`type="button" data-page="${page+1}" ${page===pages-1?'disabled':''}`)}`;
  }
  _updateDeviceIconPreview(form){
    const preview=form?.querySelector('.image-preview');
    if(preview&&(!preview.querySelector('img')||this._imageRemoved))preview.innerHTML=icon(form.querySelector('[name=device_icon]').value);
  }
  _fileLoading(form,delta){
    form.dataset.loading=String(Math.max(0,Number(form.dataset.loading||0)+delta));
    const submit=form.querySelector('button[type=submit]');if(submit)submit.disabled=this._busy||Number(form.dataset.loading)>0;
  }
  _webUrl(t){return `${t.web_scheme||'http'}://${t.host.includes(':')?`[${t.host}]`:t.host}:${t.web_port||80}${t.web_path||'/'}`;}
  _sortRows(rows){
    const {sort_by,sort_desc}=this._data.settings;
    if(!sort_by||sort_by==='manual')return rows;
    return [...rows].sort((a,b)=>{
      let result;
      if(sort_by==='address')result=(a.address_sort_key||a.host).localeCompare(b.address_sort_key||b.host,'de',{numeric:true});
      else if(sort_by==='last_checked')result=(a.last_checked||0)-(b.last_checked||0);
      else if(sort_by==='status')result=['offline','error','unknown','paused','online'].indexOf(a.status)-['offline','error','unknown','paused','online'].indexOf(b.status);
      else result=a.name.localeCompare(b.name,'de',{numeric:true});
      return (sort_desc?-1:1)*result;
    });
  }
  _deviceImage(t){
    const image=this._images.get(t.image_id);
    return image?`<img src="${escapeHTML(image)}" width="300" height="300" alt="">`:icon(t.icon&&t.icon!=='auto'?t.icon:t.kind==='ddns'?'globe':'network');
  }
  async _loadImages(){
    const ids=[...new Set((this._data?.targets||[]).map(t=>t.image_id).filter(Boolean))];
    const pending=ids.filter(id=>!this._images.has(id)&&!this._imageLoading.has(id)).slice(0,8);
    if(!pending.length)return;
    pending.forEach(id=>this._imageLoading.add(id));
    await Promise.all(pending.map(async id=>{try{this._images.set(id,await this._hass.callWS({type:'ha_pinger/image',image_id:id}));}catch{this._images.set(id,'');}finally{this._imageLoading.delete(id);}}));
    if(this.isConnected)this.render();
  }
  async _uploadImage(input){
    const file=input.files?.[0], form=input.closest('form');
    if(!file)return;
    if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>10_000_000){this._showToast('Bitte PNG, JPEG oder WebP bis 10 MB wählen.');return;}
    this._fileLoading(form,1);
    try{
      const bitmap=await createImageBitmap(file);
      const canvas=document.createElement('canvas');canvas.width=300;canvas.height=300;
      const scale=Math.max(300/bitmap.width,300/bitmap.height);
      canvas.getContext('2d').drawImage(bitmap,(300-bitmap.width*scale)/2,(300-bitmap.height*scale)/2,bitmap.width*scale,bitmap.height*scale);bitmap.close();
      if(!form.isConnected)return;
      this._editImageData=canvas.toDataURL('image/png');this._imageRemoved=false;
      form.querySelector('.image-preview').innerHTML=`<img src="${this._editImageData}" alt="Bildvorschau">`;
    }catch{this._showToast('Dieses Bild konnte nicht gelesen werden.');}finally{this._fileLoading(form,-1);}
  }
  _syncRangeFields(){
    const form=this.shadowRoot.querySelector('form[data-form=target]');if(!form)return;
    const range=Boolean(form.querySelector('[name=use_range]')?.checked);
    form.querySelector('[name=name]').required=!range;
    for(const section of form.querySelectorAll('[data-address-mode]')){
      section.hidden=(section.dataset.addressMode==='range')!==range;
      section.querySelectorAll('input').forEach(input=>{input.disabled=section.hidden;});
    }
  }
  _targetFormData(form){
    const fields=new FormData(form);
    const data={name:fields.get('name'),kind:form.dataset.kind,method:fields.get('method'),group_id:fields.get('group_id'),network_id:fields.get('network_id'),icon:fields.get('device_icon'),interval_minutes:Number(fields.get('interval_minutes'))};
    for(const key of ['enabled','favorite','notify','notify_recovery','notify_dns'])data[key]=fields.has(key);
    if(data.method==='tcp')data.port=Number(fields.get('port'));
    if(['web','both'].includes(data.method))Object.assign(data,{web_scheme:fields.get('web_scheme'),web_port:Number(fields.get('web_port')),web_path:fields.get('web_path'),verify_tls:fields.has('verify_tls')});
    if(data.method==='both')data.availability_mode=fields.get('availability_mode');
    if(fields.has('use_range'))data.range=fields.get('range');
    else {data.host=fields.get('host');if(this._editImageData)data.image_data=this._editImageData;else if(this._imageRemoved)data.image_id='';}
    return data;
  }
  async _previewRange(){
    const form=this.shadowRoot.querySelector('form[data-form=target]');
    try{const result=await this._hass.callWS({type:'ha_pinger/command',action:'preview_range',data:this._targetFormData(form)});form.querySelector('.range-preview').textContent=`${result.count} neue Adressen · ${result.skipped} bereits vorhanden · ${result.first} bis ${result.last}`;}
    catch(error){form.querySelector('.range-preview').textContent=error.message||'Bereich ungültig.';}
  }
  _grouped(rows) {
    return [...(this._data.groups||[]),{id:'',name:'Ohne Gruppe',icon:'network'}]
      .map(group=>({...group,rows:rows.filter(t=>(t.group_id||'')===group.id)}));
  }
  _groupHeading(group) {
    return `<div class="group-heading"><div class="group-heading-title"><h3>${icon(group.icon)}${escapeHTML(group.name)}</h3>${group.ip_range?`<span class="group-heading-range mono" aria-label="IP-Bereich: ${escapeHTML(group.ip_range)}">${escapeHTML(group.ip_range)}</span>`:''}</div><span class="count">${group.rows.length}</span></div>`;
  }
  async _validateGroupRange(form) {
    if(!form?.isConnected)return false;
    const input=form.querySelector('[name=ip_range]'),feedback=form.querySelector('.group-range-feedback');
    const value=input.value.trim(),request=(input._rangeRequest||0)+1;input._rangeRequest=request;
    input.setCustomValidity('');input.removeAttribute('aria-invalid');feedback.className='group-range-feedback hint full';feedback.removeAttribute('aria-busy');
    if(!value){feedback.textContent='Optional: Ohne Bereich können beliebige IP-Adressen zugeordnet werden.';return true;}
    feedback.textContent='Bereich wird geprüft …';feedback.setAttribute('aria-busy','true');
    const current=()=>form.isConnected&&input.value.trim()===value&&input._rangeRequest===request;
    try {
      const result=await this._hass.callWS({type:'ha_pinger/command',action:'preview_group_range',data:{ip_range:value},...(form.dataset.id?{target_id:form.dataset.id}:{})});
      if(!current())return false;
      const outside=result.outside||[];
      let message=`Gültiger Bereich: ${result.range} · ${result.count} ${result.count===1?'Adresse':'Adressen'} (${result.first} bis ${result.last}).`;
      if(outside.length){
        message+=` ${outside.length} zugeordnete ${outside.length===1?'IP liegt':'IPs liegen'} außerhalb: ${outside.slice(0,5).map(t=>`${t.name} (${t.host})`).join(', ')}${outside.length>5?' …':''}. Diese Einträge bleiben erhalten.`;
        feedback.classList.add('warning');
      }else{if(result.inside_count)message+=` Alle ${result.inside_count} zugeordneten IPs liegen darin.`;feedback.classList.add('valid');}
      feedback.textContent=message;return true;
    } catch(error) {
      if(!current())return false;
      const message=error.message||'Bereich konnte nicht geprüft werden. Verbindung prüfen.';
      input.setCustomValidity(message);input.setAttribute('aria-invalid','true');feedback.classList.add('invalid');feedback.textContent=message;return false;
    } finally {if(current())feedback.removeAttribute('aria-busy');}
  }
  _checkBadges(t) {
    const names=t.method==='both'?['ping','web']:[t.method==='icmp'?'ping':t.method];
    return `<div class="check-badges">${names.map(name=>{
      const check=t.checks?.[name];
      const state=['unknown','paused'].includes(t.status)?t.status:check?.online===true?'online':check?.online===false?'offline':check?.error?'error':'unknown';
      const label=name==='ping'?'Ping':name==='web'?'Web':'TCP';
      return `<span class="check-badge ${state}" title="${escapeHTML(check?.error||check?.detail||statusLabel[state])}" aria-label="${label}: ${statusLabel[state]}">${icon(state==='online'?'check':state==='offline'?'cross':state==='error'?'shield':'clock')}${label}${name==='web'&&check?.http_status&&!['unknown','paused'].includes(t.status)?` ${check.http_status}`:''}</span>`;
    }).join('')}</div>`;
  }
  _syncMethodFields() {
    const form=this.shadowRoot.querySelector('form[data-form=target]');
    if(!form)return;
    const method=form.querySelector('[name=method]').value;
    form.querySelectorAll('[data-methods]').forEach(section=>{
      const show=section.dataset.methods.split(' ').includes(method);
      section.hidden=!show;
      section.querySelectorAll('input,select').forEach(input=>{input.disabled=!show;});
    });
  }
  _moveButtons(id,scope,index,total,name) {
    return [-1,1].map(direction=>this._button('move','',direction<0?'up':'down',
      `class="square quiet" data-id="${id}" data-scope="${scope}" data-direction="${direction}" aria-label="${escapeHTML(name)} nach ${direction<0?'oben':'unten'}" ${this._busy||!this._connected||!this._admin||(direction<0?index===0:index===total-1)?'disabled':''}`)).join('');
  }
  _organize() {
    const groups=this._grouped(this._data.targets.filter(t=>t.kind===this._tab&&(t.network_id||'')===this._network));
    this._dialog('Gruppen & Reihenfolge',`<p class="hint">Die Pfeile speichern sofort. Gruppen gelten für beide Tabs; Adressen verschiebst du innerhalb ihrer Gruppe und ihres Tabs. Die Gruppe einer Adresse wählst du beim Bearbeiten.</p>
      ${this._button('add-group','Gruppe hinzufügen','plus','class="primary"')}
      <div class="organizer">${groups.map((g,index)=>`<section class="organizer-group" data-group-id="${g.id}"><div class="organizer-heading"><h3>${icon(g.icon)}<span>${escapeHTML(g.name)}</span></h3>${g.id?`<div class="order-actions">${this._moveButtons(g.id,'groups',index,groups.length-1,g.name)}${this._button('edit-group','','edit',`class="square quiet" data-id="${g.id}" aria-label="Gruppe ${escapeHTML(g.name)} bearbeiten"`)}</div>`:''}</div>
      ${g.ip_range?`<div class="group-range"><p class="hint mono">${escapeHTML(g.ip_range)}</p>${this._button('group-range','Adressen aus Bereich hinzufügen','plus',`class="quiet" data-id="${g.id}" ${this._busy||!this._connected||!this._admin?'disabled':''}`)}</div>`:''}
      ${g.rows.map((t,i)=>`<div class="order-row" data-target-id="${t.id}"><div><strong>${escapeHTML(t.name)}</strong><small class="mono">${escapeHTML(t.host)}</small></div><div class="order-actions">${this._moveButtons(t.id,'targets',i,g.rows.length,t.name)}${this._button('edit','','edit',`class="square quiet" data-id="${t.id}" aria-label="${escapeHTML(t.name)} bearbeiten"`)}</div></div>`).join('')||'<p class="hint">In diesem Tab noch keine Adressen zugeordnet.</p>'}</section>`).join('')}</div>
      <div class="form-error" role="alert"></div><div class="dialog-foot"><div class="right">${this._button('close','Fertig',null,'class="primary"')}</div></div>`);
  }
  _editGroup(group) {
    const g=group||{name:'',icon:'network'};
    this._dialog(group?'Gruppe bearbeiten':'Gruppe hinzufügen',`<form data-form="group" data-id="${group?.id||''}"><div class="form-grid">
      <div class="full">${this._field('Gruppenname','name',g.name,'text','required maxlength="80" placeholder="z. B. Büro"')}</div>
      ${this._iconSelector('Gruppen-Icon','icon',g.icon,GROUP_ICONS)}<div class="icon-preview full">${icon(g.icon)}</div>
      <div class="full">${this._field('IP-Bereich der Gruppe · optional','ip_range',g.ip_range||'','text','maxlength="160" placeholder="192.168.1.10-192.168.1.30 oder 192.168.1.0/24"')}<p class="hint">Leer lassen oder bis zu 256 Adressen als Bereich / CIDR speichern. Danach kannst du über „Adressen aus Bereich hinzufügen“ die Prüfmethode wählen und die Einträge im aktiven Netz anlegen. Änderungen am Bereich behalten vorhandene Einträge.</p></div>
      <p class="group-range-feedback hint full" role="status" aria-live="polite"></p>
      </div><div class="form-error" role="alert"></div><div class="dialog-foot">${group?this._button('delete-group','Löschen',null,`type="button" class="danger" data-id="${g.id}"`):''}<div class="right">${this._button('organize','Zurück',null,'type="button" class="quiet"')}<button type="submit" class="primary">Speichern</button></div></div></form>`);
    this._validateGroupRange(this.shadowRoot.querySelector('form[data-form=group]'));
  }
  _deleteGroup(g) {
    this._dialog('Gruppe löschen?',`<p>Die Gruppe <strong>${escapeHTML(g.name)}</strong> wird gelöscht. Ihre Adressen und Verläufe bleiben erhalten und erscheinen unter „Ohne Gruppe“.</p><div class="form-error" role="alert"></div><div class="dialog-foot"><div class="right">${this._button('organize','Abbrechen',null,'class="quiet"')}${this._button('confirm-delete-group','Gruppe löschen',null,`class="danger" data-id="${g.id}"`)}</div></div>`);
  }
  _edit(target, defaults={}) {
    const t = {name:'',host:'',kind:this._tab,method:'icmp',port:443,interval_minutes:0,enabled:true,notify:false,notify_recovery:true,notify_dns:false,favorite:false,group_id:'',web_scheme:'http',web_port:80,web_path:'/',verify_tls:true,availability_mode:'any',icon:'auto',network_id:this._network,...defaults,...target};
    this._editImageData=null;this._imageRemoved=false;
    this._dialog(target?'Adresse bearbeiten':'Adresse hinzufügen',`<form data-form="target" data-id="${target?.id || ''}" data-kind="${t.kind}"><div class="form-grid">
      <div class="full">${this._field('Name','name',t.name,'text','required maxlength="80" placeholder="z. B. Büro-Switch"')}</div>
      ${!target&&t.kind==='ip'?`<div class="full">${this._checkbox('IP-Bereich hinzufügen','use_range',Boolean(defaults.range))}</div><div class="full" data-address-mode="range" hidden>${this._field('IP-Bereich / CIDR','range',defaults.range||'','text','required disabled placeholder="192.168.1.10-192.168.1.30 oder 192.168.1.0/24"')}<p class="hint">Alle Adressen im Bereich werden angelegt (max. 256). Der Name dient als Präfix. Vorhandene Einträge werden übersprungen.</p>${this._button('preview-range','Bereich prüfen','search','type="button"')}<p class="range-preview hint" role="status"></p></div>`:''}
      <div class="full" data-address-mode="single">${this._field(t.kind==='ddns'?'DDNS-Domain':'IP-Adresse','host',t.host,'text',`required maxlength="253" autocomplete="off" spellcheck="false" placeholder="${t.kind==='ddns'?'zuhause.example.org':'192.168.1.10'}"`)}</div>
      <label class="field full">Netz<select name="network_id" aria-label="Netz"><option value="">Heimnetz · Home Assistant</option>${(this._data.networks||[]).map(n=>`<option value="${n.id}" ${t.network_id===n.id?'selected':''}>${escapeHTML(n.name)}</option>`).join('')}</select></label>
      ${this._iconSelector('Symbol','device_icon',t.icon,TARGET_ICONS)}
      <div class="full image-editor" data-address-mode="single"><div class="image-preview">${this._deviceImage(t)}</div><div><label class="field">Eigenes Bild · 300 × 300<input type="file" name="device_image" accept="image/png,image/jpeg,image/webp"></label><p class="hint">Wird zentriert auf 300 × 300 Pixel zugeschnitten.</p>${this._button('remove-image','Bild entfernen','cross','type="button" class="quiet"')}</div></div>
      <label class="field full">Gruppe<select name="group_id" aria-label="Gruppe"><option value="">Ohne Gruppe</option>${(this._data.groups||[]).map(g=>`<option value="${g.id}" ${t.group_id===g.id?'selected':''}>${escapeHTML(g.name)}</option>`).join('')}</select></label>
      <label class="field full">Prüfmethode<select name="method" aria-label="Prüfmethode">${[['icmp','Ping (ICMP)'],['web','Web (HTTP / HTTPS)'],['both','Beides: Ping + Web'],...(t.method==='tcp'?[['tcp','TCP-Verbindung (bestehend)']]:[])].map(([value,label])=>`<option value="${value}" ${t.method===value?'selected':''}>${label}</option>`).join('')}</select></label>
      <div class="full" data-methods="tcp">${this._field('TCP-Port','port',t.port,'number','min="1" max="65535" required')}</div>
      <div class="full form-grid" data-methods="web both">
        <label class="field">Web-Protokoll<select name="web_scheme" aria-label="Web-Protokoll"><option value="http" ${t.web_scheme==='http'?'selected':''}>HTTP</option><option value="https" ${t.web_scheme==='https'?'selected':''}>HTTPS</option></select></label>
        ${this._field('Web-Port','web_port',t.web_port,'number','min="1" max="65535" required')}
        <div class="full">${this._field('Web-Pfad','web_path',t.web_path,'text','required maxlength="1024" placeholder="/"')}</div>
        <div class="full checks">${this._checkbox('HTTPS-Zertifikat prüfen','verify_tls',t.verify_tls)}</div>
        <p class="hint full">HTTP-Antworten zählen als erreichbar, auch Anmeldeseiten und Fehlerseiten. Inhalt und Weiterleitungsziel werden nicht geprüft. Bei einem eigenen HTTPS-Zertifikat kannst du die Zertifikatsprüfung ausschalten.</p>
      </div>
      <label class="field full" data-methods="both">Gerät gilt als erreichbar, wenn<select name="availability_mode" aria-label="Gerät gilt als erreichbar, wenn"><option value="any" ${t.availability_mode==='any'?'selected':''}>Mindestens eine Prüfung erfolgreich ist</option><option value="all" ${t.availability_mode==='all'?'selected':''}>Beide Prüfungen erfolgreich sind</option></select></label>
      <div class="full">${this._field('Eigenes Prüfintervall in Minuten (0 = Standard)','interval_minutes',t.interval_minutes,'number','min="0" max="1440" required')}</div>
      <div class="full checks">${this._checkbox('Überwachung aktiv','enabled',t.enabled)}${this._checkbox('Als Favorit anzeigen','favorite',t.favorite)}${this._checkbox('Push bei Ausfall','notify',t.notify)}${this._checkbox('Auch melden, wenn wieder erreichbar','notify_recovery',t.notify_recovery)}${t.kind==='ddns'?this._checkbox('Auch bei Änderung der DNS-Adressen melden','notify_dns',t.notify_dns):''}</div>
      </div><p class="hint">Ausfallmeldungen werden nach der eingestellten Wartezeit einmal gesendet. Für alle Push-Meldungen muss die Glocke aktiviert und ein Handy in den Einstellungen ausgewählt sein.</p><div class="form-error" role="alert"></div><div class="dialog-foot">${target?this._button('delete','Löschen',null,`class="danger" type="button" data-id="${t.id}"`):''}<div class="right">${this._button('close','Abbrechen',null,'type="button" class="quiet"')}<button class="primary" type="submit">Speichern</button></div></div></form>`);
    this._syncMethodFields();
    this._syncRangeFields();
  }
  _settings() {
    const s=this._data.settings;
    const services=[...new Set([...this._data.notify_services,...(s.notify_service?[s.notify_service]:[])])];
    this._dialog('Überwachung einstellen',`<form data-form="settings"><div class="form-grid">
      ${this._field('Prüfintervall · Minuten','interval_minutes',s.interval_minutes,'number','required min="1" max="1440"')}
      ${this._field('Ausfallmeldung nach · Sekunden','offline_after_seconds',s.offline_after_seconds,'number','required min="0" max="86400"')}
      ${this._field('Timeout je Versuch · Sekunden','timeout_seconds',s.timeout_seconds,'number','required min="1" max="10"')}
      ${this._field('Versuche je Prüfung','attempts',s.attempts,'number','required min="1" max="5"')}
      <label class="field full">Push an dieses Handy<select name="notify_service" aria-label="Push an dieses Handy"><option value="">Kein Handy ausgewählt</option>${services.map(service=>`<option value="${escapeHTML(service)}" ${service===s.notify_service?'selected':''}>${escapeHTML(service.replace('notify.mobile_app_','').replaceAll('_',' '))}</option>`).join('')}</select></label></div>
      <p class="hint">${services.length?'':'Noch kein Handy gefunden? Richte die Home-Assistant-Companion-App ein und erlaube Mitteilungen. '}Bei 0 Sekunden kommt der Push nach der ersten fehlgeschlagenen Prüfung. Die Wartezeit beginnt beim erkannten Ausfall und läuft unabhängig vom Prüfintervall. Frühere Minutenwerte wurden in Sekunden umgerechnet.</p>
      ${this._button('test-notify','Gespeichertes Handy testen','bell',`type="button" class="quiet" ${!s.notify_service?'disabled':''}`)}<div class="form-error" role="alert"></div><div class="dialog-foot"><div class="right">${this._button('close','Abbrechen',null,'type="button" class="quiet"')}<button class="primary" type="submit">Speichern</button></div></div></form>`);
  }
  async _details(t) {
    if(!t) return;
    this._dialog(t.name,`${this._badge(t)}<dl class="help-grid" style="margin-top:20px">
      ${[['Adresse',t.host],['Prüfung',t.method==='tcp'?`TCP auf Port ${t.port}`:methodLabel[t.method]],...(t.method==='both'?[['Erreichbar, wenn',t.availability_mode==='all'?'Beide Prüfungen erfolgreich sind':'Mindestens eine Prüfung erfolgreich ist']]:[]),['Prüfintervall',`${t.interval_minutes || this._data.settings.interval_minutes} Minuten`],['Letzte Prüfung',date(t.last_checked)],['Zuletzt erreichbar',date(t.last_online)],['Antwortzeit',`${number(t.latency_ms)} ms`],['Aufgelöste IP-Adressen',t.resolved_ips.join(', ')||'—'],['Erfolgreiche Prüfungen',`${number(t.availability)} % der letzten ${t.history.length} Prüfungen`]].map(([label,value])=>`<div><dt>${label}</dt><dd>${escapeHTML(value)}</dd></div>`).join('')}</dl>
      ${this._checkBadges(t)}${Object.entries(t.checks||{}).map(([name,result])=>`<div class="probe-detail"><strong>${name==='ping'?'Ping':name==='web'?'Web':'TCP'}${result.latency_ms!=null?` · ${number(result.latency_ms)} ms`:''}</strong>${result.url?`<p class="mono">${escapeHTML(result.url)}</p>`:''}<p>${escapeHTML(result.error||result.detail||(result.online?'Erreichbar':'Keine Antwort'))}</p></div>`).join('')}
      ${t.error?`<div class="banner">${escapeHTML(t.error)}</div>`:''}${!Object.keys(t.checks||{}).length&&t.detail?`<p class="hint">${escapeHTML(t.detail)}</p>`:''}${t.notification_error?`<div class="banner">${escapeHTML(t.notification_error)}</div>`:''}
      <p class="hint push-status">${icon('bell')} ${escapeHTML(t.notification_status||'')}${t.last_notification?` · Letzter Push-Aufruf: ${date(t.last_notification)}`:''}</p>
      <div class="detail-history"><h3>Letzte 30 Tage</h3><div id="long-history"><p class="hint">Verlauf wird geladen …</p></div></div><div class="form-error" role="alert"></div>
      <div class="info-actions">${this._button('check-one','Jetzt prüfen','refresh',`data-id="${t.id}" ${!this._admin||!t.enabled||t.checking||this._manualChecks.has(t.id)?'disabled':''}`)}${this._button('log','Protokoll','clock',`data-id="${t.id}"`)}${this._button('edit','Bearbeiten','edit',`data-id="${t.id}" ${!this._admin?'disabled':''}`)}</div>`);
    this.shadowRoot.querySelector('dialog').dataset.detailId = t.id;
    this.shadowRoot.querySelector('dialog').classList.add('wide');
    try{const data=await this._hass.callWS({type:'ha_pinger/history',target_id:t.id});if(this.shadowRoot.querySelector('dialog').dataset.detailId===t.id)this.shadowRoot.querySelector('#long-history').innerHTML=this._timeline(t,data);}
    catch(error){if(this.shadowRoot.querySelector('#long-history'))this.shadowRoot.querySelector('#long-history').textContent=error.message||'Verlauf konnte nicht geladen werden.';}
  }
  _timeline(t,data){
    const today=new Date((data.now||Date.now()/1000)*1000);today.setHours(0,0,0,0);
    const days=[];
    const state=bits=>bits&2?'down':bits&4?'error':bits&1?'up':'unknown';
    const label=bits=>bits&2?'Mindestens eine Prüfung ohne Antwort':bits&4?'Technischer Prüffehler':bits&1?'Prüfung erfolgreich':'Keine Messung';
    for(let ago=29;ago>=0;ago--){
      const start=new Date(today);start.setDate(start.getDate()-ago);
      const end=new Date(start);end.setDate(end.getDate()+1);
      const cells=[];
      for(let second=start.getTime()/1000;second<end.getTime()/1000;second+=1800){
        let bits=0;
        for(let stamp=second;stamp<second+1800;stamp+=300){const day=Math.floor(stamp/86400)*86400;bits|=parseInt(data.timeline?.[String(day)]?.[Math.floor((stamp-day)/300)]||'0',16);}
        cells.push(`<button type="button" class="timeline-bin ${state(bits)}" data-action="time-slot" data-id="${t.id}" data-start="${second}" data-end="${second+1800}" title="${label(bits)}" aria-label="${escapeHTML(date(second))}: ${label(bits)}"></button>`);
      }
      days.push(`<div class="timeline-day"><time>${start.toLocaleDateString('de-DE',{day:'2-digit',month:'2-digit'})}</time><div class="timeline-bars" style="--cells:${cells.length}">${cells.join('')}</div></div>`);
    }
    return `<p class="hint">Jede Zeile ist ein Tag, jeder Strich 30 Minuten. Ein roter Strich enthält mindestens eine fehlgeschlagene Prüfung. Grau bedeutet keine Messung. Tippe einen Strich für den Zeitraum an.</p><div class="timeline-axis"><span>00 Uhr</span><span>06</span><span>12</span><span>18</span><span>24</span></div>${days.join('')}<p class="hint">Die letzten 30 Tage werden ab tatsächlichen Prüfungen aufgebaut. Kurze Ausfälle zwischen zwei Prüfungen können unbemerkt bleiben.</p>`;
  }
  async _log(t){
    this._dialog(`Protokoll · ${t.name}`,`<div id="device-log"><p class="hint">Protokoll wird geladen …</p></div><div class="form-error"></div><div class="dialog-foot">${this._button('details','Verlauf','pulse',`data-id="${t.id}"`)}${this._button('clear-log','Protokoll leeren',null,`class="danger" data-id="${t.id}" ${!this._admin?'disabled':''}`)}</div>`);
    const dialog=this.shadowRoot.querySelector('dialog');dialog.classList.add('wide');dialog.dataset.logId=t.id;
    try{const data=await this._hass.callWS({type:'ha_pinger/history',target_id:t.id});const box=this.shadowRoot.querySelector('#device-log');if(!box||dialog.dataset.logId!==t.id)return;
      box.innerHTML=`<p class="hint">Statuswechsel, Prüffehler und Push-Aufrufe · bis zu 30 Tage, maximal 2.000 Einträge.</p>${data.log.length?`<div class="log-list">${[...data.log].reverse().map(e=>`<article class="log-entry ${escapeHTML(e.kind)}"><time>${escapeHTML(date(e.time))}</time><p>${escapeHTML(e.message)}</p></article>`).join('')}</div>`:'<p class="hint">Noch keine Protokolleinträge.</p>'}`;
    }catch(error){const box=this.shadowRoot.querySelector('#device-log');if(box)box.textContent=error.message||'Protokoll nicht verfügbar.';}
  }
  _networks(){
    const active=this._data.active_network||'';
    const networks=[{id:'',name:'Heimnetz'},...(this._data.networks||[])];
    this._dialog('Netze & WireGuard',`<p class="hint">Wähle das Netz, das du prüfen möchtest. Beim Wechsel wird dessen WireGuard-Tunnel aktiviert. Im Heimnetz ist der Tunnel ausgeschaltet. Die Auswahl gilt für alle Ansichten dieses Control Centers.</p>
      <div class="info-actions">${this._button('agent-settings','App verbinden','settings')}${this._button('test-agent','Verbindung testen','refresh')}${this._button('new-network','Netz hinzufügen','plus','class="primary"')}</div>
      <div class="network-list">${networks.map(n=>`<div class="order-row network-choice"><div><strong>${escapeHTML(n.name)}</strong><small>${this._data.targets.filter(t=>(t.network_id||'')===n.id).length} Adressen · ${n.id===active?'Aktiv':n.id?'Tunnel ausgeschaltet':'Nicht ausgewählt'}</small></div><div class="network-choice-actions">${this._button('select-network',n.id===active?'Aktiv':'Aktivieren',n.id===active?'check':'arrow',`data-id="${n.id}" aria-label="${escapeHTML(n.name)} aktivieren" ${n.id===active?'disabled':''}`)}${n.id?`${this._button('edit-network','','edit',`class="square quiet" data-id="${n.id}" aria-label="Netz ${escapeHTML(n.name)} bearbeiten"`)}${this._button('delete-network','','cross',`class="square quiet" data-id="${n.id}" aria-label="Netz ${escapeHTML(n.name)} löschen" ${n.id===active?'disabled':''}`)}`:''}</div></div>`).join('')}</div>
      ${this._data.vpn?.error?`<div class="banner">${escapeHTML(this._data.vpn.error)}</div>`:''}
      <p class="hint">Nur das aktive Netz wird geprüft. Die Prüfungen anderer Netze und ihre Ausfalltimer pausieren. HA behält seine eigene Netzwerkverbindung. Zum Öffnen einer entfernten Weboberfläche benötigt dein Browser selbst Zugang zum Zielnetz.</p><div class="form-error"></div>`);
  }
  _agentSettings(){
    const vpn=this._data.vpn||{};
    this._dialog('WireGuard-App verbinden',`<form data-form="agent"><p class="hint">Installiere zunächst die mitgelieferte lokale App „Network Control Center WireGuard“. Trage dort unter api_token denselben Zugriffsschlüssel ein wie hier. Die App benötigt keinen Zugriff auf HA-Routen und keine privilegierten Netzwerkrechte.</p><div class="form-grid"><div class="full">${this._field('App-Adresse','agent_url',vpn.agent_url||'http://local-ncc-vpn:8099','url','required')}</div><div class="full">${this._field('Zugriffsschlüssel','agent_token','','password',`autocomplete="new-password" minlength="32" maxlength="256" placeholder="${vpn.token_set?'Gespeichert · leer lassen zum Beibehalten':'Mindestens 32 Zeichen'}"`)}</div></div><div class="info-actions">${this._button('generate-token','Schlüssel erzeugen','shield','type="button"')}${this._button('copy-token','Kopieren',null,'type="button"')}</div><div class="form-error"></div><div class="dialog-foot">${this._button('networks','Zurück',null,'type="button"')}<button type="submit" class="primary">Speichern</button></div></form>`);
  }
  _editNetwork(network){
    this._wireguardConfig='';
    this._dialog(network?'Netz bearbeiten':'WireGuard-Netz hinzufügen',`<form data-form="network" data-id="${network?.id||''}"><div class="form-grid"><div class="full">${this._field('Netzname','name',network?.name||'','text','required maxlength="80" placeholder="z. B. Büro oder Ferienhaus"')}</div><label class="field full">WireGuard-Konfiguration<input type="file" name="wireguard_file" accept=".conf,.txt" ${network?'':'required'}></label></div><p class="hint">Standard-WireGuard-Datei bis 32 KB. Schlüssel werden in der separaten App gespeichert. Skript-Hooks wie PostUp werden nicht ausgeführt. ${network?'Ohne neue Datei bleibt die bisherige Konfiguration erhalten.':''}</p><div class="form-error"></div><div class="dialog-foot">${this._button('networks','Abbrechen',null,'type="button"')}<button type="submit" class="primary">Speichern</button></div></form>`);
  }
  async _readWireGuard(input){
    const file=input.files?.[0],form=input.closest('form');this._wireguardConfig='';if(!file)return;
    if(file.size>32768){input.value='';this._showToast('Konfigurationsdatei ist größer als 32 KB.');return;}
    this._fileLoading(form,1);
    try{const value=await file.text();if(form.isConnected)this._wireguardConfig=value;}
    catch{input.value='';this._showToast('Konfigurationsdatei konnte nicht gelesen werden.');}
    finally{this._fileLoading(form,-1);}
  }
  _delete(t) {
    this._dialog('Adresse löschen?',`<p><strong>${escapeHTML(t.name)}</strong> (${escapeHTML(t.host)}) wird aus der Überwachung entfernt.</p><p class="hint">Der lokale Prüfverlauf dieser Adresse wird ebenfalls entfernt. Du kannst die Adresse später erneut hinzufügen.</p><div class="form-error" role="alert"></div><div class="dialog-foot"><div class="right">${this._button('close','Abbrechen',null,'class="quiet"')}${this._button('confirm-delete','Adresse löschen',null,`class="danger" data-id="${t.id}"`)}</div></div>`);
  }
  async _submit(event) {
    const form=event.target;
    if(!form.dataset.form) return;
    event.preventDefault();
    if(form.dataset.form==='group') {
      if(form.dataset.validating)return;
      clearTimeout(this._groupRangeTimer);form.dataset.validating='true';
      const submit=form.querySelector('button[type=submit]');submit.disabled=true;
      const valid=await this._validateGroupRange(form);
      delete form.dataset.validating;submit.disabled=this._busy;
      if(!valid||!form.isConnected)return;
    }
    const fields=new FormData(form);
    let data,action;
    if(form.dataset.form==='settings') {
      action='settings'; data={};
      for(const key of ['interval_minutes','offline_after_seconds','timeout_seconds','attempts']) data[key]=Number(fields.get(key));
      data.notify_service=fields.get('notify_service');
    } else if(form.dataset.form==='group') {
      action='save_group';data={name:fields.get('name'),icon:fields.get('icon'),ip_range:fields.get('ip_range')};
    } else if(form.dataset.form==='agent') {
      action='agent_settings';data={agent_url:fields.get('agent_url'),agent_token:fields.get('agent_token')};
    } else if(form.dataset.form==='network') {
      action='save_network';data={name:fields.get('name'),config:this._wireguardConfig||''};
    } else {
      action=fields.has('use_range')?'add_range':'save';data=this._targetFormData(form);
    }
    if(await this._command(action,data,form.dataset.id||undefined)) {
      if(action==='save_group')this._organize();else if(['agent_settings','save_network'].includes(action))this._networks();else this.shadowRoot.querySelector('dialog').close();
      this._showToast('Einstellungen gespeichert.');
    }
  }
}

class PingerCard extends NetworkElement {}
class PingerPanel extends NetworkElement {}
if(!customElements.get('ha-pinger-card')) customElements.define('ha-pinger-card',PingerCard);
if(!customElements.get('ha-pinger-panel')) customElements.define('ha-pinger-panel',PingerPanel);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==='ha-pinger-card')) window.customCards.push({type:'ha-pinger-card',name:'Network Control Center',description:'Netzwerkstatus, Favoriten und direkter Zugriff auf das Control Center.',preview:true});
