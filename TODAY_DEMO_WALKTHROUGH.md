# Guardrail walkthrough for today's meeting

For the expanded September 29 walkthrough covering both BGL and Liberty, use [BGL_LIBERTY_WALKTHROUGH.md](BGL_LIBERTY_WALKTHROUGH.md). This older guide documents the original BGL-only presentation.

Today's goal is to demonstrate the working local LogLLM inference path on labeled BGL data, explain the responsibility of each team member, and show inspectable results. This is a progress demonstration of the log-detection component, not proof that the complete Guardrail security-operations platform is finished.

The commands below use the original model path and do not use `demo/`. The presentation helper only reads data and results or illustrates existing preprocessing functions. Only the explicit `eval.py` command runs the real model. No full evaluation needs to run during the meeting.

## 1. Understand these words first

- **Log:** a text record written by a system about something that happened.
- **Message:** one log entry.
- **Sequence:** several messages grouped together so the model can consider their context. Today's selected sequences each contain 100 messages.
- **Dataset:** a collection of examples. Today's dataset is BGL.
- **Normal:** the sequence belongs to the normal class.
- **Anomalous:** the sequence belongs to the unusual/abnormal class. An anomaly is not automatically a cyberattack; it can reflect a system fault or another abnormal condition.
- **Label / ground truth:** the reference answer supplied with the dataset. Here, 0 means normal and 1 means anomalous.
- **Prediction:** the model's answer. We compare it with the reference label to measure correctness.
- **Masking:** replacing matched changing values, such as numeric identifiers, with a placeholder. Here that placeholder is `<*>`.
- **Token:** a piece of text represented numerically for the model. A token is not necessarily a complete word.
- **BERT:** the model that converts each message into a numerical representation.
- **Projection layer:** a learned conversion that makes BERT's representations fit the input representation expected by Llama.
- **Llama:** the model that reads the sequence representation with the classification prompt and generates the normal/anomalous answer.
- **Checkpoint:** saved learned model weights. This project loads existing weights rather than training during the demo.
- **Fine-tuned adapter:** saved task-specific adjustments to a base model. We load the base BERT and Llama models, their BGL adapters, and the saved projection layer.
- **Inference:** using a trained model to make a prediction.
- **Batch size:** the number of sequences processed together. Today it is 1.
- **Window size:** how many messages are grouped in a count-based window. **Stride / step:** how far forward the next window starts.
- **MPS / Metal:** the Apple GPU backend used by this installation.
- **Snort:** the separate signature-based network-detection component in the broader project design. It is not invoked by today's core `eval.py` run.

The architecture in one sentence:

> Prepared log sequences are normalized and tokenized, BERT encodes their messages, a projection layer converts the representations, and Llama predicts normal or anomalous; the evaluator then compares predictions with reference labels and saves the results.

## 2. Exactly how much data and how many types?

The repository provides model/checkpoint configurations for **four named datasets: HDFS, BGL, Liberty, and Thunderbird**. That does not mean four attack types, nor that all four have been evaluated on this laptop.

Only BGL prepared test data is currently downloaded here. Its full test file has **9,427 sequences: 8,610 normal and 817 anomalous**. That full evaluation was stopped and has no completed full-test score to present.

Today's selected sample has **20 sequences: 10 normal and 10 anomalous, with 100 message positions per sequence**. That is 2,000 message positions, not a claim of 2,000 unique messages. The sample contains the first 10 normal and first 10 anomalous rows from the test set; it is not a random or representative benchmark.

There are **two predicted classes: normal and anomalous**. This path does not identify SQL injection, brute force, malware, or other attack categories. It does not output a confidence percentage or an explanation of which message caused its decision.

## 3. Prepare before the professor joins

1. Plug in the laptop and close memory-heavy applications.
2. Open Terminal. Increase its font size so the professor can read it.
3. Keep this guide open in a separate window.
4. Assign one terminal operator, preferably Pooja. Each member speaks when their stage is shown; nobody needs to change laptops.
5. Paste commands one block at a time. Wait for the command prompt to return before pasting the next block.
6. Do not log into Hugging Face or display tokens during the meeting. The local models and credentials are already set up.

Run:

```bash
cd /Users/poojasindham/Desktop/gaurdrail
source .venv-logllm/bin/activate
python eval.py --check-only --data data/BGL/smoke-mixed.csv --limit 20
```

Expected last line:

```text
PASS: required local files exist; 20 sequences selected.
```

This verifies required files and the selected input, not inference accuracy. Check the saved fallback result:

```bash
python presentation_walkthrough.py results
```

That should show the completed earlier run: 10 correctly identified normal sequences, 7 detected anomalies, and 3 missed anomalies. This command does not load Llama.

## 4. Opening — Pooja — about 1 minute

Say:

> Our project is Guardrail. Its broader goal is to combine log-based anomaly detection with network security evidence so that an analyst can inspect suspicious activity. Today we are demonstrating the working log-model component on our laptop, from prepared input sequences to actual model predictions and saved evaluation results.
>
> We use the existing open-source LogLLM architecture and its fine-tuned checkpoints. Our current local setup loads the real BERT and Llama models. This demonstration uses a small labeled BGL sample so the inference can finish during the meeting.

Then explain the stages in plain language:

> First we normalize the input messages. Next we organize messages into sequences and batches. BERT converts the messages into numerical representations, the projection layer converts those representations for Llama, and Llama generates the classification. Finally, we compare the classification with the known label and save the outputs.

Do not introduce this as a completed Snort-correlation or cloud-authentication demo.

## 5. Input and preprocessing — Nikhil — about 2 minutes

Run:

```bash
python presentation_walkthrough.py inputs
```

Say:

> My assigned responsibility is ingestion and preprocessing: making sure the input has the right structure before it reaches sequence processing and inference. Today we begin with a prepared public BGL CSV. Each row is a sequence, rather than one individual log message.
>
> `Content` contains the messages, `Label` contains the reference answer, and `SourceRow` points back to the original test-file row. SourceRow uses zero-based numbering and does not count the CSV header. We selected 10 normal and 10 anomalous sequences so both classes are visible in this short demonstration.

Point to the displayed message excerpts. Say:

> These are actual excerpts from the selected BGL data. We show only three messages here for readability, but each selected sequence contains 100 messages.

Run:

```bash
python presentation_walkthrough.py preprocessing
```

The actual example shown includes:

```text
Before: iar 00106210 dear 0244c20c
After:  iar <*> dear <*>
```

Say:

> This runs the masking function used by the dataset loader. It replaces matched changing values with a common placeholder while retaining the surrounding text. The purpose is to reduce variation from identifiers and similar values. This function is part of the upstream LogLLM implementation we are using.
>
> This stage demonstrates normalization of prepared message content. We are not claiming that this command demonstrates a complete raw-log parser or malformed-line rejection system.

Handoff:

> Pooja will now explain how these messages are grouped and passed through the execution pipeline.

## 6. Sequences and execution — Pooja — about 2 minutes

Run:

```bash
python presentation_walkthrough.py sequences
```

Say:

> My assigned responsibility is sequence generation, batching, and pipeline execution. A sequence lets the model examine several messages together. A batch controls how many sequences are processed at the same time; these are different settings.
>
> The actual BGL sample already contains groups of 100 messages. We use batch size 1 to keep memory use manageable on this laptop. The current model input limits are 128 messages per sequence and 100 BERT tokens per message. Those limits truncate long inputs; they do not rebuild the dataset's windows.

Explain the illustration:

> This small example uses six numbered events to make windowing easy to understand. It calls the existing upstream window helper. With window size 3 and step 3, the groups are events 1–3 and 4–6. With step 2, the groups overlap. The helper also retains a shorter final group.
>
> The labels in this small illustration are invented reference labels to explain grouping. The window's reference label is anomalous if any member event is labeled anomalous. This is a ground-truth construction rule, not the neural model's prediction rule. The actual BGL model run still uses the unchanged prepared sample.

Explain verified local work:

> The local setup now supports Apple Metal inference, explicit device and input selection, a small-run limit, batch-size control, and saved outputs. Reading only the selected CSV rows also avoids preprocessing the full dataset when we request a short run.

Handoff:

> Vijaya will run the real fine-tuned model and explain how we measure its predictions.

## 7. Real inference — Vijaya — about 2 minutes, depending on the laptop

Run this once during the meeting:

```bash
python eval.py --device mps --dataset BGL --data data/BGL/smoke-mixed.csv --limit 20 --batch-size 1 --output-dir outputs/BGL-meeting-live
```

This uses a separate output folder so the earlier completed result is retained. If this same live folder already contains a previous rehearsal, use a new name such as `outputs/BGL-meeting-live-2`, and use that name in subsequent results commands as well.

Explain the command:

> `mps` selects the Mac's GPU. `BGL` selects the BGL checkpoint. The data argument selects our prepared sample. The limit keeps the run to 20 sequences. Batch size 1 means one sequence at a time. The output directory is where the completed predictions and metrics will be saved.

While it loads, say:

> My assigned responsibility is model inference and evaluation. This command loads the base BERT and Llama models, the BGL fine-tuned adapters, and the saved projection layer. We are using existing fine-tuned weights, not training a new model during the presentation.
>
> BERT converts each message to a numerical representation. The projection layer converts it to the representation size expected by Llama. Llama then generates the sequence's normal or anomalous classification.
>
> The reference labels are used after prediction to evaluate correctness. They are not passed as answers into the model's inference call.

The earlier run took about 52 seconds to load Llama shards and 55 seconds for inference, plus other overhead. That is an observation, not a guaranteed time. Let the command finish. If it is still running, Viswa can verbally explain the output files while you wait.

Do not use `--limit 0`: that requests all sequences in the chosen file, and on the default test file would start the long evaluation again. Do not run `train.py` during this demo.

## 8. Inspect results — Vijaya and Viswa — about 3 minutes

After the live command completes successfully, run:

```bash
python presentation_walkthrough.py results --output-dir outputs/BGL-meeting-live
```

The helper reads the new results, checks that row order and labels match the recorded input, and recomputes metrics from the predictions. It shows a correct normal example, a detected anomaly, and a missed anomaly if each exists in that particular run. The input excerpts shown are not model-generated explanations or evidence attribution.

Vijaya says:

> We are now inspecting the completed live run. A correct normal is a normal sequence predicted normal. A detected anomaly is an anomalous sequence predicted anomalous. A false alarm is a normal sequence predicted anomalous. A missed anomaly is an anomalous sequence predicted normal.

Read the actual numbers from the new run. Do not recite the earlier result if the new output differs.

For the earlier completed run, the interpretation is:

- **Accuracy 85%:** 17 of the 20 predictions were correct.
- **Precision 100%:** all 7 sequences flagged anomalous were labeled anomalous. This does not mean all anomalies were found.
- **Recall 70%:** 7 of the 10 labeled anomalies were detected; 3 were missed.
- **F1 about 82.35%:** a score combining precision and recall.
- There were 10 correct normal predictions, 7 detected anomalies, 0 false alarms, and 3 missed anomalies.

Say:

> This small selected sample establishes that the real model pipeline runs and that its outputs can be inspected. It does not establish full-dataset accuracy, generalization to cloud logs, or superiority over another method. We also show the missed anomalies because those errors are part of the result.

Viswa says:

> My assigned responsibility is configuration, structured outputs, and making the results understandable. This run produces three files. `predictions.csv` stores the reference label, predicted class, and generated model text for each sequence. `metrics.json` stores the aggregate scores. `run.json` records the input path, checkpoint, device, and sequence and batch settings.
>
> These files allow us to inspect the result after the presentation and compare runs with their recorded settings. The presentation helper checks the metric arithmetic against the predictions. It is not a complete data-provenance or train/test-leakage audit.

To show the files directly:

```bash
cat outputs/BGL-meeting-live/metrics.json
cat outputs/BGL-meeting-live/run.json
head -n 8 outputs/BGL-meeting-live/predictions.csv
```

If asked about contextual summaries, confidence, split validation, or unified severity, say they are not demonstrated by this core path. CSV/JSON export should not be described as a completed ContextAnalyzer or ConfigManager implementation.

## 9. Closing — Pooja — about 1 minute

Say:

> Today we showed the actual local log-model path: prepared BGL inputs, normalization, sequence and batch handling, real BERT-plus-Llama inference, and saved evaluation outputs. The integration runs on our Mac using the existing fine-tuned checkpoints.
>
> The complete Guardrail platform still needs further integration and validation. Following the previous meeting's feedback, our next work is to evaluate larger labeled samples, compare sequence-window settings and runtime behavior, and build an evidence-based correlation path between model results and relevant Snort alerts. A focused security-operation scenario will make that contribution easier to evaluate.

Only commit to dates and ownership that the team has agreed on. Do not claim the correlation system or agent AI is already complete.

## 10. What can we accurately say we implemented?

Use this team-level wording:

> We integrated and adapted the existing LogLLM implementation for local Apple Silicon inference, configured the models and BGL checkpoints, added a controllable evaluation command with file checks and bounded input loading, and added structured prediction, metric, and run-setting outputs. We verified real inference on a selected labeled sample. We also prepared a presentation helper that exposes the data, masking, windowing behavior, and saved results.

The local changes are visible in `model.py`, `eval.py`, `customDataset.py`, `check_macos.py`, `requirements-macos.txt`, `RUN_LOCAL.md`, the check scripts under `tests/`, and `presentation_walkthrough.py`.

The underlying BERT–projection–Llama architecture, pretrained bases, BGL fine-tuned checkpoints, original masking function, and original window helpers should be credited to their upstream sources. The selected BGL data is public prepared evaluation data.

The individual speaking parts above follow the latest local contribution documents:

- Nikhil: input ingestion, preprocessing, and validation responsibilities.
- Pooja: sequence generation, batching, and execution responsibilities.
- Vijaya: inference and evaluation responsibilities, with correlation identified as next work in the meeting summary.
- Viswa: configuration, output packaging, split validation, and contextual-analysis responsibilities.

These are ownership areas, not verified authorship of every displayed function. Each member should say “my responsibility is …” and then describe only work they actually performed. Do not claim authorship of upstream code or assign recent changes to a particular teammate without confirming that history. Follow your course's rules for acknowledging coding assistance.

## 11. Questions the professor may ask

**Is the whole project finished?**

> The demonstrated log-model path is working on this laptop. The broader Guardrail platform, including integrated network correlation and operational summaries, is not established as complete by this run.

**Did you develop or train BERT and Llama?**

> No. We use pretrained base models and the existing LogLLM fine-tuned checkpoint. Our demonstrated work concerns local integration, execution, and evaluation around that model.

**What is your contribution beyond cloning a repository?**

> Today's concrete work is making the real model path run reproducibly on this laptop and exposing its inputs and evaluation artifacts. That is engineering progress, not a new detection method. Our proposed Guardrail contribution is the operational integration and evidence-based correlation, which still needs implementation and evaluation.

**Why only 20 sequences?**

> It is a short functionality demonstration with both classes represented. The full local BGL test set has 9,427 sequences. We stopped the long evaluation and are not reporting a full-test score.

**Why is your score different from the paper?**

> This selected 20-sequence run is not the paper's evaluation protocol. The local runtime also uses its own hardware and numerical configuration. We cannot directly compare those scores or attribute the difference to one cause without a controlled experiment.

**Does anomalous mean an attack?**

> No. It is a binary anomaly classification. Confirming a security incident requires context and other evidence.

**Where is Snort in this run?**

> It is not invoked by this command. Today we are verifying the core log-model path. We are not presenting this run as an integrated network-correlation test.

**Can it classify any log I paste into it?**

> The code expects prepared sequences and uses a dataset-specific checkpoint. We have validated this local run on BGL, not arbitrary application or cloud logs. New log sources need suitable preparation and their own validation.

**Where are confidence and attack types?**

> The current inference output is normal or anomalous. It does not export a calibrated confidence score or attack category. Those should not be inferred from the displayed text or from aggregate accuracy.

**What did changing the window size prove?**

> The six-event example demonstrates grouping behavior only. It does not measure accuracy at different window sizes. That experiment would require regenerating appropriately labeled sequences and evaluating them under a controlled protocol.

**Why did the model miss those three anomalies?**

> We observed that it predicted normal for three labeled anomalies. This run does not explain the cause. We need error analysis and controlled checks rather than guessing from a short excerpt.

## 12. If the live run fails or time runs out

In your normal Terminal, press Control-C once to stop the running evaluation and wait for the command prompt. Then run:

```bash
python presentation_walkthrough.py results --output-dir outputs/BGL-mixed-smoke
```

Say:

> We will show the saved outputs from our earlier successful run on this laptop. These are completed model outputs from the selected BGL sample; they are not the results of the interrupted live run.

If the error says MPS is unavailable, confirm that you are using the Mac's normal Terminal and the activated environment. Do not change to a full CPU evaluation during the meeting. Inspect the error after the presentation.

`eval.py` saves the result bundle after evaluation completes. Do not present partial or old contents of a failed live-run directory as a new successful result.

## 13. Command card

Run these in order, with each person's explanation between commands:

```bash
cd /Users/poojasindham/Desktop/gaurdrail
source .venv-logllm/bin/activate
python eval.py --check-only --data data/BGL/smoke-mixed.csv --limit 20
python presentation_walkthrough.py inputs
python presentation_walkthrough.py preprocessing
python presentation_walkthrough.py sequences
python eval.py --device mps --dataset BGL --data data/BGL/smoke-mixed.csv --limit 20 --batch-size 1 --output-dir outputs/BGL-meeting-live
python presentation_walkthrough.py results --output-dir outputs/BGL-meeting-live
cat outputs/BGL-meeting-live/metrics.json
cat outputs/BGL-meeting-live/run.json
head -n 8 outputs/BGL-meeting-live/predictions.csv
```

Fallback for saved results only:

```bash
python presentation_walkthrough.py results --output-dir outputs/BGL-mixed-smoke
```
