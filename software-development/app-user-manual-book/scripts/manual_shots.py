"""Kerangka tangkapan layar manual book. Salinan DB + data DISAMARKAN. Produksi tidak disentuh.
Sesuaikan: APP, tabel/kolom penyamaran, daftar halaman, daftar ASLI (nama asli yang tidak boleh muncul).
Butuh: websocket-client, google-chrome-stable."""
import base64, json, os, shutil, sqlite3, subprocess, time, urllib.request
import websocket

APP = '/home/ubuntu/PWA_Bruder-Muda'
PORT = 18400
BASE = f'http://127.0.0.1:{PORT}'
W = '/tmp/manual'; OUT = f'{W}/shots'
shutil.rmtree(W, ignore_errors=True)
for d in ('shots', 'storage/framework/sessions', 'storage/framework/views', 'storage/framework/cache/data', 'storage/logs', 'storage/app/public'):
    os.makedirs(f'{W}/{d}')
shutil.copy(f'{APP}/database/database.sqlite', f'{W}/db.sqlite')

c = sqlite3.connect(f'{W}/db.sqlite')
# --- samarkan (contoh; tambahkan tabel lain: pesan, catatan, sapaan author_name, formation_data, jurnal speaker) ---
ids = [r[0] for r in c.execute("select id from users where role='user' and is_active=1 and deleted_at is null order by id")]
for i, uid in enumerate(ids):
    c.execute("update users set name=?, username=?, email=?, phone=NULL, profile_photo=NULL where id=?",
              (f'Br. Contoh {i+1}, FIC', f'bruder.contoh{i+1:02d}', f'contoh{i+1:02d}@contoh.test', uid))
c.execute("update users set username='tmp_'||id where role!='user'")  # hindari UNIQUE bentrok
# ... isi ulang super_admin / admin, lalu soft-delete sisa 'tmp_%'
h = subprocess.run(['php', '-r', 'echo password_hash("manual123", PASSWORD_BCRYPT, ["cost"=>10]);'], capture_output=True, text=True).stdout
c.execute('update users set password=?', (h,)); c.commit()
BR = c.execute("select username from users where role='user' and is_active=1 and deleted_at is null order by id limit 1").fetchone()[0]
c.close()

env = dict(os.environ, DB_DATABASE=f'{W}/db.sqlite', LARAVEL_STORAGE_PATH=f'{W}/storage', APP_URL=BASE,
           SESSION_SECURE_COOKIE='false', SESSION_DRIVER='file', CACHE_STORE='file', PHP_CLI_SERVER_WORKERS='4')
srv = subprocess.Popen(['php', 'artisan', 'serve', '--host=127.0.0.1', f'--port={PORT}', '--no-reload'], cwd=APP, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
chrome = None
try:
    for _ in range(40):
        try: urllib.request.urlopen(BASE + '/login', timeout=2); break
        except Exception: time.sleep(.5)
    chrome = subprocess.Popen(['google-chrome-stable', '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                               '--remote-debugging-port=19460', f'--user-data-dir={W}/chrome', 'about:blank'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:19460/json'))
    ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'], timeout=60)
    n = [0]
    def cmd(m, **p):
        n[0] += 1; ws.send(json.dumps({'id': n[0], 'method': m, 'params': p}))
        while True:
            r = json.loads(ws.recv())
            if r.get('id') == n[0]: return r.get('result', {})
    def js(e): return cmd('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True).get('result', {}).get('value')
    def go(path, w=2.2): cmd('Page.navigate', url=BASE + path); time.sleep(w)

    ASLI = ['NamaAsli1', 'NamaAsli2']   # isi dengan nama nyata yang tidak boleh muncul
    BOCOR = []
    def shot(name, full=False, h=None):
        t = js("document.body.innerText + ' ' + [...document.querySelectorAll('input,textarea')].map(e=>e.value).join(' ')") or ''
        BOCOR.extend((name, k) for k in ASLI if k.lower() in t.lower())
        hh = min(int(js('document.documentElement.scrollHeight') or 900), h or 2600) if full else 900
        cmd('Emulation.setDeviceMetricsOverride', width=430, height=hh, deviceScaleFactor=2, mobile=True); time.sleep(.5)
        open(f'{OUT}/{name}.png', 'wb').write(base64.b64decode(cmd('Page.captureScreenshot', format='png')['data']))
    def login(user):
        cmd('Network.clearBrowserCookies'); go('/login')
        js(f"(()=>{{const f=document.querySelector('form'); f.querySelector('[name=username]').value={json.dumps(user)};"
           "f.querySelector('input[type=password]').value='manual123'; f.submit();}})()"); time.sleep(3)
    cmd('Page.enable'); cmd('Runtime.enable'); cmd('Network.enable')
    go('/login'); shot('01-login')
    login(BR); go('/dashboard'); shot('02-beranda', full=True, h=1900)
    # ... tambah halaman lain
    print('KEBOCORAN NAMA ASLI:', BOCOR)
finally:
    for p in (chrome, srv):
        if p: p.terminate()
