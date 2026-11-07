---
name: expert-ml
description: Machine learning and data science expertise pack. Load when working on data preparation, model training or evaluation, experiment design, metric selection, feature engineering, data leakage checks, or when reviewing ML code.
---

Expertise pack (not an agent). Note concepts in `knowledge/`.

## Checklist
- [ ] **Data leakage:** scaling, imputation and feature selection are `fit` only on the training data and `transform` on test and validation; use a `Pipeline`. No feature derived from the target. No looking into the future in a time series (split by time).
- [ ] **Split:** training / validation / test are separate; group-based split on grouped data; stratified for imbalanced classes.
- [ ] **Metric:** is it suitable for the problem (not accuracy on imbalanced classes; F1, PR-AUC, recall)? Was it compared with a baseline (dummy, simple model)?
- [ ] **Reproducibility:** fixed seed, recorded versions, known data version or hash.
- [ ] **Evaluation:** cross-validation or a confidence interval; do not trust a single lucky split. The test set is used **once**, at the very end.
- [ ] **Overfitting:** the gap between training and validation is watched; early stopping or regularization.
- [ ] **Data quality:** missing values, outliers, duplicate rows and label errors were checked.
- [ ] **Memory and resources:** read large data in chunks; `n_jobs` and the number of BLAS threads (memory per core).
- [ ] **Documentation:** a model card and a data card for an important model or dataset; an experiment note in `experiments/`.

## Verification
- Actually run the numbers and show them; do not write metrics from memory (#24). Show that the result is not chance (change the seed, CV).

## Additional methods
Ideas are in our own words.
- **Experiment tracking:** In each run record the parameters, metrics, seed, data version/hash and the code commit. Tool: Trackio, MLflow or simple JSON/CSV. Ask the user before installing. The result is also written to the `experiments/` note.
- **Memory estimate (before loading a model):** weight memory ≈ number of parameters × bytes (fp32 4, fp16/bf16 2, int8 1, 4-bit ≈0.5). Add activations, context (KV cache) and, in training, the optimizer share. **Measure** the card's free memory with `nvidia-smi`, do not write it from memory (see the hardware in `me/environment.md`).
- **LLM evaluation (evals):**
  - Use a fixed test set, a baseline and a small hand-labeled gold set. Do not say "better" from looking at a single example.
  - If a model judge (LLM-as-judge) is used, check its biases: order, length, favoring its own model.
- **Fine-tuning:** First measure whether a prompt or RAG is enough. If needed, LoRA/QLoRA. The chat template must match the model's. Watch training and validation loss together.
- **RAG:**
  - Retrieval and generation are measured separately: recall@k for retrieval, faithfulness to the source for generation.
  - Chunk size and overlap are chosen by experiment. The answer cites its source.
- **Statistics:** Is the difference between two models significant? Repeat over several seeds or CV folds; if possible a confidence interval or a paired test.
- **Environment:** `.venv`, pinned versions. Verify the PyTorch and CUDA version from the official selector; check the package name in the official registry (slopsquatting).
- Idea sources: huggingface/skills (`huggingface-trackio`, `huggingface-community-evals`, `hf-mem`, `trl-training`), everything-claude-code (`eval-harness`, `mle-workflow`), alirezarezvani/claude-skills (`rag-architect`), K-Dense-AI/scientific-agent-skills (`scikit-learn`, `statsmodels`).

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
