# Beceri Kütüphanesi (Skill Library)

Claude Code becerileri. Kaynak dosyalar burada (`_sistem/beceriler/<ad>/SKILL.md`, git'te); `~/.claude/skills/<ad>` klasörleri buraya **junction** (Windows'ta) ya da sembolik bağ ile bağlı, yani tek kopya var. Yöntem belleğinin (procedural memory) basit hâli: tekrar eden iş = tek komut.

**Yarar sayacı:** Beceri her kullanıldığında kullanım sayısı artar; hata çıkarsa "son hata" sütununa yazılır. Üç kez aynı hatayı veren beceri haftalık bakımda yeniden yazılır (Memento-Skills'in "başarısızlıkta beceriyi düzelt" fikri, insan onayıyla).

| Beceri | Ne yapar | Kullanım | Son kullanım | Son hata |
|---|---|---|---|---|
| `/kayitlari-tut` | Oturum kayıtlarını tara, konuşmayı gözden geçir, vault'a işle, log, commit | 0 | — | — |
| `/yeni-proje` | Proje klasörü + ana sayfa, ilerleme, kurallar, ADR; index, log, profil | 0 | — | — |
| `/pano` | Panoyu ilk çalışmada kullanıcının claude.ai hesabında yayımlar, sonra yalnızca değişen veri setlerini yükler | 0 | — | — |
| `/sorun` | Sorun/çözüm notu (önce ara, varsa tekrar ekle), proje linki, index, log | 0 | — | — |
| `/fikir` | Fikri anında Inbox'a yaz: kendi cümlesi + kısa değerlendirme + linkler | 0 | — | — |
| `/sorgula` | Kullanıcıya konu bitene kadar tek tek soru sorar, cevapları ilgili notlara yazar (önce vault'ta arar; hassas bilgi yok) | 0 | — | — |
| `/stil` | Referans görselden animasyonlu anlatım videosu stil istemi çıkarır, taze oturumda sınar, o stilde video yapar (herkese açık bir /stil beceri metninden uyarlandı) | 0 | — | — |

### Uzmanlık paketleri (kural #28)
Kendiliğinden yüklenir (iş o alana dokununca). Uzmanlaşma her paketin **Dersler** bölümünde birikir; ders yalnızca merkezî ajan tarafından ve doğrulandıktan sonra eklenir. Ajanlar ve kullanım: `bilgi/ajanlar/` altındaki ajan sayfaları.

| Paket | Alan | Kullanım | Son kullanım |
|---|---|---|---|
| `uzman-mimari` | Yapı, modül sınırı, ADR, dosya sahipliği | 0 | — |
| `uzman-tasarim` | Görsel tasarım, tasarım sistemi, tipografi, renk, WCAG 2.2 | 0 | — |
| `uzman-frontend` | Arayüz (UI), kullanıcı deneyimi (UX), erişilebilirlik | 0 | — |
| `uzman-backend` | API, iş mantığı, veritabanı, migration | 0 | — |
| `uzman-guvenlik` | OWASP, sırlar, bağımlılık, tehdit modeli | 0 | — |
| `uzman-sunucu` | Dağıtım, port, TLS, CI | 0 | — |
| `uzman-docker` | Dockerfile, compose, imaj güvenliği | 0 | — |
| `uzman-ml` | Veri sızıntısı, metrik, tekrarlanabilirlik | 0 | — |
| `uzman-seo` | Teknik SEO, sayfa içi, JSON-LD, site yapısı, yapay zekâ aramalarında görünürlük | 0 | — |
| `uzman-icerik` | Kullanıcının ağzından blog, LinkedIn, README metni; yapay zekâ izi ayıklama, yedi geçişli düzenleme | 0 | — |
| `uzman-dil` | TDK ve İngilizce yazım, noktalama, bağlam; metinden yapay zekâ izi ayıklama; `references/tdk.md`, `references/yapay-zeka-izi.md` | 0 | — |
| `uzman-yazarlik` | Oyun anlatısı, karakter, diyalog, hikâye, arayüz metni, teknik belge, tasarım brief'i | 0 | — |
| `uzman-cografi-veri` | Kamuya açık canlı coğrafi veri (uçak, gemi, uydu geçişi, deprem, harita) ve açık kaynak istihbaratı (OSINT) tarzı olay ve altyapı araştırması | 0 | — |

### Yöntem becerileri
Ajan tanımındaki `skills:` alanıyla o ajana başlarken önceden yüklenir. Ana sohbet de aynı işi yaparken yükleyebilir.

| Beceri | Ajan | Ne | Kullanım | Son kullanım |
|---|---|---|---|---|
| `kesif-yontemi` | `kasif` | Kod keşfi adımları, kaynak sırası, alıntı → iddia, bitirmeden doğrulama | 0 | — |
| `inceleme-yontemi` | `inceleyici` | Farka odaklı geçişler, güven puanı (80 eşiği), yanlış pozitif eleme, rapor | 0 | — |
| `obsidian-yazimi` | `bakimci` | Obsidian sözdizimi, vault kuralları özeti, bitirmeden doğrulama | 0 | — |
| `temiz-kod` | hepsi (kural #30) | Temiz kod kuralları: isimler, fonksiyonlar, yorumlar, hata yönetimi, SRP, DRY/YAGNI/KISS, biçim, testler; bitirmeden kontrol listesi | 0 | — |
| `dogrulama` | `inceleyici`, `bakimci` (`kasif` ve ana sohbet yükleyebilir) | Önce kanıt sonra iddia: iddia → gereken kanıt tablosu, ajan raporunu diff ile doğrulama | 0 | — |
| `hata-ayiklama` | ana sohbet (`inceleyici` yükleyebilir) | Kök neden bulunmadan düzeltme yok; 4 aşama, 3 deneme kuralı, sorun notu | 0 | — |
| `test-yazma` | ana sohbet (`inceleyici` yükleyebilir) | Kırmızı-yeşil-düzenle (silmeden, #22), iyi test, regresyon, web arayüzünde keşif önce | 0 | — |
| `gorev-yazma` | ana sohbet | Uygulama planı, ajana görev şartnamesi (sayılmayan sonuçlar, çıktı sözleşmesi), paralel dağıtım, inceleme raporunu uygulama | 0 | — |
| `degerlendirme-yontemi` | ana sohbet (`inceleyici` yükleyebilir) | Doğrudan puan ya da A/B, önyargı önlemleri, rubrik, metrik seçimi, beceri ve prompt ölçümü | 0 | — |
| `baglam-yonetimi` | ana sohbet (`bakimci` yükleyebilir) | Zorunlu bölümlü özet, yoklama soruları, büyük çıktıyı dosyaya alma, bağlam bozulması belirtileri | 0 | — |
| `beceri-yazma` | ana sohbet | Dışarıdan gelen beceriyi inceleme ve uyarlama, SKILL.md yapısı, test, bağlama | 0 | — |
| `dis-kaynak-inceleme` | ana sohbet | Dış depo, beceri ya da ikinci beyin sistemini inceleme: envanter, tarama, `kasif`lerle okuma, doğrulama, A/B/C/D sınıflandırma, kırmızı bayraklar (üç tekrardan beceriye dönüştü, §10.2) | 0 | — |
| `orkestrasyon` | ana sohbet | Üç mod seçimi, kurul klasörü, kör ilk tur, en çok iki tur, çatışma etiketleri, tek sayfalık son rapor | 0 | — |
| `yorum-yontemi` | `yorumcu` | Başta yön ve kapsam, sonda kabul ölçütleri; dört bakış açısı, üç önem derecesi | 0 | — |
| `karsi-gorus-yontemi` | `hater` | Ön ölüm analizi, kanıtlı itiraz, durdurma ölçütü, cevapsız en güçlü itiraz | 0 | — |
| `haber-yontemi` | `haber` | Soru daraltma, kaynak sırası, SIFT ile iki kaynaklı doğrulama | 0 | — |
| `dis-ajan` | ana sohbet | Kurulu dış kodlama ajanını (Codex vb.) varsayılan kapalı, görev başına izinle kullanma | 0 | — |
| `tersine-muhendislik` | ana sohbet | Kaynak kodu olmadan program, paket ya da dosya biçimini anlama: önce yetki ve sınır, hedefe göre yol, önce özet, gözlem/çıkarım/bilinmeyen, bulgu defteri | 0 | — |
| `graf` | ana sohbet, `kasif` | Not grafı (`graph.py`: en kısa yol, komşular, topluluk, köprü not) ve Python kod haritası (`code_map.py`: import grafı, döngü, çağıranlar; çıkarıldı/tahmin etiketi). Standart kütüphane, ağ yok | 0 | — |
| `sentetik-musteri-testi` | ana sohbet | Bir fikri, teklifi ya da fiyatı kanıta dayalı sanal müşteri paneline sınatma: bağımsız sorular, karar kuralı, gerçek dünya testi (talep kanıtı değildir) | 0 | — |

## Yeni beceri ekleme
Ayrıntılı yöntem: `beceri-yazma` becerisi (dışarıdan gelen beceriyi uyarlama ve test dahil).

1. `_sistem/beceriler/<ad>/SKILL.md` yaz: frontmatter `name`, `description` (ne zaman kullanılacağı dahil); gövde numaralı adımlar; vault yolu ve şema referansı; kesin kurallar.
2. `~/.claude/skills/<ad>` bağını aç (Windows'ta: `cmd /c mklink /J "%USERPROFILE%\.claude\skills\<ad>" "<vault>\_sistem\beceriler\<ad>"`; başka sistemlerde `ln -s`).
3. Bu tabloya satır ekle; `log.md`'ye `kurulum` girdisi; pano onu bir sonraki `/pano` çalışmasında gösterir.
