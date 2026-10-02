"""Connected narrative for the professor copy; preserves technical evidence."""
import re


def connect_story(dataset):
    name = dataset['dataset']
    steps = [
        ('The question we want to answer', 'Public system logs', 'A path from logs to a checked prediction',
         f'Can we take a group of {name} system messages and classify the group as normal or anomalous? We will follow that journey from the original logs to the final results. First we explain how the data is prepared; then we follow the saved test sample through our local inference pipeline.',
         'Let us begin with where these logs come from and which files we have locally.'),
        ('Find the data', 'The original public dataset', 'The prepared test file and our selected sample',
         f'To answer that question, we need both data and saved model weights. For {name}, the source links lead to the original logs and the separately provided prepared test file. Our local folder contains test.csv and the selected smoke-mixed.csv; it does not contain train.csv. The raw excerpt is a small illustration of the original format.',
         'Before looking inside a prepared CSV row, let us see what an original log line contains.'),
        ('Understand one raw record', 'A raw log line', 'Named fields, including Content and a reference label',
         'The source gives us text records, but each line combines several pieces of information. Parsing separates the message from fields such as timestamps and system identifiers. This raw excerpt explains that operation; it is not a traced ancestor of the test sequence shown later.',
         'Once records have separate message and label fields, the preparation script can split and group them into CSV rows.'),
        ('Build the sequence files', 'Parsed records in their original order', 'Separate train.csv and test.csv sequence files',
         'Now we connect individual records to the files used by the model. The preparation code splits records into training and testing portions, then groups each portion into message windows. This explains how the files can be created. In our local run, we entered the workflow afterward by downloading the prepared test file.',
         'The training branch produces saved weights. We already have a checkpoint, so let us follow the test branch and inspect one input sequence.'),
        ('Choose the input we will follow', 'A row in the prepared test sample', 'Message text for inference; a label kept for checking',
         f'We now join the actual local {name} inference path. Each selected CSV row contains a sequence of messages. From this point, we follow the selected sequence through normalization and the model. Its reference label travels separately and is used only after a prediction exists.',
         'The first change to that message text happens in the dataset loader: normalization.'),
        ('Make variable text more consistent', 'The selected sequence’s Content text', 'Normalized messages',
         'We have the message text, but changing identifiers and other variable values can make similar events look different. The loader applies the existing regular-expression replacements. The before-and-after examples show this text transformation; no prediction has been made yet.',
         'With the text normalized, we need to arrange the messages for a model call while keeping their sequence boundaries.'),
        ('Organize the model call', 'Normalized messages grouped by sequence', 'A batch of messages with recorded sequence boundaries',
         'The loader splits each sequence into individual messages. The collator collects those messages into a batch and records where sequences separate. This arrangement lets BERT process messages individually and lets the later stages reconstruct the original groups.',
         'The batch still begins as text. The tokenizer now converts each message into the numerical IDs BERT accepts.'),
        ('Turn text into token IDs', 'The messages collected by the collator', 'Token IDs and attention masks',
         'The tokenizer breaks each message into vocabulary pieces and maps those pieces to integer IDs. Padding makes the rows fit together, and the attention mask identifies padding positions. These arrays are the direct inputs to BERT.',
         'These IDs identify vocabulary entries. BERT processes them to produce a learned representation of each message.'),
        ('Represent each message with BERT', 'Token IDs and attention masks', 'One 768-value vector per message',
         'BERT now transforms the tokenized messages into numerical representations. A vector is an ordered list of numbers; here, each message becomes 768 numbers. The dataset adapter adjusts the base model’s behavior, and the saved trace lets us inspect the resulting shape.',
         'We now have message vectors, but Llama expects 4,096 values per input position. The projection layer bridges that size difference.'),
        ('Connect BERT to Llama', '768-value BERT message vectors', '4,096-value projected message vectors',
         'The projection layer takes exactly the vectors produced by BERT and applies a learned linear transformation. It keeps one row per message while changing the width from 768 to 4,096. This makes the representations compatible with Llama’s input size.',
         'The vectors are now the right size. We can combine them with the task instructions and ask Llama to classify the sequence.'),
        ('Generate the sequence verdict', 'Projected message vectors plus prompt embeddings', 'Generated text: normal or anomalous',
         'The model restores the sequence groups and places their projected vectors alongside the instruction and question embeddings. Llama uses this combined input and its dataset-specific adapter to generate a short classification response. This is where the model produces its answer.',
         'We have a model answer. Now we bring back the reference label to check whether that answer is correct.'),
        ('Check each prediction', 'Generated response and the separate reference label', 'Correct detections, normal classifications, false alarms, or misses',
         'The evaluator converts the response into a class and compares it with the reference label withheld from inference. This connects each original sample row to its prediction and outcome. An anomalous prediction is a correct detection only when its reference label is also anomalous.',
         'After checking each row, we can count the outcomes and summarize the whole selected run.'),
        ('Close the loop with results', 'The individual prediction outcomes', 'Evaluation metrics and saved run evidence',
         f'We have now followed the complete local path: a prepared {name} sequence became normalized text, token IDs, BERT vectors, projected vectors, and a Llama response. Comparing responses with reference labels gives the counts and scores below. These results describe our selected twenty-sequence run.',
         'This completes the story for this dataset. We can select the other dataset and follow the same stages with its own input files, checkpoint, and saved results.'),
    ]
    assert len(dataset['stages']) == len(steps)
    for stage, (chapter, incoming, outgoing, narrative, transition) in zip(dataset['stages'], steps):
        stage['storyChapter'] = chapter
        stage['storyInput'] = incoming
        stage['storyOutput'] = outgoing
        stage['explanation'] = narrative
        # Retain detailed technical explanation and pointers; replace disconnected framing.
        notes = stage['say']
        notes = re.sub(r'^What we are explaining:.*?\n\n', '', notes, flags=re.S)
        notes = re.sub(r'\n\n(?:Transition|Closing):.*$', '', notes, flags=re.S)
        notes = notes.replace('the selected sequence shown on the next slide', 'the selected sequence we inspect after preparation')
        stage['say'] = f'Opening connection\n“{narrative}”\n\nExplain this step\n{notes}\n\nConnect to the next section\n“{transition}”'
        stage['nextConnection'] = transition
