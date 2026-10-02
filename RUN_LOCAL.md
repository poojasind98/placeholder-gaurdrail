# Run LogLLM on this Mac

## BGL and Liberty presentation (September 29 update)

See [BGL_LIBERTY_WALKTHROUGH.md](BGL_LIBERTY_WALKTHROUGH.md) for the expanded speaking script and [the offline presentation](presentations/BGL-Liberty/index.html) for dataset switching and stage-by-stage evidence.

Liberty's prepared test file is now available at `data/Liberty/test.csv` (10,000 sequences: 9,349 normal and 651 anomalous). A selected sample at `data/Liberty/smoke-mixed.csv` contains the first 10 normal and first 10 anomalous rows, with `SourceRow` retained. Real inference using `ft_model_Liberty` completed with 20/20 correct on this selected sample. This is a functionality check, not a full benchmark.

```bash
source .venv-logllm/bin/activate
python presentation_walkthrough.py inputs --dataset Liberty
python presentation_walkthrough.py preprocessing --dataset Liberty
python presentation_walkthrough.py tokens --dataset Liberty
python presentation_walkthrough.py trace --dataset Liberty
python presentation_walkthrough.py results --dataset Liberty
```

Replace `Liberty` with `BGL` for the corresponding saved evidence. The `sources`, `raw`, and `sequences` stages are also available. These commands do not run the neural models.

To repeat a small Liberty inference with optional first-batch tracing, use a fresh output folder:

```bash
python eval.py --device mps --dataset Liberty --data data/Liberty/smoke-mixed.csv --limit 20 --batch-size 1 --output-dir outputs/Liberty-meeting-live --trace-output outputs/Liberty-meeting-live/pipeline-trace.json
```

`--trace-output` observes intermediate shapes and small numerical excerpts without modifying model outputs. The presentation's BGL metrics remain from the earlier 20-sequence run; its tensor trace is a separate one-sequence run at `outputs/BGL-trace-example`. Both model runs are complete; only the optional localhost presentation server may remain running.

The Liberty download is linked in the [upstream README](https://github.com/guanwei49/LogLLM#5-evaluate-on-test-dataset):

```bash
.venv-logllm/bin/gdown 1-Z2FrsRSm8ojfOW1555obNyU6B_aRDTH -O data/Liberty/test.csv
```

The full raw archives were not reprocessed. Three original-source records per dataset are stored as separate parsing illustrations; their provenance files identify their sources.

This setup uses the original BERT/projector/Llama architecture and the existing
fine-tuned adapters. It does not use `demo/` or retrain the models.

## Setup status

- Python 3.11 environment: `.venv-logllm`.
- BERT downloaded to `models/bert-base-uncased`.
- Prepared BGL evaluation data downloaded to `data/BGL/test.csv`.
- 4-bit Metal GPU operation passed on this M3 Mac.
- Tiny randomly initialized BERT/projector/Llama inference and adapter save/reload
  passed on Metal. This validates compatibility, not trained-model accuracy.
- Llama 3 8B downloaded to `models/Meta-Llama-3-8B` after account approval/login.
- Real BGL checkpoint evaluation passed on this Mac on September 22, 2026:
  20 selected sequences (10 normal, 10 anomalous), 17 correct predictions.
  Accuracy 0.85, precision 1.0, recall 0.7, F1 0.8235. This small selected sample
  is a functionality check, not a representative benchmark or reproduction of
  the paper's published scores.

## Model access and download (already completed on this laptop)

1. Sign in at https://huggingface.co/meta-llama/Meta-Llama-3-8B.
2. Submit the access form with your real details and accept the terms if you agree.
3. Once approved, create a Read token at https://huggingface.co/settings/tokens.
4. Enter that token only at the terminal login prompt below, not in chat or source code.

```bash
cd /Users/poojasindham/Desktop/gaurdrail
source .venv-logllm/bin/activate
hf auth login
hf auth whoami
hf download meta-llama/Meta-Llama-3-8B --include '*.json' '*.safetensors' --local-dir models/Meta-Llama-3-8B
```

The base model is a roughly 16 GB download. Access approval and login must use the
same account. A 401/403 response is an access/authentication issue, not evidence
that a larger usage plan is needed.

## Run a small evaluation

```bash
cd /Users/poojasindham/Desktop/gaurdrail
source .venv-logllm/bin/activate
python check_macos.py
python eval.py --check-only --data data/BGL/smoke-mixed.csv
python eval.py --device mps --data data/BGL/smoke-mixed.csv --limit 20 --batch-size 1 --output-dir outputs/BGL-mixed-smoke
```

Run these in your normal Mac terminal; a sandbox may hide Metal devices.
The command above uses `data/BGL/smoke-mixed.csv`, containing the first 10 normal
and first 10 anomalous rows from the original BGL test file, with their original
row indices retained in the `SourceRow` column. Results are saved to `outputs/BGL-mixed-smoke/`:
`predictions.csv`, `metrics.json`, and `run.json`.
The selected 20 rows are a smoke test, not a representative benchmark.
An invalid generated label stops evaluation rather than counting it as normal.

After the small run succeeds, increase the number of sequences, keeping the batch
size at 1 on this 16 GB laptop:

```bash
python eval.py --device mps --limit 100 --output-dir outputs/BGL-100
```

`--limit 0` evaluates all rows. Without `--data`, the original BGL `test.csv` is used.
The tested mixed run took about 52 seconds to load the Llama shards and 55 seconds
for inference; timings vary with laptop load and temperature. Existing output filenames are overwritten on another
run; use a different `--output-dir` to retain each run.

Use `python eval.py --help` to select another dataset, checkpoint, or model path.
Datasets must be prepared CSVs with `Content` and binary `Label` columns. Each
sequence's messages are separated by ` ;-; `, matching the upstream preparation.

## Re-create the environment

```bash
uv venv --python 3.11 .venv-logllm
uv pip install --python .venv-logllm/bin/python -r requirements-macos.txt
```

`requirements-macos.txt` records the installed versions used for compatibility
checks. The original `requirements.txt` targets Linux/CUDA.

Downloads already completed on this laptop can be reproduced with:

```bash
source .venv-logllm/bin/activate
hf download google-bert/bert-base-uncased --include config.json model.safetensors tokenizer.json tokenizer_config.json vocab.txt --local-dir models/bert-base-uncased
mkdir -p data/BGL
gdown 1aMKzhrLklnk5RX78UBc3Zx3voIIGnQzo -O data/BGL/test.csv
```

The BGL link is from https://github.com/guanwei49/LogLLM.

## Offline checks

```bash
python -m unittest discover -s tests -p 'test_*.py'
python tests/check_model_backend.py
```

The second command uses tiny random models created in a temporary directory and
requires Metal access. It never substitutes these random weights for the real
models or reports benchmark metrics.
