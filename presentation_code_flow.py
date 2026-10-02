"""File-level navigation for the professor-facing presentation."""


def add_code_flow(dataset):
    name = dataset['dataset']
    sample = f'data/{name}/smoke-mixed.csv'
    checkpoint = f'ft_model_{name}'
    output = f'outputs/{name}-mixed-smoke'
    trace = 'outputs/BGL-trace-example/pipeline-trace.json' if name == 'BGL' else f'{output}/pipeline-trace.json'
    entries = [
        f'''RELATED FILES
README.md — dataset downloads and preparation instructions.
prepareData/sliding_window.py — raw-log preparation entry point for BGL/Liberty.
prepareData/helper.py — parsing and grouping functions used by that entry point.
train.py — optional fine-tuning entry point; requires training data, configured paths, and a suitable CUDA environment.
eval.py — inference/evaluation entry point used in our local runs.
customDataset.py and model.py — imported by eval.py; not scripts to run separately for each stage.

FULL FILE FLOW
Raw logs → prepareData/sliding_window.py → helper.py → train.csv + test.csv
train.csv → train.py → model.py → saved adapters + projector.pt
Prepared test sample + saved checkpoint → eval.py → customDataset.py → model.py → output files

CURRENT RUN
{sample} + {checkpoint} → eval.py → {output}/

RUN ORDER
Starting from full raw logs: configure preparation → run preparation → optionally train → evaluate.
Using our downloaded test files and existing weights: go directly to evaluation. Preparation and training need not run again.
The presentation_walkthrough.py commands inspect stages; they do not execute the full model.''',
        f'''RELATED FILES
README.md — links to raw sources and prepared test downloads.
presentation_walkthrough.py: SOURCES, sources() — records and prints source links.
data/{name}/test.csv — downloaded prepared test sequences.
{sample} — selected 20-sequence input with SourceRow.

FILE FLOW
Public prepared-test download → data/{name}/test.csv
Separate local sample selection → {sample}
presentation_walkthrough.py inputs → displays the sample and source-row references

WHAT RUNS HERE
python presentation_walkthrough.py sources --dataset {name}
This only prints links and format information. It does not download data, train, or evaluate.
build_pipeline_presentation.py checks that selected rows match test.csv; it does not create the selection.''',
        f'''RELATED FILES
data/{name}/raw-excerpt.log — three saved original-source records.
data/{name}/raw-excerpt.source.json — source URL and excerpt details.
presentation_walkthrough.py: raw_example(), raw() — loads one record and displays parsed fields.
prepareData/helper.py: generate_logformat_regex() — builds the dataset-format regex.

ILLUSTRATION FLOW
raw-excerpt.log → raw_example() → generate_logformat_regex() → named fields → screen

FULL PREPARATION FLOW
sliding_window.py → structure_log() → generate_logformat_regex() + log_to_dataframe() → structured CSV

WHAT RUNS HERE
python presentation_walkthrough.py raw --dataset {name}
This parses an excerpt in memory. It does not regenerate test.csv or connect this excerpt to a selected test row.''',
        f'''RELATED FILES
prepareData/sliding_window.py — controls paths, raw-line range, train_ratio, window_size, and step_size.
prepareData/helper.py: structure_log(), log_to_dataframe(), fixedSize_window() — does the underlying work.

PREPARATION CALL ORDER
1. Configure data_dir, log_name, and a separate output_dir in sliding_window.py.
2. Run: python prepareData/sliding_window.py
3. structure_log() writes <log_name>_structured.csv.
4. sliding_window.py reads that file and converts reference labels to 0/1.
5. Split parsed records: first 80% training, remaining 20% testing.
6. Call fixedSize_window() separately for each split (100 messages, step 100).
7. Join messages with " ;-; "; save train.csv, test.csv, train_info.txt, and test_info.txt.

NEXT BRANCHES
Optional training: configure train.py for the dataset, base-model paths, training CSV, output path, and CUDA environment; then python train.py.
Training calls model.train_helper() through staged trainModel() calls and finishes with model.save_ft_model().
Evaluation: configure eval.py arguments to point at the test data and matching saved checkpoint.

IMPORTANT
This is the procedure, not an instruction to run unchanged now. Full raw logs and correct paths are required.
The existing downloaded data/{name}/test.csv was not regenerated during our demonstration.
Despite the script name, its active default uses fixedSize_window(), not the time-based sliding_window() helper.''',
        f'''RELATED FILES
{sample} — Content, Label, and SourceRow for each selected sequence.
eval.py: main() — chooses the CSV from --data and the checkpoint from --dataset/--checkpoint.
customDataset.py: CustomDataset.__init__(), get_label() — reads content and retains reference labels.

FILE / CALL FLOW
eval.py --data {sample}
  → CustomDataset(data_path, max_samples=limit)
  → pandas reads the selected CSV rows
  → content normalization and message splitting
  → later: get_label() supplies references for scoring

LABEL SEPARATION
evalModel() passes batch['inputs'] and batch['seq_positions'] to model().
It does not pass batch['labels'] into the inference call.

READ-ONLY VIEW
python presentation_walkthrough.py inputs --dataset {name}''',
        f'''RELATED FILES
customDataset.py: patterns, combined_pattern, replace_patterns() — masking rules.
customDataset.py: CustomDataset.__init__() — applies replace_patterns to Content.
presentation_walkthrough.py: preprocessing() — calls the same function for the displayed examples.

CALL FLOW
eval.py → CustomDataset → Content.apply(replace_patterns)
  → reduce repeated dots
  → regex substitutions to <*>
  → normalized Content

NEXT STEP
CustomDataset splits normalized Content into messages. CustomCollator tokenizes them later.
No neural-model weights are loaded or updated by replace_patterns().

READ-ONLY VIEW
python presentation_walkthrough.py preprocessing --dataset {name}''',
        f'''RELATED FILES
customDataset.py: CustomDataset.__getitem__() — supplies a sequence and reference label.
customDataset.py: CustomCollator.__call__(), merge_data() — truncates and combines messages, preserving sequence boundaries.
eval.py: DataLoader configuration — batch size, no shuffle, num_workers=0 for local evaluation.
prepareData/helper.py: fixedSize_window() — separate preparation/window illustration helper.

INFERENCE CALL FLOW
CustomDataset → DataLoader → CustomCollator
  → keep up to 128 messages per sequence
  → merge_data() combines messages and records starting positions
  → tokenizer creates BERT inputs
  → batch contains inputs, seq_positions, and separately held labels
model.py later uses torch.tensor_split() to restore sequence groups.

READ-ONLY ILLUSTRATION
python presentation_walkthrough.py sequences --dataset {name}
The six-event window example calls fixedSize_window(); it does not replace the prepared model input.''',
        f'''RELATED FILES
model.py: LogLLM.__init__() — loads BertTokenizerFast from models/bert-base-uncased.
customDataset.py: CustomCollator.__call__() — calls the tokenizer with padding and truncation.
presentation_walkthrough.py: token_example(), tokens() — reproduces the first selected sequence’s tokenizer input locally.

CALL FLOW
Normalized messages → BertTokenizerFast → input_ids + attention_mask + token_type_ids
  → batched tensors from CustomCollator
  → evalModel() moves inputs to the selected device
  → model.py: LogLLM.forward() passes them into Bert_model

LIMIT
max_content_len=100 caps BERT token positions per message, including its special-token layout.

READ-ONLY VIEW
python presentation_walkthrough.py tokens --dataset {name}
This loads the tokenizer and runs the collator; it does not load BERT/Llama model weights.''',
        f'''RELATED FILES
model.py: LogLLM.__init__() — loads base BERT and its dataset adapter.
models/bert-base-uncased/ — base model and tokenizer files.
{checkpoint}/Bert_ft/ — adapter_model.safetensors and adapter_config.json.
model.py: LogLLM.forward() — calls self.Bert_model(**inputs).pooler_output.
pipeline_trace.py: PipelineTrace.bert() — captures a small excerpt of that actual output.

CALL FLOW
evalModel() → LogLLM.forward() → adapted Bert_model(**inputs)
  → pooler_output [100, 768]
  → convert to float32 for the projection layer

SAVED EVIDENCE
{trace}
python presentation_walkthrough.py trace --dataset {name}
The trace command reads saved observations. To obtain new values, a new eval.py run with --trace-output is required.''',
        f'''RELATED FILES
model.py: LogLLM.__init__() — creates nn.Linear(BERT hidden size, Llama hidden size).
{checkpoint}/projector.pt — saved projection weights and bias.
model.py: LogLLM.forward() — calls self.projector(outputs), then casts to float16.
pipeline_trace.py: PipelineTrace.projector() — records the output before that cast.

CALL FLOW
BERT pooler_output [100, 768]
  → float32
  → learned nn.Linear / projector.pt
  → projection output [100, 4096]
  → float16
  → split projected rows back into their sequence groups

RUNNING THIS STAGE
The projection executes inside the same eval.py model call; do not run model.py as a separate pipeline command.
python presentation_walkthrough.py trace --dataset {name} displays the saved projection values.''',
        f'''RELATED FILES
model.py: LogLLM.__init__() — loads the Llama base model, tokenizer, and adapter.
models/Meta-Llama-3-8B/ — base model shards and tokenizer.
{checkpoint}/Llama_ft/ — dataset-specific adapter weights and configuration.
model.py: LogLLM.forward(), stack_and_pad_left() — assembles embeddings and generates tokens.
pipeline_trace.py: llama_input(), finish() — captures initial Llama input and generated output.

CALL FLOW
Projected sequence vectors + instruction/question/answer-prefix embeddings
  → stack_and_pad_left() → inputs_embeds + attention_mask
  → Llama_model forward → logits → argmax next token
  → repeat with DynamicCache until stop condition
  → generated token-ID tensor returned to evalModel()
  → Llama_tokenizer.batch_decode() → response text

SAVED VIEW
python presentation_walkthrough.py trace --dataset {name}
There is no separate Llama-stage CLI in this pipeline; eval.py drives the complete call.''',
        f'''RELATED FILES
eval.py: evalModel() — runs inference and decodes responses.
eval.py: parse_prediction() — maps normal/anomalous text to 0/1 or raises an error.
customDataset.py: get_label() — returns reference labels for comparison.
{output}/predictions.csv — completed sequence-level output.
presentation_walkthrough.py: results() — aligns predictions with the recorded input and displays examples.

CALL FLOW
Generated token IDs → batch_decode() → parse_prediction()
  → collect model classes and responses
  → get_label() supplies reference classes
  → compute scores and save prediction rows

CHECK COMPLETED RESULTS
python presentation_walkthrough.py results --dataset {name}
SourceRow is recovered by joining the saved sequence index with the sample CSV; predictions.csv itself does not contain SourceRow.''',
        f'''RELATED FILES
eval.py: evalModel() — computes accuracy, precision, recall, and F1; writes metrics and prediction files.
eval.py: main() — writes run.json after successful evaluation.
{output}/metrics.json — aggregate scores.
{output}/predictions.csv — individual reference labels, classes, and responses.
{output}/run.json — input/checkpoint paths and run settings.
presentation_walkthrough.py: results() — recomputes metrics and checks input-label alignment.
build_pipeline_presentation.py — validates evidence and builds the saved presentation.
build_professor_presentation.py — creates this separate professor-facing copy.

FILE FLOW
Completed eval.py run → three result files → results() consistency checks → presentation evidence

READ-ONLY CHECK
python presentation_walkthrough.py results --dataset {name}

OPTIONAL NEW INFERENCE — use a fresh output folder; this starts the model
python eval.py --device mps --dataset {name} --data {sample} --limit 20 --batch-size 1 --output-dir outputs/{name}-new-run

A new output folder does not automatically refresh this saved presentation. Do not run the BGL and Liberty models concurrently on this laptop.''',
    ]
    if len(entries) != len(dataset['stages']):
        raise ValueError('Code-flow mapping does not match presentation stages.')
    for stage, entry in zip(dataset['stages'], entries):
        stage['codeFlow'] = entry
