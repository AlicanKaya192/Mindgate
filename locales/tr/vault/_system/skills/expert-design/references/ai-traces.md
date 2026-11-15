# Yapay zekâ izi denetimi

Ekrana karşı tek tek geç. Hiçbiri tek başına suç değildir: brief gerektiriyorsa kullanılır, gerekçesi yazılır. Sorun, boş kalan tercihlerin bunlara harcanmasıdır. Kaçarken başka bir varsayılana düşme.

Her satır **iz → yerine ne yapılır** biçimindedir. Düzeltme bir başlangıçtır; projenin tasarım kararı ve kullanıcının zevki önce gelir.

**Kanıt düzeyi:** **A** birincil kaynak, sayfada okundu. **B** Anthropic'in `frontend-design` becerisi (13 Ekim 2026, indirilen kopya). **C** arama sonucu özeti; çoğu araç satan blog, sayfalara girilmedi: aday, kesin değil. **D** bir tasarımcının işaret listesi (unslop, 15 Kasım 2026, indirilen kopya); ölçüme değil zanaat görüşüne dayanır. Kullanıcının kendi redleri bu listede değildir; `ben/profil.md` ve [[reddedilen-oneriler]]'den okunur ve bu listenin önüne geçer.

## Genel görünüm
- [ ] **A** Nötr, sade zemin ve parlak tek vurgu, başka kimlik yok. (NN/g) → Yön adımına dön: ürünün dünyasından gelen bir malzeme ve tek akılda kalacak öğe seç.
- [ ] **A** Ekran başka ürünle yer değiştirse kimse fark etmez. (NN/g) → Başlığı, görseli ve imza ayrıntısını bu ürünün kendi adlarıyla ve içeriğiyle yeniden yaz.
- [ ] **A** Görsel tercihler bir fikirden değil kütüphane varsayılanından geliyor (Tailwind, Shadcn). (NN/g) → Token'ları yönden türet; varsayılan kalan her değer için "neden bu" sorusunu cevapla.
- [ ] **D** Zenginlik çerçeveye yayılmış: zemin, düğme, kenarlık ve etiketlerin hepsi renkli ya da efektli. → Çerçeveyi sakinleştir; rengi ve ayrıntıyı içeriğin bir iki anına topla.

## Hiyerarşi ve düzen
- [ ] **A** Her öğe eşit ağırlıkta; asıl görev aşağıda, ikincil bilgi üstte. (NN/g) → Asıl görevi yukarı al ve en büyük öğe yap; ikincil bilgiyi küçült ya da sonraya taşı.
- [ ] **A** İlgili iki şey arasında büyük boşluk; gruplama yok. (NN/g) → Grup içi boşluk grup arası boşluktan küçük olsun.
- [ ] **A** Kenar boşlukları ekranlar arasında tutarsız. (NN/g) → Sayfa kenarı için tek değer; ölçek dışı tek seferlik değerleri ölçeğe çek.
- [ ] **B** Her şey aynı yuvarlak karta bölünmüş, aynı gölgeyle. Kart yasak değil, gerçek gruplama için kullanılır. → Gruplama taşımayan kartı kaldır; ayrımı boşluk ve ince çizgiyle ver.
- [ ] **C** Eşit aralıklı aynı boy kart ızgarası; bölümler aynı kalıpla yinelenir. → Izgaraya ritim ver: birkaç küçük öğe ve bir geniş öğe; içerik türü farklıysa boyut da farklı olsun.
- [ ] **C** Bölümler ayrı ayrı üretilmiş gibi, farklı sitelerden gelmiş gibi duruyor. → Bütün bölümleri aynı token'lara bağla; düzeltmeyi bölüm bölüm değil katman katman yap (önce boşluk, sonra renk).
- [ ] **D** Aynı listedeki satırlar farklı yükseklikte; kardeş kartların iç boşluğu farklı. → Aynı şey aynı boyda: tek satır yüksekliği, tek iç boşluk.
- [ ] **D** Simgeler, etiketler ve sayılar aynı sütunda hizalı değil. → Simge kutusu her satırda aynı genişlikte; sayılar sağa hizalı.

## Renk ve yüzey
- [ ] **A** Renk fazla, görsel gerilim yaratıyor. (NN/g) → Zemin, yüzey, kenarlık ve metni tek nötr rampadan al; vurguyu ekran başına bir iki yere indir.
- [ ] **A** Kontrast zayıf. (NN/g) → Ölç; normal metin 4.5:1, büyük metin ve arayüz öğesi 3:1.
- [ ] **B** Süs olarak gradyan. → Düz yüzey. Gradyan kalacaksa bir anlam taşısın ya da aynı tonun içinde küçük bir geçiş olsun.
- [ ] **B** Krem zemin, serif başlık ve kiremit vurgu; ya da koyu zeminde tek parlak yeşil veya kırmızı vurgu. → Paleti ürünün dünyasından türet; bir varsayılandan ötekine geçme.
- [ ] **C** Mor, indigo ya da mavi-mor gradyan; gradyanlı hero. → Tek nötr yüzey; marka rengi varsa vurgu olur, yüzeyden çıkar.
- [ ] **C** Yuvarlak kartın bir kenarında kalın renkli şerit. → Durumu küçük bir nokta ya da metinle söyle.
- [ ] **D** Başlıkta, sayıda ya da logoda gradyanlı metin. → Düz, birincil metin rengi.
- [ ] **D** Renkli parıltı, renkli gölge, neon kenarlık; içeriğin arkasında bulanık renk lekesi. → Kaldır. Derinlik yüzey basamağından ve ince, düşük opaklıklı kenarlıktan gelsin.
- [ ] **D** Aynı rengin birbirine çok yakın birçok tonu metinde. → Üç metin rolü: birincil, ikincil, soluk.
- [ ] **D** Her öğe vurgulu, hiçbiri öne çıkmıyor. → Vurgu yalnızca asıl eylemi, seçimi ya da önemli tek sayıyı işaretler.
- [ ] **D** Cam görünümlü kart: beyaz iç parlaklık ve renkli gölge. → Düz yükseltilmiş yüzey ve ince kenarlık.

## Tipografi
- [ ] **B** Her başlığın üstünde büyük harfli küçük etiket. → Etiketi kaldır ya da cümle düzeninde yaz. Kısa, tek satırlık büyük harfli etiket gerekçesiyle kalabilir (harf aralığı: `gorsel-zanaat.md`); iz olan, her bölümde yinelenmesidir.
- [ ] **B** Küçük veri etiketlerinde tek aralıklı (monospace) yazı. → Arayüz ailesini kullan; tek aralıklı yazıyı kod ve hizalanması gereken sayıya sakla.
- [ ] **B** Başlıkta tek kelimeyi renklendirmek. → Vurguyu kelime seçimiyle ver; başlık tek renk.
- [ ] **C** Yazı tipi seçilmemiş, varsayılan kalmış (Inter vb.). **Inter yasak değil**, kaynaklar tartışıyor; soru "bu yazı tipini neden seçtim" sorusudur. → Yöndeki karaktere göre seç ya da neden kaldığını yaz.
- [ ] **D** Başlıklar 800–900 kalınlıkta. → Hiyerarşiyi boyut ve renkle kur; kalınlığı az sayıda basamakta tut.
- [ ] **D** Aynı ekranda çok sayıda boyut ve kalınlık. → Ölçekten birkaç boyut, iki kalınlık.
- [ ] **D** Sayılar karışık biçimde (biri kuruşlu, biri kuruşsuz). → Ekran boyunca tek biçim, `tabular-nums`.
- [ ] **D** Küçük yazıda negatif harf aralığı; vurgu için italik. → Küçük yazıda sıfır ya da hafif açık aralık; vurgu renk ya da kalınlıkla.

## Simge
- [ ] **D** Gezinmede, etikette ya da durumda emoji; sayaç içinde emoji. → Tek setten çizgi simge ya da hiçbiri; sayaç düz sayı.
- [ ] **D** Simgeler farklı boyut ve renkte. → Tek boyut, tek çizgi kalınlığı; renk bağlı olduğu metnin rolünden.
- [ ] **D** Yapay zekâ ile ilgili her şeyde parıltı simgesi. → Kaldır; simge ancak bir şeyi açıklıyorsa kalır.

## Kalıp tekrarları
- [ ] **B** `A · B · C` biçimli meta satırı. → En önemli bilgiyi bırak, ötekileri ayrıntıya taşı.
- [ ] **B** Düğme metninin sonunda `→`. → Düğme eylemi söyler; ok ancak başka sayfaya götürüyorsa.
- [ ] **B** Sıra değilken 01/02/03 numaralandırma. → Numarayı kaldır; sıra gerçekse kalsın.
- [ ] **B** Gazete düzeni: ince çizgiler, köşesiz kutular. → Projenin köşe ve çizgi token'larına dön.
- [ ] **B** Her bölüme kayarak beliren giriş animasyonu. → Yüklemede en çok bir giriş; ötekiler durağan (`hareket-etkilesim.md`).
- [ ] **D** Sayaç, plan ve kısayol için parlayan hap; her yerde "PRO", "Yeni", "Beta" rozeti. → Sakin metin ya da tuş görünümü; rozet ancak gerçekten gerekiyorsa, tek ve sakin.
- [ ] **D** Aramadan düğmeye, karta kadar her şey tam yuvarlak. → Köşe boyuta göre; iç içe köşe hesabı.

## Metin
Kurallar: beceri dosyasında "Arayüz metni".
- [ ] **C** John Doe, Sarah Johnson gibi yer tutucu adlar; yuvarlak sayılı sahte veri. → Projenin gerçek verisine benzeyen ad ve sayı.
- [ ] **D** Selamlama başlığı ("Tekrar hoş geldin!"). → Başlık bağlamı söyler: sayfanın adı ya da dönem.
- [ ] **D** Arayüz metninde ünlem. → Düz cümle.
- [ ] **D** Neye göre olduğu söylenmeyen değişim ("+%12"). → Karşılaştırmayı yaz: "geçen aya göre +%12".
- [ ] **D** Abartı kelimeler ve her ürüne uyan başlık ("iş akışınızı güçlendirin"). → Ürünün kime ne yaptığını kendi adlarıyla söyle.
- [ ] **D** Kaynağı olmayan sosyal kanıt ("10.000+ ekip güveniyor", yıldızlar, avatar dizisi). → Kullanıcıya sor; gerçekse sakin ve somut yaz, değilse kaldır. Raporda listele.
- [ ] **D** Uzun yer tutucu ("Herhangi bir şey ara..."); etiket ve düğme sonunda nokta. → "Ara"; kısa metin noktasız biter.

## Grafik ve sayı kartı
Kurallar: `gorsel-zanaat.md` "Grafik ve sayı kartı".
- [ ] **D** Tek seride gökkuşağı çubuklar, parlayan çubuklar. → Önemli olan tek şey vurguyu alır, gerisi nötr basamaklarda.
- [ ] **D** Her sayı kartına eklenmiş mini grafik ya da süs çizgisi. → Etiket, büyük sayı ve neye göre değiştiği.
- [ ] **D** Aynı boyda, aynı düzende yan yana grafikler. → Tek ana grafik; öteki veriler daha küçük ve farklı türde.

## Açılış bölümü (hero)
- [ ] **D** Başlığın üstünde hap biçimli duyuru rozeti. → Kaldır; gerçek bir haberse sakin bir metin bağlantısı.
- [ ] **D** Arkada süzülen leke, küre, ızgara, parlayan çizgi; her yapay zekâ ürününde robot ve beyin görseli. → Düz zemin ya da ürünün kendisi: gerçekçi veriyle kodda kurulmuş bir önizleme.
- [ ] **D** Üç ve daha çok düğme; düğmelerin altına dizilmiş rozet ve avatarlar. → Bir birincil, en çok bir ikincil eylem.
- [ ] **D** Görsele gömülü yazı, sahte düğme ya da sahte logo. → Yazı sayfada gerçek metin olur; görsel yazısız.
- [ ] **D** Her bölümde bir görsel. → Görsel yardım ettiği yerde, çoğu zaman yalnızca açılışta.

## Hareket
Ölçen kurallar: `denetim.md` T15, T16, T27, T38, T39.
- [ ] **D** Canlı olmayan öğede nabız ya da soluk alan parıltı; kaydırmada süzülen öğeler. → Durağan.
- [ ] **D** Kartta üzerine gelince büyüme; sıçrayan, taşan yaylar. → Üzerine gelince renk ya da yüzey basamağı; basışta küçük bir küçülme; tek ease-out eğrisi.

## Süreç
- [ ] **A** Yanlış kalıp: kelimeden seçilmiş, bağlamdan değil. (NN/g) → Brief'teki görevi yeniden oku; kalıbı görevden seç.
- [ ] **A** Değiştirme sınavı yapılmadı, gerekçe yok. → Yap ve yaz.
- [ ] Hiç ekran görüntüsü alınmadan bitti. → Çiz, ölç, bak (akışın 8. adımı).

## Temizlikten sonra düşülen şablon
İz değildir; kimse karar vermediğinde temizlenmiş ekranın vardığı yerdir. Düzeltmelerden sonra bak.
- [ ] **D** Düz gri zemin, varsayılan yazı tipi ve tek düğmede eski marka rengi. → Nötrleri ürünün dünyasına doğru hafifçe renklendir; vurguyu oradan al.
- [ ] **D** Boş kutu ya da genel bir resim olarak kalan açılış görseli. → Ürün önizlemesi.
- [ ] **D** Her ürüne aynı düzen, yazı ve palet. → Yön karar versin, alışkanlık değil.

## Kalite yukarı çeken ayrıntılar
Bunlar zanaatin görünmez kısmıdır. Kowalski: fark edilmese bile birikir.
- Gölgeler tek ışık kaynağından; rakamlar tablo düzeninde (`tabular-nums`); iç içe köşeler uyumlu.
- Basışta küçük geri bildirim; popover tetikleyiciden açılır; ikinci tooltip gecikmesiz.
- Kopyalamada bildirim yerine yerinde onay işareti; hata ilgili alanı vurgular.
- Üzerine gelme ve odak, dinlenme hâlinden daha yüksek kontrastlı.

---
**D** düzeyindeki işaretler ve düzeltme fikirleri Damir Sokolovsky'nin unslop becerisinden uyarlandı (CC BY 4.0, https://github.com/heydamir/unslop). Metin yeniden yazıldı, sayısal değerleri ve mutlak yasakları alınmadı; A, B ve C satırlarındaki düzeltmeler bizim.
