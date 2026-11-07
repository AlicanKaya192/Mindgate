---
name: uzman-ml
description: Makine öğrenmesi ve veri bilimi uzmanlık paketi. Veri hazırlama, model eğitimi ya da değerlendirmesi, deney tasarımı, metrik seçimi, özellik mühendisliği, veri sızıntısı kontrolü veya ML kodunu incelerken yükle.
---

Uzmanlık paketi (ajan değil). Kavramları `bilgi/`'ye not al.

## Kontrol listesi
- [ ] **Veri sızıntısı (data leakage):** ölçekleme, doldurma ve özellik seçimi yalnızca eğitim verisinde `fit`, test ve doğrulamada `transform`; `Pipeline` kullan. Hedeften türeyen özellik yok. Zaman serisinde geleceğe bakma yok (zamana göre bölme).
- [ ] **Bölme:** eğitim / doğrulama / test ayrı; gruplu veride grup bazlı bölme; dengesiz sınıfta tabakalı (stratified).
- [ ] **Metrik:** probleme uygun mu (dengesiz sınıfta accuracy değil; F1, PR-AUC, recall)? Temel çizgi (baseline: dummy, basit model) ile karşılaştırıldı mı?
- [ ] **Tekrarlanabilirlik:** seed sabit, sürümler kayıtlı, veri sürümü ya da karması belli.
- [ ] **Değerlendirme:** çapraz doğrulama (cross-validation) ya da güven aralığı; tek bir şanslı bölmeye güvenme. Test seti en sonda **bir kez** kullanılır.
- [ ] **Aşırı öğrenme (overfitting):** eğitim ve doğrulama farkı izleniyor; erken durdurma ya da düzenlileştirme.
- [ ] **Veri kalitesi:** eksik değer, aykırı değer, tekrar eden satır, etiket hatası kontrol edildi.
- [ ] **Bellek ve kaynak:** büyük veride parça parça okuma; `n_jobs` ve BLAS çekirdek sayısı (çekirdek başına bellek).
- [ ] **Belgeleme:** önemli model ya da veri setinde model kartı ve veri kartı; deney notu `deneyler/`.

## Doğrulama
- Sayıları gerçekten çalıştırıp göster; ezberden metrik yazma (#24). Sonucun rastlantı olmadığını göster (seed değiştir, CV).

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **Deney takibi:** Her koşuda parametreler, metrikler, seed, veri sürümü/karması ve kod commit'i kaydedilir. Araç: Trackio, MLflow ya da basit JSON/CSV. Kurulumu kullanıcıya sor. Sonuç `deneyler/` notuna da işlenir.
- **Bellek tahmini (model yüklemeden önce):** ağırlık belleği ≈ parametre sayısı × bayt (fp32 4, fp16/bf16 2, int8 1, 4-bit ≈0.5). Üstüne aktivasyon, bağlam (KV önbelleği) ve eğitimde optimizer payı eklenir. Kartın boş belleğini `nvidia-smi` ile **ölç**, ezberden yazma (donanım için `ben/ortam.md`).
- **LLM değerlendirmesi (evals):**
  - Sabit bir test seti, temel çizgi ve küçük bir elle etiketlenmiş altın küme kullan. Tek örneğe bakıp "daha iyi" deme.
  - Model-yargıç (LLM-as-judge) kullanılırsa yanlılığını kontrol et: sıra, uzunluk, kendi modelini kayırma.
- **İnce ayar (fine-tuning):** Önce prompt ya da RAG yetiyor mu, ölç. Gerekirse LoRA/QLoRA. Sohbet şablonu (chat template) modelinkiyle uyumlu olmalı. Eğitim ve doğrulama kaybı birlikte izlenir.
- **RAG:**
  - Getirme (retrieval) ve üretim ayrı ölçülür: getirmede recall@k, üretimde cevabın kaynağa bağlılığı (faithfulness).
  - Parça boyutu (chunk) ve örtüşme deneyle seçilir. Cevap kaynak gösterir.
- **İstatistik:** İki model arasındaki fark anlamlı mı? Birkaç seed ya da CV katmanında tekrar et; mümkünse güven aralığı ya da eşleştirilmiş test.
- **Ortam:** `.venv`, sabit sürümler. PyTorch ve CUDA sürümünü resmî seçiciden doğrula; paket adını resmî kayıtta kontrol et (slopsquatting).
- Fikir kaynakları: huggingface/skills (`huggingface-trackio`, `huggingface-community-evals`, `hf-mem`, `trl-training`), everything-claude-code (`eval-harness`, `mle-workflow`), alirezarezvani/claude-skills (`rag-architect`), K-Dense-AI/scientific-agent-skills (`scikit-learn`, `statsmodels`).

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
