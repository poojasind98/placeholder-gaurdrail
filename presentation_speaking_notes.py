"""Detailed speaking notes for the existing pipeline presentation."""


def expand_notes(dataset):
    name = dataset['dataset']
    stages = dataset['stages']
    counts = dataset['counts']
    metrics = dataset['metrics']
    source = 'Blue Gene/L supercomputer' if name == 'BGL' else 'Liberty supercomputing system'
    token_width = 11 if name == 'BGL' else 71
    notes = [
        f"""What I am explaining: where our data comes from and exactly what this experiment uses.

“We are working with {name}, a public collection of logs from the {source}. A log is a text record of a system event. A dataset is a collection of these records. Our source links distinguish the original logs from the prepared test CSV published by the LogLLM authors.

We begin inference with that prepared CSV. We selected the first ten normal and first ten anomalous sequences, retaining their original CSV row numbers. This deliberately balanced sample makes both classes visible in a short demonstration. It is not a random sample, and its scores do not estimate performance on the complete dataset.

The input file contains data; the checkpoint contains learned model weights. Those are different things. We use the {name}-specific adapters and projection weights with the base BERT and Llama models. We are running inference, which means making predictions without updating those weights.”

Point to: the original-source link, prepared-test link, local sample path, and full-test label counts.

Transition: “First, I will illustrate what an original record looks like before showing the prepared input we actually evaluate.”""",
        """What I am explaining: parsing a raw record into named fields.

“An original log line combines metadata and a message. Metadata can include a date, timestamp, machine identifier, component, or severity field. The Content field contains the event message itself. The repository uses a dataset-specific format and a regular expression to separate the line into these named fields.

The original Label field is a reference annotation. In this preparation code, a dash maps to zero, meaning normal; other tags map to one, meaning anomalous. This conversion constructs the reference answer. It is not a model prediction. A severity word such as INFO or an occurrence of the word error is not the same thing as the reference Label field.

The record shown here is a real source excerpt. It illustrates parsing, but it is not the raw ancestor of the selected sequence shown on the next slide. We downloaded the authors’ already-prepared test file rather than regenerating it from the entire archive. Also, the existing raw parser silently skips unmatched lines; we should not describe it as comprehensive validation.”

Point to: one raw field and its matching parsed value, then the extracted Content.

Transition: “After preparation, the model’s input is organized as groups of messages in a CSV.”""",
        """What I am explaining: the unit the model classifies and the separation between input and answer key.

“Each row in this prepared CSV represents a sequence, not a single message. In our selected sample, each sequence contains one hundred messages, separated by the literal delimiter shown on screen. The excerpt displays only the first three messages for readability.

Content is the input text. Label is the reference answer: zero for normal and one for anomalous. SourceRow points to the zero-based row in the prepared test CSV, excluding its header; it is not a raw-log line number.

The repository’s count-window preparation groups messages and assigns the window an anomalous reference label if any event in it is labeled anomalous. That is how a target can be constructed for training or evaluation. The neural model does not use that rule to predict—it has to generate its own answer from the processed messages.

During evaluation, the labels are loaded alongside the data but are not passed into the model’s inference call. They are compared with predictions afterward. The displayed preparation recipe comes from the code; we have not independently reproduced the historical generation of these downloaded CSVs.”

Point to: the sequence length, Content excerpt, reference label, and SourceRow.

Transition: “Next, the loader normalizes the message content.”""",
        """What I am explaining: how normalization changes the actual text before tokenization.

“The dataset loader calls replace_patterns on Content. This is a deterministic regular-expression function: the same text produces the same normalized output. It masks matched patterns such as numeric identifiers, IP addresses, and file paths with the placeholder <*>. It also handles other configured patterns and reduces runs of repeated dots.

For example, two messages that differ only in a matched identifier may become identical after masking. The intention is to reduce variation from changing values so the model can process more consistent message patterns. This operation does not detect an anomaly or assign a label.

We are using the existing upstream normalization function. It is not a newly trained template parser, and it does not guarantee an accuracy improvement. Masking can remove useful information, and its regexes can replace parts of a word or path. Later, the uncased BERT tokenizer also lowercases the text; that is a separate operation.

The before and after panels contain the same actual messages from the selected sample. We can therefore inspect exactly what this implementation removes and what remains.”

Point to: a changing value before masking and the corresponding <*> afterward. Do not describe every remaining word as an identified security feature.

Transition: “The normalized messages are then arranged into a batch for BERT.”""",
        """What I am explaining: the difference between messages, sequences, windows, and batches.

“A message is one entry. A sequence is a group of entries that receives one prediction. A window is a rule for forming such groups. A batch is the number of sequences processed together in one model call.

Our prepared sample already has one hundred messages per sequence. The loader splits the Content string using the delimiter. The collator then keeps at most 128 messages per sequence and limits each tokenized message to 100 BERT tokens. These are input caps: changing them does not rebuild the original windows. With 100 messages and a cap of 128, no messages are removed from these sample sequences by that cap.

For efficiency, messages from all sequences in a batch are combined for BERT. The code records split positions so it can restore the sequence groups after encoding. With batch size one, the split-position list is empty because there is no boundary between different sequences to record.

The separate six-event example in the Terminal explains window size and stride. It is an illustration using the existing helper, not a model experiment or a change to our prepared evaluation data.”

Point to: sequence count, message count, length limits, and split positions.

Transition: “Now we can inspect the numerical input that the tokenizer produces.”""",
        f"""What I am explaining: how text becomes the integer input BERT accepts.

“The tokenizer breaks text into vocabulary pieces called tokens. A token can be a word, punctuation, or part of a word. With WordPiece tokenization, a piece beginning with ## continues a word. The placeholder <*> is also tokenized into pieces; it is not a special anomaly symbol.

Each token is mapped to an integer vocabulary ID. These IDs are lookup indices, not severity values or meaningful measurements: a larger ID does not mean a more anomalous token. BERT later looks up learned numerical embeddings for them. [CLS] marks the start and [SEP] the end of each message input. [PAD] fills shorter rows so they can be stored together.

The attention mask tells BERT which positions are real or special tokens and which are padding: one means included, zero means padding. It is not a normal/anomalous mask, nor an explanation of what BERT considers important.

In this captured {name} batch, the input shape is [100, {token_width}]: one hundred message rows with {token_width} token positions per row after padding. A tensor is simply a numerical array with one or more dimensions. The width depends on this batch’s token lengths and the configured cap.”

Point to: a token, its ID at the same position, the mask, and both dimensions of the shape.

Transition: “BERT turns those token IDs into learned message vectors.”""",
        """What I am explaining: what a vector is and what BERT contributes to the pipeline.

“A vector is an ordered list of numbers. Here, a message vector contains 768 values. We also call it a numerical representation or embedding. These values are learned features, not the original token IDs and not a list of named fields such as IP address or severity. We cannot point to a single coordinate and say that it means attack or failure.

BERT first converts token IDs into embeddings and processes them through transformer layers. Its attention mechanism allows tokens within the same message to influence each other’s representations. In our implementation, each message is a separate BERT input row; BERT is not directly attending across all one hundred log messages at this step.

The code takes BERT’s pooler_output, a transformed representation of the first [CLS] position, as one fixed-length vector for each message. That gives the observed shape [100, 768]: one hundred messages, each represented by 768 numbers. The display shows only eight numbers from the first vector, not the complete tensor.

We load the dataset-specific LoRA adapter with base BERT. LoRA stores learned low-rank adjustments to selected layers. During this inference run those weights remain fixed. The vector is an intermediate representation; BERT does not output our final normal/anomalous verdict here.”

Point to: [100, 768], the eight-value excerpt, and the BERT adapter path. Positive and negative numbers are representation values, not confidence percentages.

Transition: “Llama expects a different vector size, so the projection layer converts these message vectors.”""",
        """What I am explaining: why the projection layer is needed and what changes at this stage.

“BERT produces a 768-value vector per message, while this Llama model expects a 4,096-value embedding at each input position. The projection layer is a learned linear mapping that connects these two sizes. For one message, it computes y = W x + b, where x is the BERT vector, W is a learned matrix, and b is a learned bias.

The output shape is [100, 4096]. The number of message rows remains one hundred; only the representation width changes. It is not padding the BERT vector with zeros or creating 4,096 messages. The learned transformation produces a representation that the downstream model can use.

The weights are loaded from projector.pt. The captured projection values are float32 at this point; the model code then casts them to float16 before assembling Llama’s input. Float32 and float16 describe numerical precision, not prediction quality or confidence.

Like the BERT vectors, these projected values are intermediate features, not anomaly scores. Their usefulness depends on the learned weights and the rest of the model, rather than on interpreting a single displayed coordinate.”

Point to: the change from 768 to 4,096 columns, the unchanged 100 rows, the dtype, and the saved projector path.

Transition: “We place these projected message vectors between the instruction and question embeddings for Llama.”""",
        """What I am explaining: what Llama actually receives and how it generates a classification.

“The input is a sequence of embeddings, not a CSV file or a plain-text copy of every original log. The code combines embeddings of the instruction, one projected vector per message, embeddings of the question, and the answer prefix ‘The sequence is’. This gives Llama the task instruction together with the encoded log sequence.

The observed shape [1, 124, 4096] means one sequence in the batch, 124 input positions, and 4,096 values at every position. In this example, one hundred positions represent log messages and the remaining 24 come from the surrounding prompt. The shape can change for a different sequence length.

Llama uses its base weights and the dataset-specific adapter. It predicts scores called logits for possible next tokens. Our code selects the highest-scoring token using argmax and continues generating, reusing cached attention information. It stops when the sequence finishes or reaches the code’s short answer-length cap.

The generated token IDs are decoded into text such as ‘normal.’ or ‘anomalous.’. The reference label is not part of this prompt. We do not report the logits as calibrated confidence, and this short classification response does not explain which individual message caused the decision.”

Point to: the input’s three dimensions, the prompt composition, generated IDs, and decoded text.

Transition: “The evaluator converts that response into a class and compares it with the answer key.”""",
        """What I am explaining: the difference between a model prediction and a correct detection.

“The evaluator reads the generated text and maps normal to zero and anomalous to one. An answer that cannot be parsed as either class raises an error rather than being silently treated as normal.

Prediction is the model’s answer. Reference label is the dataset’s answer. A reference of one and prediction of one is a detected anomaly, or true positive. Zero and zero is a correctly classified normal sequence, or true negative. Reference zero with prediction one is a false alarm. Reference one with prediction zero is a missed anomaly.

Sample index identifies the row in our selected input. Source row links that row back to the authors’ prepared test CSV. This lets us inspect the input associated with a prediction. It does not establish a causal explanation of the model’s decision.

These records are from a completed real inference run. Opening this presentation or running the results walkthrough reads those saved records; it does not secretly start another model run. Each verdict applies to an entire sequence, so it should not be presented as a precise attack category or a highlighted offending log line.”

Point to: one prediction row and compare its reference, prediction, model text, and outcome. Show an error when the selected run contains one.

Transition: “Finally, we summarize these individual outcomes into evaluation metrics.”""",
        f"""What I am explaining: how the scores are calculated and what conclusions they support.

“In this selected {name} run, we have {counts['TN']} correctly classified normal sequences, {counts['TP']} detected anomalies, {counts['FP']} false alarms, and {counts['FN']} missed anomalies.

Accuracy asks: out of all sequences, how many predictions were correct? It is (TP + TN) divided by the sample count. Precision asks: among sequences flagged anomalous, how many really had an anomalous reference label? It is TP / (TP + FP). Recall asks: among all reference anomalies, how many did we detect? It is TP / (TP + FN). F1 is the harmonic mean of precision and recall, 2PR / (P + R).

Here the recorded accuracy is {metrics['accuracy']:.0%}, precision is {metrics['precision']:.0%}, recall is {metrics['recall']:.0%}, and F1 is {metrics['f1']:.2%}. These are aggregate scores across the selected sample, not confidence values for individual predictions. We checked their arithmetic against the saved prediction rows.

Both samples deliberately contain ten normal and ten anomalous sequences. They do not reflect the full datasets’ class distributions. Each dataset also uses its own checkpoint, so this comparison does not show that one checkpoint generalizes to the other dataset. The BGL scores come from the earlier twenty-sequence run; its intermediate trace is a separate one-sequence observation, not a new benchmark.

We save predictions.csv for individual outputs, metrics.json for scores, and run.json for paths and execution settings. These records support inspection and rerunning with the same settings, but they do not guarantee bit-for-bit results on every environment or prove who originally trained the weights.”

Point to: confusion counts first, then scores and run settings.

Closing: “We have demonstrated two functioning dataset-specific inference paths and made their transformations and results inspectable. Larger evaluations would be needed for broader performance claims.”""",
    ]
    if len(stages) != len(notes):
        raise ValueError('Speaking notes no longer match the presentation stages.')
    for item, note in zip(stages, notes):
        item['say'] = note
