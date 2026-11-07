---
name: fikir
description: Kullanıcının söylediği bir fikri anında ikinci beynin Inbox'ına kaydeder (kendi cümlesi aynen + kısa değerlendirme + bağlantılar). "Aklıma bir şey geldi", "şöyle bir fikrim var" gibi anlarda kullan; soru sormadan yaz.
---

Vault: `{{VAULT}}`. Şema: vault `CLAUDE.md` §7.1, şablon `_sablonlar/fikir.md`. Türkçe yaz.

1. **Hemen yaz, soru sorma.** `gelen/YYYY-MM-DD-<kisa-ad>.md` oluştur (küçük harf, ASCII, tire). Frontmatter: `type: idea`, `status: draft`, `tags`, `created`/`updated` bugün.
2. "Ham fikir" bölümüne kullanıcının **kendi cümlesini aynen** koy (düzeltme, kısaltma yok).
3. Kısa değerlendirme: ne işe yarar / kime; ilk adım ne; hangi mevcut proje, fikir ya da kavramla ilişkili (`[[...]]` linkleri). Açık sorular varsa listele. Toplam 10 satırı geçmesin.
4. Aynı ya da çok benzer bir fikir `gelen/` veya `fikirler/`'de varsa yeni not açma; mevcut nota tarihli ekleme yap ve bunu kullanıcıya tek cümleyle söyle.
5. `index.md` "Fikirler" bölümüne tek satır; `log.md` sonuna `## [YYYY-MM-DD] fikir | <başlık>`.
6. Vault'ta commit (uzak depo tanımlıysa push). İsteğe bağlı pano: v1'de yok.
7. `_sistem/beceriler/beceriler.md` tablosunda kullanım sayısını 1 artır.
8. Kullanıcıya tek satır: "Kaydettim → [[dosya-adi]]". Fikri tartışmaya ya da öğretmeye girişme (#15); kullanıcı isterse konuşulur.
