"""Kerangka verifikasi UI di Chrome headless (CDP) memakai SALINAN DB. Produksi tidak disentuh.

Pemakaian: salin ke /tmp/verif_x.py, ubah PORT/CDP unik, isi blok "SKENARIO", jalankan `python3 /tmp/verif_x.py`.
Prasyarat: websocket-client (python3), google-chrome-stable, artisan serve port uji.
Catat `md5sum database/database.sqlite` sebelum/sesudah; selalu bersihkan proses (blok finally).
Jangan menaruh '&' di heredoc foreground (ditolak terminal): simpan lewat write_file lalu jalankan.
"""
import json, os, shutil, sqlite3, subprocess, time, urllib.request, base64
import websocket

APP = '/home/ubuntu/PWA_Bruder-Muda'; PORT = 18950; CDP = 19550
BASE = f'http://127.0.0.1:{PORT}'; W = '/tmp/verif_tpl'
shutil.rmtree(W, ignore_errors=True)
for d in ('storage/framework/sessions', 'storage/framework/views', 'storage/framework/cache/data', 'storage/logs', 'storage/app/public'):
    os.makedirs(f'{W}/{d}')
shutil.copy(f'{APP}/database/database.sqlite', f'{W}/db.sqlite')
c = sqlite3.connect(f'{W}/db.sqlite')
h = subprocess.run(['php', '-r', 'echo password_hash("uji12345", PASSWORD_BCRYPT, ["cost"=>10]);'], capture_output=True, text=True).stdout
c.execute('update users set password=?', (h,))          # sandi uji hanya di SALINAN
def akun(role): return c.execute("select username from users where role=? and is_active=1 and deleted_at is null order by id limit 1", (role,)).fetchone()[0]
BR, AD, SA = akun('user'), akun('admin'), akun('super_admin')
c.commit(); c.close()

env = dict(os.environ, DB_DATABASE=f'{W}/db.sqlite', LARAVEL_STORAGE_PATH=f'{W}/storage', APP_URL=BASE,
           SESSION_SECURE_COOKIE='false', SESSION_DRIVER='file', CACHE_STORE='file')
srv = subprocess.Popen(['php', 'artisan', 'serve', '--host=127.0.0.1', f'--port={PORT}', '--no-reload'], cwd=APP, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
chrome = None; hasil = []
try:
    for _ in range(40):
        try: urllib.request.urlopen(BASE + '/login', timeout=2); break
        except Exception: time.sleep(.5)
    chrome = subprocess.Popen(['google-chrome-stable', '--headless=new', '--no-sandbox', '--disable-gpu', f'--remote-debugging-port={CDP}',
                               f'--user-data-dir={W}/chrome', '--window-size=412,900', 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{CDP}/json'))
    ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'], timeout=60)
    n = [0]
    def cmd(m, **p):
        n[0] += 1; ws.send(json.dumps({'id': n[0], 'method': m, 'params': p}))
        while True:
            r = json.loads(ws.recv())
            if r.get('id') == n[0]: return r.get('result', {})
    def js(e): return cmd('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True).get('result', {}).get('value')
    def go(p, w=2.2): cmd('Page.navigate', url=BASE + p); time.sleep(w)
    def login(u):
        cmd('Network.clearBrowserCookies'); go('/login')
        js(f"""(()=>{{const f=document.querySelector('form');f.querySelector('[name=username]').value={json.dumps(u)};f.querySelector('input[type=password]').value='uji12345';f.submit();}})()""")
        time.sleep(3)
    def cek(nama, ok, d=''):
        hasil.append(bool(ok)); print(('LULUS  ' if ok else 'GAGAL  ') + nama + (f'  [{d}]' if d else ''))
    def foto(nama, tinggi=1300, skala=1.4):
        open(f'{W}/{nama}.png', 'wb').write(base64.b64decode(cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
             clip={'x': 0, 'y': 0, 'width': 412, 'height': tinggi, 'scale': skala})['data']))
    cmd('Page.enable'); cmd('Runtime.enable'); cmd('Network.enable')
    cmd('Emulation.setDeviceMetricsOverride', width=412, height=900, deviceScaleFactor=2, mobile=True)

    # ===================== SKENARIO (isi di sini) =====================
    login(BR); go('/dashboard')
    cek('contoh: beranda bruder terbuka', 'STATISTIK PEMBINAAN' in (js('document.body.innerText') or '').upper())  # innerText mengikuti CSS uppercase
    # tips: bandingkan teks dengan .upper()/.lower(); hitung elemen dengan selector; ukur getBoundingClientRect untuk tata letak
    # tips: uji 403 dengan fetch POST + token CSRF SAH (ambil input[name=_token] dari form halaman lain); token palsu = 419 menyamarkan hasil
    # tips: layar sempit -> setDeviceMetricsOverride width=320 lalu cek scrollWidth > clientWidth
    # ==================================================================
finally:
    for p in (chrome, srv):
        if p: p.terminate()
    time.sleep(1); print(f'\nRINGKASAN: {sum(hasil)}/{len(hasil)} lulus')
