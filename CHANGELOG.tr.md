<div align="right">
  <b>Türkçe</b> · <a href="./CHANGELOG.md">English</a>
</div>

# Değişiklik günlüğü

## v1.2.2 — Güvenlik güncellemesi: beceri dosyalarındaki hook'lar

**Güncellemeniz önerilir.** Bir beceri (`SKILL.md`) ya da ajan tanımı, ön bilgisinde (frontmatter) `hooks:` alanı
taşıyabilir. Böyle bir hook, beceri ya da ajan etkinken her araç çağrısında `settings.json`'a uğramadan komut
çalıştırır; kapılar da sağlık raporu da bunu görmüyordu.

- **Yazma kapısı sorar:** bir yazma, beceri ya da ajan tanımının ön bilgisine `hooks:` koyuyorsa. Kapsam: her
  `SKILL.md`; vault'un `_sistem/beceriler/` ya da `_sistem/ajanlar/` klasörlerinin, her asistanın evindeki (`~/.claude`,
  `~/.codex`, `~/.gemini`, `~/.agents`) `skills/` ya da `agents/` klasörünün ve bir projenin `.claude/skills/` ya da
  `.claude/agents/` klasörünün altındaki her `.md`. Düzenlemede yeni metindeki girintisiz bir `hooks:` satırı yeter.
  Gövdedeki `hooks:` (ör. kod bloğundaki girintili bir örnek) sorulmaz.
- **Mod 4 ve 5, her yerde son sürüm:** yalnızca kullanıcı "Mod 4" ya da "Mod 5" deyince açılan iki yeni mod. Kurul Mod 3 kurulu; fark ana sohbetin modelidir: Fable'ın (4) ya da Mythos'un (5) en son sürümü, kullanıcının onayıyla geçilir (erişim yoksa Opus'ta kalınır ve söylenir; Mythos alt ajan olamaz). Modeller artık sürümsüz takma adla verilir (`opus`, `sonnet`, `haiku`, `fable`); kullanıcı sabitlemediyse yeni sürüm kendiliğinden kullanılır. Kural #28, `orkestrasyon`, `gorev-yazma`, global talimatlar ve şema tabloları güncellendi.
- **`health.py` var olanları gösterir:** yeni *Hooks in skill and agent definitions* denetimi vault'un ve her asistanın
  evindeki beceri ve ajan tanımlarını tarar. `hooks:` taşıyan tanım hatadır, dosya adı ayrıntıda görünür; okunamayan
  dosya uyarıdır.

**Nasıl güncellenir:** aşağıdaki v1.2.0 adımlarını izleyin, sonra `health.py`'yi bir kez çalıştırıp yeni denetime bakın.
Bir dosya adı görünürse o beceriyi ya da ajanı yeniden kullanmadan önce dosyayı açın; hook'ların yeri `settings.json`.

**Bu sürümde ayrıca**

- **Tasarım denetimi daha çok şey ölçüyor** (`expert-design`, `page_audit.py`): yer tutucu metin ve boş görünen başlık
  ya da düğme, 3 katına uzayınca taşan başlık, tam ekran bölüm yüksekliği (`--section-threshold`), eşit olmayan sol ve
  sağ boşluk, yüklenmemiş ya da boyutsuz görsel, sınırı aşan WebGL bağlamı (`--webgl-limit`, varsayılan 4) ve
  `prefers-reduced-motion: reduce` altındaki ek ölçümde durmayan animasyon ve rAF döngüsü. Sayfa ağırlığı Resource
  Timing'den okunur; ölçülemeyen `UNMEASURABLE` diye yazılır.
- **Yapay zekâ izi listesi yerine ne yapılacağını söylüyor** (`expert-design`, Türkçe kurulumda `uzman-tasarim`):
  `references/yapay-zeka-izi.md`'deki her işaret artık düzeltmesini taşır; yeni **D** işaretleri yüzey, simge, metin,
  grafik, açılış bölümü, hareket ve temizlenmiş ekranın düştüğü şablonu kapsar. Akış, var olan ekranın ne kadar
  değişeceğine önce karar verir; yön bir karakter ve tek imza ayrıntısı adlandırır, gerçek markayı korur; arayüz metnine
  beş kural daha; `references/gorsel-zanaat.md`'ye grafik ve sayı kartı bölümü. unslop'tan uyarlandı (Damir
  Sokolovsky, CC BY 4.0); metin yeniden yazıldı, kodu, sayısal değerleri ve mutlak yasakları alınmadı. Atıf
  `NOTICE.md`'de.
- **Kurmadan beceri dizininde arama** (`external-source-review`, yeni 0. adım): önce kendi becerilerine bak, yalnızca
  izinle ve tarayıcıdan ara, dizinin kurulum aracını çalıştırma; kurulum sayısı ve yıldız okuma sırasını belirler,
  güvenliği değil. Karardan önce adayın `SKILL.md` dosyası okunur.
- **Yeni beceri: marka içeriği ve reklam** (`expert-brand-content`, Türkçe kurulumda `uzman-marka-icerigi`): gönderi
  ve karusel, ürün çekim briefi, UGC senaryosu, reklam açısı ve test planı, reklam raporu okuma. Önce girdi envanteri
  ve iddia defteri gelir; hiçbir şey uydurulmaz, hiçbir şey yayınlanmaz. `scripts/ad_metrics.py` bir CSV'den harcama,
  dönüşüm, gelir, CPA ve ROAS hesaplar, biçim tahmin etmez: para birimi ve atıf sütunu ya adıyla verilir ya da yok
  diye beyan edilir; karışık para birimi ve bozuk hücre reddedilir, birebir aynı satırlar da `--count-duplicates`
  verilmedikçe. `uzman-icerik` marka metni için artık bu beceriyi gösterir.
- **Yeni beceri: oyun geliştirme** (`expert-game`, Türkçe kurulumda `uzman-oyun`): motoru proje dosyalarından bulur
  (Godot, Unity, Unreal, Phaser, PixiJS, three.js, Bevy, pygame, LÖVE, Defold, Ebitengine, Roblox), sonra yalnızca
  gereken disiplin (oyun hissi, kamera, seviye tasarımı, yapay zekâ, prosedürel üretim, kayıt, diyalog, girdi,
  arayüz, ses, gölgelendirici, fizik, performans), tür ve iş akışı (game jam, prototip, Steam, itch.io, oyun belgesi)
  dosyalarını okur. Doğrulama merdiveni çalıştırılanı yalnızca denetlenenden ve doğrulanmayandan ayırır; eğlence, his
  ve ses kullanıcının kararıdır. Fikirler ve eşikler kendi cümlelerimizle uyarlandı; metin ya da kod alınmadı. Atıf
  `NOTICE.md`'de.

## v1.2.1 — Güvenlik güncellemesi: güncelleme denetimi

**Güncellemeniz önerilir.** Bu sürüm aşağıdaki v1.2.0'ın tamamını içerir ve bir sonraki sürümden haberdar olmanın
yolunu ekler.

- **Güncelleme denetimi (varsayılan kapalı).** Mindgate bir program değil, bir dosya kümesi; yeni sürüm çıktığında size
  bunu söyleyen bir şey yoktu. `health.py` artık GitHub'a son sürümü sorup `Mindgate vX is out (security update)`
  diyebilir. Açmak için `_sistem/config.json` (İngilizce kurulumda `_system/`) içinde `"update_check": {"enabled": true}`
  yazın. Yalnızca `https://api.github.com/repos/AlicanKaya192/Mindgate/releases/latest` adresine sorar; vault'tan hiçbir
  şey gönderilmez, cevaptan yalnızca sürüm numarası kullanılır. Günlük ve haftalık görevler `health.py`'yi çalıştırdığı
  için uyarı orada görünür. Denetim kapalıyken sağlık raporu nasıl açılacağını gösterir.
- **Python 3.10 yeniden çalışıyor.** Komut kapısındaki bir desen Python 3.11 ile gelen bir sözdizimi kullanıyordu;
  3.10'da komut kapısı yüklenemiyordu. Desen yeniden yazıldı; bir test 3.11'e özgü desen sözdizimini kapılardan uzak
  tutar.
- **Denetim olmadan da haber almak için:** GitHub'da *Watch → Custom → Releases* her sürümde size bildirim gönderir.

**Nasıl güncellenir:** aşağıdaki v1.2.0 adımlarını izleyin. Kurucu `config.json` dosyasının üzerine yazmaz; güncelleme
denetimini kullanmak için sürümdeki `vault/_system/config.json` içinden `update_check` bölümünü kendi dosyanıza ekleyin
(düzenlemek sorulur; bu bilerek böyle).

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

1. Son sürümü alın (Mindgate klasörünüzde `git pull` ya da sürümü indirin).
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
