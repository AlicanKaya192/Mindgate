# Yapay zekâ izi denetimi

Ekrana karşı tek tek geç. Hiçbiri tek başına suç değildir: brief gerektiriyorsa kullanılır, gerekçesi yazılır. Sorun, boş kalan tercihlerin bunlara harcanmasıdır. Kaçarken başka bir varsayılana düşme.

**Kanıt düzeyi:** **A** birincil kaynak, sayfada okundu. **B** Anthropic'in `frontend-design` becerisi (13 Ekim 2026, indirilen kopya). **C** arama sonucu özeti; çoğu araç satan blog, sayfalara girilmedi: aday, kesin değil. Kullanıcının kendi redleri bu listede değildir; `ben/profil.md` ve [[reddedilen-oneriler]]'den okunur ve bu listenin önüne geçer.

## Genel görünüm
- [ ] **A** Nötr, sade zemin ve parlak tek vurgu, başka kimlik yok. (NN/g)
- [ ] **A** Ekran başka ürünle yer değiştirse kimse fark etmez. (NN/g)
- [ ] **A** Görsel tercihler bir fikirden değil kütüphane varsayılanından geliyor (Tailwind, Shadcn). (NN/g)

## Hiyerarşi ve düzen
- [ ] **A** Her öğe eşit ağırlıkta; asıl görev aşağıda, ikincil bilgi üstte. (NN/g)
- [ ] **A** İlgili iki şey arasında büyük boşluk; gruplama yok. (NN/g)
- [ ] **A** Kenar boşlukları ekranlar arasında tutarsız. (NN/g)
- [ ] **B** Her şey aynı yuvarlak karta bölünmüş, aynı gölgeyle. Kart yasak değil, gerçek gruplama için kullanılır.
- [ ] **C** Eşit aralıklı aynı boy kart ızgarası; bölümler aynı kalıpla yinelenir.
- [ ] **C** Bölümler ayrı ayrı üretilmiş gibi, farklı sitelerden gelmiş gibi duruyor.

## Renk
- [ ] **A** Renk fazla, görsel gerilim yaratıyor. (NN/g)
- [ ] **A** Kontrast zayıf. (NN/g)
- [ ] **B** Süs olarak gradyan.
- [ ] **B** Krem zemin, serif başlık ve kiremit vurgu; ya da koyu zeminde tek parlak yeşil veya kırmızı vurgu.
- [ ] **C** Mor, indigo ya da mavi-mor gradyan; gradyanlı hero.
- [ ] **C** Yuvarlak kartın bir kenarında kalın renkli şerit.

## Tipografi
- [ ] **B** Her başlığın üstünde büyük harfli küçük etiket.
- [ ] **B** Küçük veri etiketlerinde tek aralıklı (monospace) yazı.
- [ ] **B** Başlıkta tek kelimeyi renklendirmek.
- [ ] **C** Yazı tipi seçilmemiş, varsayılan kalmış (Inter vb.). **Inter yasak değil**, kaynaklar tartışıyor; soru "bu yazı tipini neden seçtim" sorusudur.

## Kalıp tekrarları
- [ ] **B** `A · B · C` biçimli meta satırı.
- [ ] **B** Düğme metninin sonunda `→`.
- [ ] **B** Sıra değilken 01/02/03 numaralandırma.
- [ ] **B** Gazete düzeni: ince çizgiler, köşesiz kutular.
- [ ] **B** Her bölüme kayarak beliren giriş animasyonu.

## İçerik
- [ ] **C** John Doe, Sarah Johnson gibi yer tutucu adlar; yuvarlak sayılı sahte veri.

## Süreç
- [ ] **A** Yanlış kalıp: kelimeden seçilmiş, bağlamdan değil. (NN/g)
- [ ] **A** Değiştirme sınavı yapılmadı, gerekçe yok.
- [ ] Hiç ekran görüntüsü alınmadan bitti.

## Kalite yukarı çeken ayrıntılar
Bunlar zanaatin görünmez kısmıdır. Kowalski: fark edilmese bile birikir.
- Gölgeler tek ışık kaynağından; rakamlar tablo düzeninde (`tabular-nums`); iç içe köşeler uyumlu.
- Basışta küçük geri bildirim; popover tetikleyiciden açılır; ikinci tooltip gecikmesiz.
- Kopyalamada bildirim yerine yerinde onay işareti; hata ilgili alanı vurgular.
- Üzerine gelme ve odak, dinlenme hâlinden daha yüksek kontrastlı.
