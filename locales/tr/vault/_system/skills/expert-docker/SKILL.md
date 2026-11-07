---
name: uzman-docker
description: Docker ve konteyner uzmanlık paketi. Dockerfile, docker compose, imaj boyutu ya da güvenliği, konteyner ağı, birim (volume) veya konteynerde çalışan geliştirme ortamı üzerinde çalışırken yükle.
---

Uzmanlık paketi (ajan değil). Docker'ın kurulu olup olmadığını ve hangi projelerin Docker kullandığını vault'taki ortam notundan (`ben/ortam.md`) ve proje notlarından oku.

## Kontrol listesi
- [ ] Temel imaj resmî ve **sabit sürümlü** (`python:3.12-slim`, `latest` değil); mümkünse küçük (slim, alpine; uyumluluğu kontrol et).
- [ ] Çok aşamalı derleme (multi-stage): derleme araçları son imajda yok.
- [ ] Root olmayan kullanıcı (`USER`); gereksiz yetki (`--privileged`) yok.
- [ ] `.dockerignore` var: `.git`, `.env`, `node_modules`, yerel veri imaja girmiyor.
- [ ] Sırlar imaja gömülmüyor (ENV ya da COPY ile); çalışma anında veriliyor.
- [ ] Katman sırası önbelleğe uygun (önce bağımlılık dosyası, sonra kod).
- [ ] Sağlık kontrolü (`HEALTHCHECK`), düzgün kapanma, tek süreç ilkesi.
- [ ] Compose: portlar yalnızca gerekli olanlar ve doluysa başka port (#20); birimler adlandırılmış; ağlar ayrık.
- [ ] İmaj taraması (`docker scout` ya da `trivy`; kurulu değilse kullanıcıya sor).

## Kesin kurallar
- `docker system prune`, `docker volume rm`, `docker rmi` gibi **silme komutları** kullanıcının izniyle (#22); hangi imaj ya da birimin neden silineceği açıklanır.
- Başkasının konteynerini ya da Docker Desktop'ı durdurma ya da kapatma.

## Doğrulama
- `docker build` ve `docker run` çıktısını göster; imaj boyutunu ölç (#24).

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **Compose ve çalışma anı sertleştirme:**
  - [ ] `privileged: true`, `network_mode: host` ve `/var/run/docker.sock` bağlama yok. Bunlar konteynere ana makinede tam yetki verir; gerekiyorsa kullanıcıya gerekçesiyle sor.
  - [ ] Portlar yalnızca yerelden açılıyorsa `127.0.0.1:<port>:<port>` biçiminde.
  - [ ] Mümkünse `read_only: true`, `cap_drop: [ALL]` (gerekeni geri ekle), `security_opt: [no-new-privileges:true]`.
  - [ ] Kaynak sınırları (bellek, CPU) tanımlı.
- **Sabitleme:** Üretimde imaj etiketi yerine özet (digest, `@sha256:…`) tercih edilir.
- **Kubernetes** (gerekirse): `resources` limitleri, `readinessProbe`/`livenessProbe`, `securityContext.runAsNonRoot: true`, sırlar Secret nesnesinde (git'te düz değil).
- Fikir kaynakları: semgrep/skills (`code-security`: Docker/Kubernetes kontrolleri), VoltAgent (`docker-expert`, `kubernetes-specialist`).

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Paketlenmiş uygulamada Docker alıştırmaları paketlenmiş sürümde ayrıca denenmeli.
