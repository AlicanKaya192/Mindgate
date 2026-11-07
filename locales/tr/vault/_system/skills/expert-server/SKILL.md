---
name: uzman-sunucu
description: Sunucu, dağıtım ve ağ uzmanlık paketi. Uygulama yayınlama (deploy), ters vekil (reverse proxy), port, alan adı ve TLS, CI/CD, sunucu yapılandırması, kayıt ve izleme ya da yerel geliştirme sunucusu üzerinde çalışırken yükle.
---

Uzmanlık paketi (ajan değil). Bu bilgisayarda kural #19 ve #20 kesindir.

## Kesin kurallar (bu bilgisayar)
- Port doluysa süreci **öldürme**; boş port seç (`netstat -ano | findstr :<port>` ya da `Get-NetTCPConnection`) ve projeyi o porta ayarla. Kodda port 0 kullanmak işletim sistemine boş port seçtirir.
- İsme göre süreç öldürme asla. PID ile yalnızca sahibini doğrulayıp kullanıcıya sorarak.
- Güvenlik duvarı, servis, zamanlanmış görev, kayıt defteri (HKLM) değişikliği yapılmaz. Kapatma ya da yeniden başlatma yok.
- Uzak sunucuya bağlanma, yayınlama, DNS değiştirme gibi dışa dönük işlemler kullanıcının onayıyla (#23).

## Kontrol listesi
- [ ] Yapılandırma ortam değişkeni ya da dosyasıyla; sırlar `.env`'de ve git dışında.
- [ ] TLS açık, HTTP → HTTPS yönlendirme; güvenlik başlıkları (HSTS, CSP, X-Content-Type-Options).
- [ ] Ters vekil zaman aşımı, gövde boyutu sınırı, oran sınırı.
- [ ] Sağlık kontrolü uç noktası; düzgün kapanma (graceful shutdown).
- [ ] Kayıt: yapılandırılmış (JSON), dönen (rotation), içinde sır yok.
- [ ] Geri dönüş planı (rollback): önceki sürüme nasıl dönülür?
- [ ] CI: testler, bağımlılık taraması, sır taraması; sırlar CI gizli değişkenlerinde.
- [ ] En az yetki: servis kullanıcısı root ya da yönetici değil.

## Doğrulama
- Değişikliği yerelde ya da deneme ortamında çalıştır, sonucu göster (#24). "Yayına aldım" demeden önce sağlık kontrolünü gerçekten çağır.

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **GitHub Actions güvenliği:**
  - [ ] Üçüncü taraf action'lar commit SHA'sıyla sabitli (etiket değil).
  - [ ] `permissions:` en az yetkiyle tanımlı.
  - [ ] `pull_request_target` ile fork'tan gelen kod çalıştırılmıyor.
  - [ ] Güvenilmeyen girdi (`${{ github.event.issue.title }}` gibi) doğrudan `run:` içine konmuyor; ortam değişkeniyle veriliyor (komut enjeksiyonu).
  - [ ] Yapay zekâ ajanı çalıştıran iş akışlarına güvenilmeyen içerik (issue, PR metni) verilmiyor.
- **Gözlemlenebilirlik:** üç sinyal (log, metrik, iz/trace); anlamlı alarm eşikleri; her alarm için kısa bir runbook (ne yapılır).
- **Olay sonrası:** suçlamasız postmortem. Zaman çizelgesi, etki, kök neden, düzeltme ve tekrarını önleyecek adım. `sorunlar/`'a yazılır.
- **Terraform/IaC:**
  - `plan` çıktısı gösterilir; `apply` ve `destroy` kullanıcının onayıyla.
  - State dosyasında sır olabilir; git'e girmez.
  - Sağlayıcı ve modül sürümleri sabitlenir.
- Fikir kaynakları: trailofbits/skills (`agentic-actions-auditor`), semgrep/skills (`code-security`: GitHub Actions kontrolleri), hashicorp/agent-skills (Terraform), wshobson/agents (`observability-monitoring`, `incident-response`).

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
