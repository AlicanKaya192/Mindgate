<div align="right">
  <b>Türkçe</b> · <a href="./SECURITY.md">English</a>
</div>

# Güvenlik Politikası

## Desteklenen sürümler

Mindgate erken geliştirme aşamasında. Bildirimler `main` dalının güncel
hâline göre değerlendirilir.

| Sürüm | Destek |
|---|:-:|
| `main` | ✅ |
| `v1.2.2` (güvenlik güncellemesi, en son) | ✅ |
| `v1.2.1` (güvenlik güncellemesi) | ✅ (beceri ya da ajan tanımındaki `hooks:` alanı sorulmaz: v1.2.2'ye güncelleyin) |
| `v1.2.0` (güvenlik güncellemesi) | ✅ (Python 3.10'da komut kapısı yüklenmez: v1.2.1'e güncelleyin) |
| `v1.1.0` ve öncesi | ❌ (lütfen güncelleyin, bkz. [CHANGELOG.tr.md](CHANGELOG.tr.md)) |

## Mindgate bilgisayarınızda ne yapar

Mindgate bir servis değildir. Sunucusu, hesabı ve telemetrisi yoktur. `health.py` içindeki güncelleme denetimi
varsayılan olarak kapalıdır; açarsanız sabit bir GitHub adresine yalnızca son sürüm numarasını sorar, vault'tan
hiçbir şey göndermez.

- **Kurucu** yalnızca README'nin Güvenlik notu bölümünde sayılan yerlere
  yazar: seçtiğiniz vault klasörü, `~/.claude/CLAUDE.md` (ya da içindeki bir
  içe aktarma satırı), `~/.claude/settings.json` içindeki hook'lar, beceriler,
  ajanlar, zamanlanmış görev dosyaları ve `~/.claude/mindgate/`. Değiştireceği
  dosyayı önce yedekler. İnternetten bir şey indirmez, paket kurmaz. Tam liste
  için `--dry-run`.
- **Kaldırıcı** hiçbir şey silmez. Yedekleri geri yükler, kurulan dosyaları
  `~/.claude/mindgate-removed-<zaman>/` klasörüne taşır.
- **Betikler ağa bağlanmaz.** Web erişimi yalnızca Claude Code'un kendi
  araçlarıyla, Claude onları kullanmaya karar verdiğinde olur; haftalık
  görevin web adımı, kurulumda açmadıkça kapalıdır.
- **Hook'lar Python betiklerini sizin kullanıcı yetkinizle çalıştırır;**
  Claude Code bir olaya her geldiğinde (araç çağrısından önce, oturum
  başında vb.).

> **Kapılar bir kum havuzu (sandbox) değildir.** Komut, yazma ve site kapıları
> ile ajan kapısı bilinen riskli kalıpları yakalar, sorar ya da reddeder.
> Modelin kötü bir talimata uyma riskini azaltır; her zararlı komutu
> durduramaz ve bir modeli tek başına güvenli yapmaz.

### Kapılar neyi denetler (v1.2.0'dan beri)

- **Savunma dosyaları.** Kapıların kendi zeminini değiştirmek sorulur:
  desteklenen her asistanın hook ve izin ayarları, `_system/` içindeki vault
  betikleri, `config.json`, ajan tanımları, zamanlanmış görevler, git
  kancaları, kara liste, kurallar, talimatlar ve vault şeması. Tek liste
  (`common.DEFENSE_SET`) yazma kapısına da komut kapısına da hizmet eder.
- **Kabuktan ağa çıkış** sorulur, gerekçede adres görünür: indirme araçları,
  ham soket ve uzak kabuk, uzak yol, .NET ağ sınıfları, node/deno/bun ya da
  Python'a verilen ağ kodu, tarayıcıda adres açma, `git clone`/`git remote`,
  `gh api`. İndirileni yorumlayıcıya bağlamak reddedilir. Web araması
  (`WebSearch`) bir sayfa gibi sorulur.
- **Gizlenmiş komut adları** (ada serpiştirilmiş tırnak ya da ters bölü,
  `command`, `env` gibi önekler, `$(…)` ile hesaplanan ad) gerçek komut gibi
  denetlenir ya da sorulur.
- **Uzun komutlar.** 20.000 karakteri geçen komut, hiçbir desen çalışmadan
  sorulur (kayıtsız sohbette reddedilir); hiçbir girdi hook'un süre sınırını
  tüketemez.
- **Bozuk yardımcı modüller.** Kapı yardımcı modüllerini yükleyemezse çökmek
  yerine sorar (öbür asistanlarda reddeder); `_system/` içindeki standart
  kütüphane adlı bir dosya onun yerine geçemez.
- **Beceri ve ajan tanımlarındaki hook'lar** (v1.2.2'den beri). Bir
  `SKILL.md`'nin ya da ajan tanımının ön bilgisindeki `hooks:` alanı, her araç
  çağrısında `settings.json`'a uğramadan komut çalıştırır. Böyle bir alan
  yazmak sorulur; `health.py` zaten taşıyan tanımları adıyla gösterir.
- `health.py` eksik ya da daralmış güvenlik hook'larını, geniş izin
  kalıplarını, atlatılmış commit kancasını ve kapı betiklerindeki commit
  edilmemiş değişikliği gösterir.

### Bilinen sınırlar

- **Dolaylı yazan betik görülmez.** Bir kapı dosyasını değiştiren
  `py arac.py`, yol komut satırında geçmiyorsa komut kapısından geçer;
  `health.py` commit edilmemiş değişikliği sonradan gösterir.
- **Çalışırken kurulan değerler çözülmez:** değişkende tutulan (`$p`, `%P%`)
  ya da dizgi birleştirerek kurulan bir yol veya komut adı kapıdan görülmez.
- Okuma araçları hiçbir kapıdan geçmez; `.env` dosyaları yalnızca kabukta
  korunur.

## Güvenlik açığı bildirme

Şunlar güvenlik açığı sayılır ve bildirimleriniz memnuniyetle karşılanır:

- Bir kapının durdurması gereken bir komutu, dosya yazımını ya da site
  ziyaretini geçirmenin bir yolu (örneğin komut kapısının izin verdiği, proje
  dışında bir silme)
- Kurucunun ya da kaldırıcının saydığı yerlerin dışına yazması, üzerine
  yazması ya da silmesi; yedeklemesi gereken bir kullanıcı dosyasını kaybetmesi
- Bir betiğin bilgisayar dışına veri göndermesi ya da ağ bağlantısı açması
- Depoda kalmış bir sır, kişisel yol ya da kişisel veri; ya da bir betiğin
  vault'a bunları yazması
- `secret_scan.py` ya da `security_scan.py` betiğinin yakaladığını söylediği
  bir kalıbı kaçırması
- Bir web sayfası, dosya ya da araç çıktısındaki metnin yalnızca modeli değil,
  bir betiği harekete geçirmesi

Şunlar Mindgate'in açığı sayılmaz: hiçbir kapının devrede olmadığı bir yerde
Claude'un bir talimata uymaması (bu model davranışıdır) ve hook'ların kod
çalıştırabilmesi (hook'lar böyle çalışır; kurmadan önce okuyun).

### Nasıl bildirilir

**Güvenlik açığını herkese açık bir issue'da paylaşmayın.** Bunun yerine:

1. GitHub'ın
   [Security Advisories](https://github.com/AlicanKaya192/Mindgate/security/advisories/new)
   sayfasından gizli bir bildirim açın, ya da
2. [Bakımcının GitHub profilindeki](https://github.com/AlicanKaya192) iletişim
   adreslerinden birine yazın.

Bildirime denediğiniz commit'i, adım adım tekrar etme yolunu, olası etkisini
ve varsa düzeltme fikrinizi ekleyin. Kendi kişisel verilerinizi ve sırlarınızı
bildirime koymayın.

### Sonrası

- Bildirimin alındığı **48 saat içinde** doğrulanır.
- **7 gün içinde** sorunun geçerli olup olmadığı ve ne kadar ciddi olduğu
  bildirilir.
- Geçerliyse düzeltme yayınlanana kadar bilgilendirilirsiniz.
- İsterseniz düzeltme yayınlanırken adınız anılır.

Proje tek bir kişi tarafından boş zamanında yürütülüyor; bu süreler söz değil,
iyi niyetli hedeflerdir.
