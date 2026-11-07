<div align="right">
  <b>Türkçe</b> · <a href="./CONTRIBUTING.md">English</a>
</div>

# Katkı Rehberi

Issue ve pull request herkese açık. Başlamadan önce
[Davranış Kuralları](./CODE_OF_CONDUCT.tr.md) belgesini okuyun. Güvenlik
sorunları issue'ya yazılmaz: [SECURITY.tr.md](./SECURITY.tr.md).

## Nasıl katkı verebilirim?

- **Hata bildirimi:** zararsız bir şeyi durduran ya da zararlı bir şeyi
  geçiren bir kapı, başarısız olan bir kurulum adımı, yanlış bir çeviri.
- **Yeni beceri, ajan ya da kural:** önce bir issue açıp çözdüğü sorunu
  anlatın; yazmadan önce biçimi birlikte belirleyelim.
- **Çeviri:** Mindgate İngilizce ve Türkçe geliyor. Yeni bir dil için
  [TRANSLATION-GUIDE.md](./TRANSLATION-GUIDE.md) belgesine uyan bir
  `locales/<kod>/` klasörü gerekir.
- **macOS ve Linux denemesi:** ikisi de denenmedi; bu sistemlerden gelen
  bildirimler çok değerli.

## Testleri çalıştırma

Python 3.10 ya da üstü gerekir. Paket kurulmaz.

```bash
# kurucu ve kaldırıcı (her zaman .yerel/ altında geçici bir ev klasörü kullanır)
cd setup
py -3 -I -B installer_test.py -v

# vault betikleri (vault/ klasöründen)
cd vault
py -3 -I -B _system/run_tests.py
```

macOS ve Linux'ta `py -3` yerine `python3` kullanın. Testler ağa bağlanmaz,
gerçek `~/.claude` klasörünüze ve kendi vault'unuza dokunmaz.

## Değişiklik kuralları

1. **İki dil birlikte.** Kullanıcının gördüğü metin aynı pull request'te hem
   İngilizce (`vault/`, `setup/`) hem Türkçe (`locales/tr/`) değişir. Kod,
   frontmatter alanları ve betik mesajları iki dilde de İngilizce kalır.
   Adlar `locales/tr/names.json` dosyasına uyar.
2. **Kişisel veri yok.** Kodda, notlarda, testlerde ve ekran görüntülerinde
   gerçek ad, yol, e-posta adresi, bilgisayar adı, proje adı ya da sır olmaz.
   `{{VAULT}}`, `{{HOME}}`, `{{PY}}` ve tarafsız örnekler kullanın.
3. **Hiçbir şey silinmez.** Kurucu ve kaldırıcı yedekler ve taşır; kodlarında
   silen bir çağrı olursa bir test başarısız olur. Böyle kalsın.
4. **Kapı değişikliği testle gelir.** Bir kapıdaki (`command_guard.py`,
   `write_guard.py`, `site_guard.py`, `agent_gate.py`) değişiklik, eklediği ya
   da düzelttiği durumun ve hâlâ durdurması gereken zararlı durumun testiyle
   gelir.
5. **Varsayılan güvenli.** Yeni bir güvenlik ayarı varsayılan açıktır; veriyi
   dışarı gönderen ya da web'e çıkan bir ayar varsayılan kapalıdır ve
   kurulumda sorulur.

## Pull request

- Her pull request tek bir değişiklik içersin ve neden gerektiğini anlatsın.
- İki test takımını da çalıştırın ve geçtiğini açıklamaya yazın.
- Değişiklik kurucunun yazdıklarını etkiliyorsa kurucuyu bir kez `--dry-run`
  ile çalıştırıp özetin ilgili kısmını ekleyin.
