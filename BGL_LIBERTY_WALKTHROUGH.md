# BGL and Liberty presentation walkthrough

Prepared September 29, 2026. This guide extends the original BGL presentation to Liberty using the existing architecture and dataset-specific checkpoints. It does not add a new detector, retrain models, or use demo/.

## Open the presentation

[Open the offline browser presentation](presentations/BGL-Liberty/index.html). Double-click the HTML file in Finder to open it in a browser; no server or internet is required to view its saved evidence. The source links require internet. While the local server is running, use http://127.0.0.1:8765/.

Use the dataset selector to switch between BGL and Liberty. Use Next/Previous, the stage buttons, or left/right arrow keys. Speaking notes can be shown or hidden. This presentation displays saved observations; it does not run inference.

## Opening statement

> Last time we verified the BGL inference path. We have now run the corresponding Liberty checkpoint on a selected labeled sample as well. Today we will show the source links, what each input looks like, how it changes through the existing pipeline, and the completed predictions.

## Results we can report

- BGL: earlier selected 20-sequence run, 17 correct, 10 correct normal predictions, 7 detected anomalies, 3 missed anomalies, and 0 false alarms. Accuracy 85%, precision 100%, recall 70%, F1 82.35%.
- Liberty: new selected 20-sequence run, 20 correct, 10 correct normal predictions, 10 detected anomalies, 0 missed anomalies, and 0 false alarms. Accuracy/precision/recall/F1 are 100% on this selected sample only.
- Each sample is the first 10 normal and first 10 anomalous rows from the authors’ prepared test CSV. This is not random sampling, not a full benchmark, and not evidence that Liberty is generally easier or that the model achieves 100% overall accuracy.
- Each dataset uses its own checkpoint. The base models are shared.
- The BGL numerical trace comes from a separate one-sequence run, not a new 20-sequence benchmark. Its output agrees with the corresponding earlier prediction. Liberty’s trace comes from the first batch of the new 20-sequence run.

## Before presenting

```bash
cd /Users/poojasindham/Desktop/gaurdrail
source .venv-logllm/bin/activate
python eval.py --dataset BGL --data data/BGL/smoke-mixed.csv --limit 20 --check-only
python eval.py --dataset Liberty --data data/Liberty/smoke-mixed.csv --limit 20 --check-only
```

## Walk through each dataset

Run these lightweight commands for Liberty; replace Liberty with BGL for the earlier dataset. They do not run the neural models.

```bash
python presentation_walkthrough.py sources --dataset Liberty
python presentation_walkthrough.py raw --dataset Liberty
python presentation_walkthrough.py inputs --dataset Liberty
python presentation_walkthrough.py preprocessing --dataset Liberty
python presentation_walkthrough.py sequences --dataset Liberty
python presentation_walkthrough.py tokens --dataset Liberty
python presentation_walkthrough.py trace --dataset Liberty
python presentation_walkthrough.py results --dataset Liberty
```

## Stage-by-stage speaking script

### 1. Source data and the file used today — Pooja

BGL has 9,427 prepared test sequences locally. Our presentation uses the first 10 normal and first 10 anomalous sequences. Original logs, prepared CSVs, and our selected sample are different artifacts.

**Say:**

> We use the authors’ prepared BGL test file. We selected twenty sequences for a short functionality check. The original sources are linked here; we did not collect these logs ourselves.

**BGL command:**

```bash
python presentation_walkthrough.py sources --dataset BGL
```

**BGL evidence:**

Local input:

```text
/Users/poojasindham/Desktop/gaurdrail/data/BGL/smoke-mixed.csv
```

Full prepared test label counts:

```text
{
  "normal": 8610,
  "anomalous": 817
}
```

- [Original description](https://github.com/logpai/loghub/tree/master/BGL)
- [Original download](https://zenodo.org/records/8196385/files/BGL.zip?download=1)
- [Prepared test](https://drive.google.com/file/d/1aMKzhrLklnk5RX78UBc3Zx3voIIGnQzo/view)
- [LogLLM authors’ preparation and test links](https://github.com/guanwei49/LogLLM)

**Liberty command:**

```bash
python presentation_walkthrough.py sources --dataset Liberty
```

**Liberty evidence:**

Local input:

```text
/Users/poojasindham/Desktop/gaurdrail/data/Liberty/smoke-mixed.csv
```

Full prepared test label counts:

```text
{
  "normal": 9349,
  "anomalous": 651
}
```

- [Original description](https://www.usenix.org/cfdr-data#hpc4)
- [Original download](http://0b4af6cdc2f0c5998459-c0245c5c937c5dedcca3f1764ecc9b2f.r43.cf2.rackcdn.com/hpc4/liberty2.gz)
- [Prepared test](https://drive.google.com/file/d/1-Z2FrsRSm8ojfOW1555obNyU6B_aRDTH/view)
- [LogLLM authors’ preparation and test links](https://github.com/guanwei49/LogLLM)

### 2. Original log record and parsed fields — Nikhil

Actual public-source excerpt parsed using the repository’s format regex. This is a separate format illustration, not a reconstruction of the selected test sequence. The entire raw archive was not reprocessed locally.

**Say:**

> This shows how the original record is separated into fields. The Content field holds the message. In upstream preparation, a dash label maps to normal. The existing parser skips unmatched lines, so we do not describe it as a complete validation system.

**BGL command:**

```bash
python presentation_walkthrough.py raw --dataset BGL
```

**BGL evidence:**

Original record:

```text
- 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.675872 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected
```

Parsed fields:

```text
{
  "Label": "-",
  "Id": "1117838570",
  "Date": "2005.06.03",
  "Code1": "R02-M1-N0-C:J12-U11",
  "Time": "2005-06-03-15.42.50.675872",
  "Code2": "R02-M1-N0-C:J12-U11",
  "Component1": "RAS",
  "Component2": "KERNEL",
  "Level": "INFO",
  "Content": "instruction cache parity error corrected"
}
```

Excerpt provenance:

```text
{
  "source": "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log",
  "note": "First three source lines; separate illustration, not proven to be the origin rows of the selected prepared sequences."
}
```

**Liberty command:**

```bash
python presentation_walkthrough.py raw --dataset Liberty
```

**Liberty evidence:**

Original record:

```text
- 1102911148 2004.12.12 ladmin2 Dec 12 20:12:28 src@ladmin2 .... IRQ redirection table:
```

Parsed fields:

```text
{
  "Label": "-",
  "Id": "1102911148",
  "Date": "2004.12.12",
  "Admin": "ladmin2",
  "Month": "Dec",
  "Day": "12",
  "Time": "20:12:28",
  "AdminAddr": "src@ladmin2",
  "Content": ".... IRQ redirection table:"
}
```

Excerpt provenance:

```text
{
  "source": "http://0b4af6cdc2f0c5998459-c0245c5c937c5dedcca3f1764ecc9b2f.r43.cf2.rackcdn.com/hpc4/liberty2.gz",
  "source_line_numbers_one_based": [
    8,
    9,
    10
  ],
  "note": "Three complete source lines; separate parsing illustration, not the origin rows of our selected test sequences."
}
```

### 3. Prepared sequence and reference label — Nikhil

The preparation script maps event labels to 0/1, splits the structured data 80/20, and forms count-based windows of 100 messages with step 100. A window reference label is 1 if any event label is 1. This describes the provided code; the exact historical run was not reproduced here.

**Say:**

> Each CSV row is a sequence. These are the first three messages of sample row zero, not the whole sequence. The label is an answer key for evaluation and is not passed to the inference model.

**BGL command:**

```bash
python presentation_walkthrough.py inputs --dataset BGL
```

**BGL evidence:**

Selected row metadata:

```text
{
  "sample_index": 0,
  "SourceRow": 0,
  "Label": 0,
  "messages": 100
}
```

Content excerpt; messages separated by ;-;:

```text
iar 00106210 dear 0244c20c ;-; iar 00106210 dear 0244c23c ;-; iar 00106210 dear 0244c20c
```

Prepared CSV columns:

```text
[
  "Content",
  "Label",
  "item_Label",
  "session_length"
]
```

**Liberty command:**

```bash
python presentation_walkthrough.py inputs --dataset Liberty
```

**Liberty evidence:**

Selected row metadata:

```text
{
  "sample_index": 0,
  "SourceRow": 0,
  "Label": 0,
  "messages": 100
}
```

Content excerpt; messages separated by ;-;:

```text
kernel: LustreError: 2032:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054168) #105#@f72d1200 x540847/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0 ;-; kernel: LustreError: 1965:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054168) #105#@f3cbb000 x150476/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0 ;-; kernel: LustreError: 2084:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054169) #105#@e6f51e00 x547988/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0
```

Prepared CSV columns:

```text
[
  "Content",
  "Label",
  "item_Label",
  "session_length"
]
```

### 4. Normalization before BERT — Nikhil

CustomDataset applies replace_patterns() to Content. Regexes mask matched numeric values, IP addresses, paths, and other patterns as <*>. Repeated dots are reduced. The tokenizer later lowercases text. This is the existing LogLLM preprocessing, not a newly trained parser.

**Say:**

> Here are the same actual messages before and after normalization. The text becomes more consistent, but values are removed and this can lose information. A word such as error does not by itself establish the reference class.

**BGL command:**

```bash
python presentation_walkthrough.py preprocessing --dataset BGL
```

**BGL evidence:**

Before:

```text
iar 00106210 dear 0244c20c
iar 00106210 dear 0244c23c
iar 00106210 dear 0244c20c
```

After:

```text
iar <*> dear <*>
iar <*> dear <*>
iar <*> dear <*>
```

**Liberty command:**

```bash
python presentation_walkthrough.py preprocessing --dataset Liberty
```

**Liberty evidence:**

Before:

```text
kernel: LustreError: 2032:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054168) #105#@f72d1200 x540847/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0
kernel: LustreError: 1965:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054168) #105#@f3cbb000 x150476/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0
kernel: LustreError: 2084:0:(client.c:823:ptlrpc_expire_one_request()) @@@ timeout (sent 1126054169) #105#@e6f51e00 x547988/t0 o38->#104#@NID_3712519978_UUID:12 lens 168/64 ref 2 fl Rpc:/0/0 rc 0/0
```

After:

```text
kernel: LustreError: <*>(<*>()) @@@ timeout (sent <*>) #<*>#@<*> <*> <*>>#<*>#@<*> lens <*> ref <*> fl <*> rc <*>
kernel: LustreError: <*>(<*>()) @@@ timeout (sent <*>) #<*>#@<*> <*> <*>>#<*>#@<*> lens <*> ref <*> fl <*> rc <*>
kernel: LustreError: <*>(<*>()) @@@ timeout (sent <*>) #<*>#@<*> <*> <*>>#<*>#@<*> lens <*> ref <*> fl <*> rc <*>
```

### 5. Sequence boundaries and batch construction — Pooja

Content is split on the exact delimiter " ;-; ". CustomCollator keeps at most 128 messages per sequence, combines messages for BERT tokenization, and records boundaries. Our saved run uses batch size 1.

**Say:**

> A sequence is a group of messages; a batch is a group of sequences. Here there are one hundred messages in one sequence. The empty boundary list means no split is needed between multiple sequences in this batch.

**BGL command:**

```bash
python presentation_walkthrough.py sequences --dataset BGL
```

**Liberty command:**

```bash
python presentation_walkthrough.py sequences --dataset Liberty
```

### 6. Actual BERT tokenizer output — Nikhil / Pooja

The local BERT tokenizer converts text into WordPiece tokens and integer IDs. [CLS] and [SEP] are special tokens; ## means a continuing word piece. Padding makes message rows equal length. The attention mask is 1 for included tokens and 0 for padding, not an anomaly indicator.

**Say:**

> These are actual tokens and token IDs for the first message. The input tensor has one row per message. The second dimension depends on the longest tokenized message in this batch, up to the configured limit.

**BGL command:**

```bash
python presentation_walkthrough.py tokens --dataset BGL
```

**BGL evidence:**

Tokens, first message:

```text
[
  "[CLS]",
  "ia",
  "##r",
  "<",
  "*",
  ">",
  "dear",
  "<",
  "*",
  ">",
  "[SEP]"
]
```

Token IDs, first message:

```text
[
  101,
  24264,
  2099,
  1026,
  1008,
  1028,
  6203,
  1026,
  1008,
  1028,
  102
]
```

Input tensor shape and attention mask:

```text
{
  "shape": [
    100,
    11
  ],
  "mask": [
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1
  ]
}
```

**Liberty command:**

```bash
python presentation_walkthrough.py tokens --dataset Liberty
```

**Liberty evidence:**

Tokens, first message:

```text
[
  "[CLS]",
  "kernel",
  ":",
  "lust",
  "##ree",
  "##rro",
  "##r",
  ":",
  "<",
  "*",
  ">",
  "(",
  "<",
  "*",
  ">",
  "(",
  ")",
  ")",
  "@",
  "@",
  "@",
  "time",
  "##out",
  "(",
  "sent",
  "<",
  "*",
  ">",
  ")",
  "#",
  "<",
  "*",
  ">",
  "#",
  "@",
  "<",
  "*",
  ">",
  "<",
  "*",
  ">",
  "<",
  "*",
  ">",
  ">",
  "#",
  "<",
  "*",
  ">",
  "#",
  "@",
  "<",
  "*",
  ">",
  "lens",
  "<",
  "*",
  ">",
  "ref",
  "<",
  "*",
  ">",
  "fl",
  "<",
  "*",
  ">",
  "rc",
  "<",
  "*",
  ">",
  "[SEP]"
]
```

Token IDs, first message:

```text
[
  101,
  16293,
  1024,
  11516,
  9910,
  18933,
  2099,
  1024,
  1026,
  1008,
  1028,
  1006,
  1026,
  1008,
  1028,
  1006,
  1007,
  1007,
  1030,
  1030,
  1030,
  2051,
  5833,
  1006,
  2741,
  1026,
  1008,
  1028,
  1007,
  1001,
  1026,
  1008,
  1028,
  1001,
  1030,
  1026,
  1008,
  1028,
  1026,
  1008,
  1028,
  1026,
  1008,
  1028,
  1028,
  1001,
  1026,
  1008,
  1028,
  1001,
  1030,
  1026,
  1008,
  1028,
  10014,
  1026,
  1008,
  1028,
  25416,
  1026,
  1008,
  1028,
  13109,
  1026,
  1008,
  1028,
  22110,
  1026,
  1008,
  1028,
  102
]
```

Input tensor shape and attention mask:

```text
{
  "shape": [
    100,
    71
  ],
  "mask": [
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1
  ]
}
```

### 7. BERT output with the dataset adapter — Vijaya

BERT receives token IDs and attention masks. The code uses pooler_output: one 768-number vector per message. The values below were captured during real inference with the matching adapter; they are not probabilities or human-readable explanations.

**Say:**

> BERT changes each message into a numerical representation. For one hundred messages, the observed output contains one hundred vectors of 768 values each. We display only eight values from the first vector.

**BGL command:**

```bash
python presentation_walkthrough.py trace --dataset BGL
```

**BGL evidence:**

Observed BERT output:

```text
{
  "shape": [
    100,
    768
  ],
  "dtype": "torch.float16",
  "first_eight_values": [
    -0.71875,
    -0.1968994140625,
    0.38525390625,
    0.55908203125,
    -0.111083984375,
    -0.06024169921875,
    0.67041015625,
    0.045166015625
  ]
}
```

Adapter folder:

```text
/Users/poojasindham/Desktop/gaurdrail/ft_model_BGL/Bert_ft
```

**Liberty command:**

```bash
python presentation_walkthrough.py trace --dataset Liberty
```

**Liberty evidence:**

Observed BERT output:

```text
{
  "shape": [
    100,
    768
  ],
  "dtype": "torch.float16",
  "first_eight_values": [
    -0.74072265625,
    -0.54541015625,
    -0.86376953125,
    0.53759765625,
    0.5400390625,
    -0.287353515625,
    0.2174072265625,
    0.4130859375
  ]
}
```

Adapter folder:

```text
/Users/poojasindham/Desktop/gaurdrail/ft_model_Liberty/Bert_ft
```

### 8. Projection into Llama’s representation size — Vijaya

The learned linear projection converts each 768-value BERT vector into a 4,096-value vector. The code then casts the projected vectors to float16 before building the Llama input.

**Say:**

> This layer connects the two models. It changes the representation size, not the number of messages, and loads its learned weights from projector.pt.

**BGL command:**

```bash
python presentation_walkthrough.py trace --dataset BGL
```

**BGL evidence:**

Observed projection output before float16 cast:

```text
{
  "shape": [
    100,
    4096
  ],
  "dtype": "torch.float32",
  "first_eight_values": [
    -2.052311420440674,
    0.110897958278656,
    0.2268199622631073,
    0.6610448956489563,
    0.9206374883651733,
    -1.9726778268814087,
    1.1101058721542358,
    0.4854617714881897
  ]
}
```

Saved weights:

```text
/Users/poojasindham/Desktop/gaurdrail/ft_model_BGL/projector.pt
```

**Liberty command:**

```bash
python presentation_walkthrough.py trace --dataset Liberty
```

**Liberty evidence:**

Observed projection output before float16 cast:

```text
{
  "shape": [
    100,
    4096
  ],
  "dtype": "torch.float32",
  "first_eight_values": [
    -0.9259205460548401,
    -0.7525415420532227,
    -1.7194838523864746,
    -2.4591877460479736,
    -0.9016880393028259,
    0.314546674489975,
    -1.0119361877441406,
    0.3773966133594513
  ]
}
```

Saved weights:

```text
/Users/poojasindham/Desktop/gaurdrail/ft_model_Liberty/projector.pt
```

### 9. Llama input and generated response — Vijaya

Llama receives embeddings: instruction text embeddings, projected log vectors, question embeddings, and the answer prefix. It generates a short answer token by token using argmax. Reference labels are not included.

**Say:**

> Llama does not simply receive the original CSV text. It receives this combined numerical input. The actual captured shape includes the log-message positions plus prompt positions. The output token IDs decode into the classification text.

**BGL command:**

```bash
python presentation_walkthrough.py trace --dataset BGL
```

**BGL evidence:**

Prompt around the projected messages:

```text
Below is a sequence of system log messages: [projected log vectors] . Is this sequence normal or anomalous? \n The sequence is
```

Observed Llama input:

```text
{
  "shape": [
    1,
    124,
    4096
  ],
  "dtype": "torch.float16",
  "first_eight_values": [
    -0.0001430511474609375,
    0.00010776519775390625,
    -0.0001964569091796875,
    3.170967102050781e-05,
    0.0001239776611328125,
    -0.000370025634765625,
    0.00830078125,
    -0.0033416748046875
  ],
  "attention_mask_shape": [
    1,
    124
  ],
  "composition": "instruction embeddings + projected message vectors + question embeddings + answer-prefix embeddings"
}
```

Actual generated output:

```text
{
  "token_ids": [
    [
      4725,
      13,
      128001
    ]
  ],
  "decoded": [
    " normal."
  ]
}
```

**Liberty command:**

```bash
python presentation_walkthrough.py trace --dataset Liberty
```

**Liberty evidence:**

Prompt around the projected messages:

```text
Below is a sequence of system log messages: [projected log vectors] . Is this sequence normal or anomalous? \n The sequence is
```

Observed Llama input:

```text
{
  "shape": [
    1,
    124,
    4096
  ],
  "dtype": "torch.float16",
  "first_eight_values": [
    -0.0001430511474609375,
    0.00010776519775390625,
    -0.0001964569091796875,
    3.170967102050781e-05,
    0.0001239776611328125,
    -0.000370025634765625,
    0.00830078125,
    -0.0033416748046875
  ],
  "attention_mask_shape": [
    1,
    124
  ],
  "composition": "instruction embeddings + projected message vectors + question embeddings + answer-prefix embeddings"
}
```

Actual generated output:

```text
{
  "token_ids": [
    [
      4725,
      13,
      128001
    ]
  ],
  "decoded": [
    " normal."
  ]
}
```

### 10. Prediction records and correctness — Vijaya / Viswa

The evaluator maps generated normal/anomalous text to 0/1, then compares it with the separate reference labels. These are saved results from completed inference, not a live model running inside this presentation.

**Say:**

> Prediction is the model’s answer. Label is the reference answer. Matching values mean a correct prediction; a label of one with a prediction of zero is a missed anomaly. These are sequence-level decisions, not identified attack types.

**BGL command:**

```bash
python presentation_walkthrough.py results --dataset BGL
```

**Liberty command:**

```bash
python presentation_walkthrough.py results --dataset Liberty
```

### 11. Evaluation and reproducibility — Viswa

Metrics below are recomputed and checked against the saved predictions. Both samples were deliberately balanced and selected, not representative benchmarks. Each dataset uses its own adapter checkpoint; this is not a cross-dataset generalization test.

**Say:**

> We retain predictions, metrics, and run settings. These small evaluations establish that the two dataset-specific paths execute. They do not establish overall accuracy on the full datasets or explain every model error.

**BGL command:**

```bash
python presentation_walkthrough.py results --dataset BGL
```

**Liberty command:**

```bash
python presentation_walkthrough.py results --dataset Liberty
```

## Important questions

**Did you reprocess both full raw datasets yourself?** No. We downloaded the authors’ prepared test CSVs. We separately fetched three public raw-source lines for each dataset and exercised the existing format parser to explain that upstream step. Those raw excerpts are not the origin lines of the selected sample.

**What preparation does the repository describe?** The count-window script extracts fields, converts raw labels, splits the structured rows 80/20, and groups 100-message windows with step 100. For Liberty, the README instructs using raw lines 40,000,000–45,000,000. We have not independently reproduced the historical generation of the distributed CSVs.

**Does Content include the original timestamp and header?** The prepared CSV uses extracted message content. Header fields are not generally retained as separate model inputs. SourceRow refers to the prepared CSV row, not a raw-log line number.

**What gets normalized?** The existing regex function masks patterns such as numeric identifiers, IP addresses and paths. It also handles booleans, number words and date-related patterns, and reduces repeated dots. Tokenization then lowercases text. Masking removes information and should not be described as guaranteed accuracy improvement.

**Why can Liberty normal examples contain LustreError?** Normal/anomalous follows the dataset reference labels and model output. The presence of the word error is not sufficient to determine the label. We have not established a causal explanation of these labels or predictions.

**Do the displayed SSH messages prove a login attack?** No. They are excerpts from a sequence labeled anomalous. We do not identify the causal line, an attack type, or an authentication-template match.

**What do the embedding numbers mean?** They are actual learned numerical representations. Individual coordinates have no provided plain-language meaning and are not confidence percentages.

**Was Snort invoked?** No. This walkthrough covers the existing log-model path.

**Did we train these checkpoints?** Their use is verified; their authorship is not. Claim team-produced Colab checkpoints only if these files are the corresponding saved outputs.

## Optional fresh live inference

The presentation is ready without re-running models. To make a fresh Liberty run, use a new output directory so saved results remain intact:

```bash
python eval.py --device mps --dataset Liberty --data data/Liberty/smoke-mixed.csv --limit 20 --batch-size 1 --output-dir outputs/Liberty-meeting-live --trace-output outputs/Liberty-meeting-live/pipeline-trace.json
python presentation_walkthrough.py results --dataset Liberty --output-dir outputs/Liberty-meeting-live
python presentation_walkthrough.py trace --dataset Liberty --trace-file outputs/Liberty-meeting-live/pipeline-trace.json
```

For BGL, replace Liberty with BGL in the dataset, data path, and output paths. Do not run both large models concurrently on this laptop. Do not use --limit 0 for the meeting.

The HTML presentation is a saved snapshot of the named completed runs, not automatically linked to a new meeting output. The builder checks the saved BGL-mixed-smoke and Liberty-mixed-smoke folders. To rebuild after intentionally updating those runs:

```bash
python build_pipeline_presentation.py
```

## Evidence files

- data/BGL/test.csv and data/Liberty/test.csv: authors’ prepared test files.
- data/<dataset>/smoke-mixed.csv: selected samples with SourceRow.
- data/<dataset>/raw-excerpt.log and raw-excerpt.source.json: separate original-source parsing illustrations.
- outputs/BGL-mixed-smoke and outputs/Liberty-mixed-smoke: completed 20-sequence outputs.
- outputs/BGL-trace-example/pipeline-trace.json: one-sequence BGL trace.
- outputs/Liberty-mixed-smoke/pipeline-trace.json: first-batch Liberty trace.
- presentations/BGL-Liberty/pipeline-evidence.json: presentation data and current file hashes. Hashes capture the files now; they do not establish the history of checkpoint training.
