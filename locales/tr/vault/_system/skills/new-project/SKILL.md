---
name: yeni-proje
description: İkinci beyinde yeni bir proje klasörü açar (ana sayfa, ilerleme, kurallar, kararlar/, deneyler/), index ve log'u günceller. Kullanıcı yeni bir projeye başlarken ya da var olan bir projeyi vault'a eklerken kullan.
---

Vault: `{{VAULT}}`. Şema: vault `CLAUDE.md` §2 (proje klasörü düzeni), §3 (adlandırma), §5 (frontmatter). Türkçe yaz.

1. Proje adını belirle: küçük harf, ASCII, tire (`rag-chatbot`). Kullanıcı söylemediyse kısa bir öneri yap, sorma.
2. Proje bilgisayarda varsa önce **oku**: README, varsa plan/durum dosyaları, `git log --oneline | head -30`, bağımlılık dosyaları. Kodu değiştirme.
3. `projeler/<proje>/` altında şablonlardan oluştur (`_sablonlar/`): `<proje>.md` (`proje`), `<proje>-ilerleme.md` (`proje-ilerleme`), `<proje>-kurallar.md` (`proje-kurallar`), boş `kararlar/` ve ML projesiyse `deneyler/`. `{{title}}`/`{{proje}}`/`{{date}}` yer tutucularını doldur; hedefi, durumu, teknoloji yığınını ve "İçerik haritası (MOC)" bölümünü gerçek bilgiyle yaz.
4. Projede daha önce alınmış önemli bir teknik karar belliyse geriye dönük ADR yaz (`karar-adr` şablonu; seçenekler çıkarımsa "geriye dönük" diye işaretle).
5. Projede bilinen, başka projelerde de işe yarayacak sorun/çözümler varsa `sorunlar/`'a yaz ve proje ana sayfasından link ver.
6. `index.md` → "Projeler" bölümüne ekle; `projeler/projeler.md` Bases tablosu otomatik gösterir. `ben/profil.md` → "Projeler" listesine ekle.
7. `log.md` sonuna `## [YYYY-MM-DD] proje | <Proje> eklendi` girdisi.
8. Proje klasöründe `CLAUDE.md` varsa sonuna kısa bir "İkinci beyin" bölümü ekle (vault yolu, bu projenin vault sayfaları, ilerleme/sorun/kararın vault'a da işleneceği). Commit'e **AI imzası koyma** (#14); proje reposuna sadece kullanıcı isterse commit at.
9. Vault'ta commit (uzak depo tanımlıysa push), sonra panoyu güncelle (`/pano`).
10. `_sistem/beceriler/beceriler.md` tablosunda kullanım sayısını 1 artır.

Kesin kurallar: hassas bilgi ve bilgisayar kodları yazılmaz (#3, #18); projede AI izi bırakılmaz (#14).
