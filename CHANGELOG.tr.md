<div align="right">
  <b>Türkçe</b> · <a href="./CHANGELOG.md">English</a>
</div>

# Değişiklik günlüğü

## v1.2.0 — Güvenlik güncellemesi

**Güncellemeniz önerilir.** Bu sürüm komut, yazma ve site kapılarını sıkılaştırır. Aynı sınama girdilerinde komut
kapısının sessiz kaldığı kabuk komutu 72'de 68'den 72'de 7'ye indi; en yavaş kapı kararı 123 sn'den 1 sn'nin altına
indi.

### Ne değişti

**Tek savunma kümesi.** `common.DEFENSE_SET` kapıların dayandığı dosyaları sayar: Claude Code, Codex CLI, Gemini CLI
ve Antigravity'nin hook ve izin ayarları, vault'un `.claude/settings*.json` dosyaları, her `.claude/launch.json`,
global ve kurulu talimatlar, öbür asistanların talimat dosyaları, zamanlanmış görevler, `_system/` içindeki vault
betikleri ve `config.json`, ajan tanımları (vault ve her asistan), git kancaları, kara liste, kurallar, talimatların
asıl kopyası ve vault şeması. Yazma kapısı da komut kapısı da buradan okur.

**Komut kapısı**
- Savunma dosyasına kabukla yazma sorulur (yönlendirme, `sed -i`, `tee`, `Set-Content`, kopyalama ve taşıma hedefi,
  dosyayı yazmak için açan Python kodu, vault'un kendi `_system/` betiği olmayan bir Python betiğine argüman olarak
  verilen savunma yolu). Okumak, vault betiği çalıştırmak, `git add` ve `git commit` sessiz kalır.
- Kabuktan ağa çıkış sorulur, gerekçede adres görünür: `curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod`,
  `Start-BitsTransfer`, `certutil -urlcache`; `nc`, `telnet`, `ssh`, `sftp`, `ftp`; uzak yollu `scp` ve `rsync`;
  .NET ağ sınıfları; node, deno ya da bun'a verilen ağ kodu; Python ağ modülleri ve indirme aracı geçen
  `os.system`/`subprocess` çağrıları; tarayıcıda adres açma; `git clone`, `git remote add/set-url`, adresli
  `git pull/push/fetch`; `gh api`.
- İndirileni yorumlayıcıya bağlamak reddedilir; borunun arasına başka komut girse de, yorumlayıcı stdin'den okusa da
  (`| py -`), süreç ikamesiyle (`bash <(curl …)`) ve çözülen base64'le de.
- Gizlenmiş komut adları açılır: ada serpiştirilmiş tırnak ya da ters bölü (`"r""m"`, `c''url`, `r\m`), öndeki
  atamalar ve önekler (`HUSKY=0`, `command`, `env`, `sudo -E`, `nohup`). `$(…)` ya da ters tırnakla hesaplanan ad
  sorulur. `eval "…"` ve `Start-Process … -ArgumentList '…'` içindeki komutlar da öbürleri gibi denetlenir.
- 20.000 karakteri geçen komut, hiçbir desen çalışmadan sorulur; kayıtsız sohbette reddedilir. Dakikalarca geri izleyen
  desenler yeniden yazıldı.
- Commit kancasını atlama (`--no-verify`, `-n`, `core.hooksPath`) sorulur.
- Daha fazla silme sorulur: `Clear-Content`, `: > dosya`, `truncate`, `$_.Delete()`, `git checkout -- <yol>`,
  `git restore <yol>`, `git worktree remove`, `robocopy /purge`, `rsync --delete`, `tar --remove-files`, `eval`,
  hedefi önde yazılmış `Remove-Item <hedef> -Recurse`, Python `os.replace`/`shutil.move`.
- Süreç öldürmenin başka yolları reddedilir: `kill $(pgrep …)`, `… | xargs kill`, `spps -Name`, `.Kill()`, WMI ve CIM.
- Sır gösteren komutlar sorulur: `gh auth token`, `git credential`, `cmdkey`, bütün ortamı basma, adı sır gibi olan
  değişkeni basma, jokerle eşleşen sır dosyası.
- Kalıcılık ve yürütme politikası sorulur: `reg add`, Run anahtarı, `Set-ExecutionPolicy`, `-ExecutionPolicy Bypass`,
  `setx`, `git push +ref`.
- Paket kurulumu sorulur (`pip`, `pipx`, `uv`, `npm`, `pnpm`, `yarn`, `bun`, `winget`, `choco`, `scoop`).
- Yama uygulama (`git apply`, `git am`) ve vault dosyasını geçici klasöre taşıma sorulur.
- Terminal aracı (`mcp__terminal__run_in_terminal`) Bash ve PowerShell gibi denetlenir.
- Kapı yardımcı modüllerini yükleyemezse çökmek yerine sorar (öbür asistanlarda reddeder).

**Yazma kapısı**
- Savunma dosyasını değiştirmek sorulur (asistan soramıyorsa reddedilir); gerekçe hangi savunma olduğunu söyler.
- `_system/` altına standart kütüphane modülü adıyla dosya (`json.py`, `re.pyc`, `json/` klasörü) yazılması reddedilir.
- Kapı yardımcı modüllerini yükleyemezse sorar (öbür asistanlarda reddeder).

**Site kapısı**
- `WebSearch` bir sayfa gibi sorulur; gerekçede sorgu görünür.
- Kesin saldırı izi bilinen bir siteyi ya da çok kullanıcılı barındırmayı (`github.io`, `pages.dev`, `medium.com` …)
  artık kara listeye kendiliğinden yazmaz: tek bir sayfa bütün siteyi kalıcı engellemesin; karar kullanıcının.
- Yardımcı modül yüklenemezse kara liste reddi dışındaki her karar sorulur, kara listeye hiçbir şey yazılmaz.

**Bütün kapılar** kendi klasörlerini içe aktarma yolunun sonuna koyar; `_system/` içindeki bir dosya standart
kütüphaneyi gölgeleyemez. `hook_io.py` yalnızca standart kütüphaneye dayanır; başka bir yardımcı bozuk olsa da cevap
verebilir.

**Sağlık denetimi** (`health.py`): güvenlik hook'ları ve eşleştiricileri (komut kapısı için terminal aracı, site
kapısı için `WebSearch`), ayar dosyalarındaki geniş izin kalıpları, standart kütüphane adlı betik, kapı betiklerinde
commit edilmemiş değişiklik, commit kancasının bütünlüğü (`core.hooksPath`, sır taraması).

**Kurucu**: Claude Code hook şablonu komut kapısının eşleştiricisine `mcp__terminal__run_in_terminal`, site
kapısınınkine `WebSearch` ekler.

**Kurallar**: #28 ajanın kullanıcıya nasıl anılacağını söyler: rolü, modeli ve eforuyla, örneğin
"Yazılımcı Agent (Opus 5.5, Yüksek) yaptı".

### Fark edecekleriniz

`pip install`, `npm install`, `curl` ve `git clone` artık sorulur. `_system/config.json`, bir kapı betiği, bir ajan
tanımı ya da kurallar dosyasını düzenlemek sorulur. Web araması sorulur.

### Nasıl güncellenir

Kurucu var olan dosyaların üzerine yazmaz; var olan kurulum elle güncellenir:

1. v1.2.0'ı alın (Mindgate klasörünüzde `git pull` ya da sürümü indirin).
2. Claude Code'u kapatın. Sürümdeki bütün `vault/_system/*.py` dosyalarını vault'unuzun `_system/` klasörüne
   (Türkçe kurulumda `_sistem/`; betik adları iki dilde de aynı) kopyalayın. Oturum içinde yazma kapısı her dosya
   için sorar; bu bilerek böyle.
3. `~/.claude/settings.json` içinde var olan Mindgate hook'larına iki araç adını ekleyin: komut kapısının
   eşleştiricisi `Bash|PowerShell|mcp__terminal__run_in_terminal` olur, site kapısının PreToolUse eşleştiricisi
   `WebFetch|WebSearch|` ile başlar. Kaldırıp yeniden kurmak da aynısını yapar.
4. İsteğe bağlı: #28'in yeni metnini `locales/tr/vault/rules/general-rules.md` dosyasından alın (İngilizce:
   `vault/rules/general-rules.md`).
5. Vault'ta `py -3 -I _sistem/health.py` (İngilizce kurulumda `_system/health.py`) çalıştırın: "Security hooks and
   their matchers" satırı ok demeli.

### Bilinen sınırlar

- Dosyayı dolaylı yazan bir betik (yol betiğin içinde, `py arac.py`) komut kapısından geçer; `health.py` kapı
  betiklerindeki commit edilmemiş değişikliği sonradan gösterir.
- Değişkende tutulan ya da dizgi birleştirerek kurulan yol veya komut adı çözülmez.
- Okuma araçları hiçbir kapıdan geçmez. Web araması yalnızca Claude Code'da denetlenir.

## v1.1.0

`v1.1.0` etiketine bakın.
