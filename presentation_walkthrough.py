"""Read-only presentation aid for the real LogLLM pipeline; never runs inference."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LABEL = {0: "normal", 1: "anomalous"}

SOURCES = {
    'BGL': {
        'original_description': 'https://github.com/logpai/loghub/tree/master/BGL',
        'original_download': 'https://zenodo.org/records/8196385/files/BGL.zip?download=1',
        'prepared_test': 'https://drive.google.com/file/d/1aMKzhrLklnk5RX78UBc3Zx3voIIGnQzo/view',
        'format': '<Label> <Id> <Date> <Code1> <Time> <Code2> <Component1> <Component2> <Level> <Content>',
    },
    'Liberty': {
        'original_description': 'https://www.usenix.org/cfdr-data#hpc4',
        'original_download': 'http://0b4af6cdc2f0c5998459-c0245c5c937c5dedcca3f1764ecc9b2f.r43.cf2.rackcdn.com/hpc4/liberty2.gz',
        'prepared_test': 'https://drive.google.com/file/d/1-Z2FrsRSm8ojfOW1555obNyU6B_aRDTH/view',
        'format': '<Label> <Id> <Date> <Admin> <Month> <Day> <Time> <AdminAddr> <Content>',
    },
}


def sources(dataset):
    print(json.dumps(SOURCES[dataset], indent=2))
    print('Prepared test links are from https://github.com/guanwei49/LogLLM#5-evaluate-on-test-dataset')
    print('Inference input: the publicly provided prepared test CSV.')


def raw_example(dataset):
    from prepareData.helper import generate_logformat_regex
    path = ROOT / 'data' / dataset / 'raw-excerpt.log'
    headers, regex = generate_logformat_regex(SOURCES[dataset]['format'])
    line = path.read_text().splitlines()[0]
    match = regex.search(line.strip())
    if not match:
        raise ValueError('Raw excerpt did not match the upstream format.')
    return {'original_line': line, 'parsed_fields': {k: match.group(k) for k in headers},
            'provenance': json.loads(path.with_suffix('.source.json').read_text())}


def raw(dataset):
    print(json.dumps(raw_example(dataset), indent=2))
    print('Raw-format example from raw-excerpt.log; the evaluation sample is loaded separately from smoke-mixed.csv.')
    print('Upstream preparation maps raw label "-" to 0 and other tags to 1, then groups messages.')
    print('Parser behavior: unmatched lines are skipped.')


def token_example(dataset):
    from customDataset import replace_patterns, CustomCollator
    from transformers import BertTokenizerFast
    import numpy as np
    row = read_rows(ROOT / 'data' / dataset / 'smoke-mixed.csv')[0]
    messages = replace_patterns(row['Content']).split(' ;-; ')
    tokenizer = BertTokenizerFast.from_pretrained(str(ROOT / 'models/bert-base-uncased'), local_files_only=True)
    batch = CustomCollator(tokenizer, max_seq_len=128, max_content_len=100)([(np.array(messages, dtype=object), int(row['Label']))])
    ids = batch['inputs']['input_ids'][0].tolist()
    return {'source_row': int(row['SourceRow']), 'normalized_first_message': messages[0],
            'bert_input_shape': list(batch['inputs']['input_ids'].shape),
            'tokens_first_message': tokenizer.convert_ids_to_tokens(ids),
            'input_ids_first_message': ids,
            'attention_mask_first_message': batch['inputs']['attention_mask'][0].tolist(),
            'sequence_split_positions': batch['seq_positions'].tolist()}


def tokens(dataset):
    print(json.dumps(token_example(dataset), indent=2))
    print('Local tokenizer and CustomCollator output.')
    print('[CLS]/[SEP] delimit BERT input; ## marks a continuing word piece; [PAD] fills shorter rows.')
    print('Attention mask: 1 = content/special token; 0 = padding.')
    print('An empty split-position list means one sequence in this batch. Reference labels are kept separate for evaluation.')


def trace_path(dataset):
    return ROOT / 'outputs' / ('BGL-trace-example' if dataset == 'BGL' else 'Liberty-mixed-smoke') / 'pipeline-trace.json'


def trace(dataset, path=None):
    path = path or trace_path(dataset)
    print('Saved actual model trace:', path)
    print(json.dumps(json.loads(path.read_text()), indent=2))
    print('Trace scope: first batch. Embedding values are learned numerical representations.')


def read_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def inputs(dataset="BGL"):
    rows = read_rows(ROOT / "data" / dataset / "smoke-mixed.csv")
    full = read_rows(ROOT / "data" / dataset / "test.csv")
    print(f"{dataset}: prepared public system-log sequences.")
    print(f"Full local test set: {len(full):,} sequences")
    print(f"Selected presentation sample: {len(rows)} sequences")
    print("Selection: first 10 normal and first 10 anomalous test rows.")
    print("Evaluation scope: this deliberately selected sample.")
    for label in (0, 1):
        print(f"  {LABEL[label]}: {sum(int(r['Label']) == label for r in rows)}")
    print("Each sample sequence contains these numbers of messages:",
          sorted({len(r['Content'].split(' ;-; ')) for r in rows}))
    print("Content = input messages; Label = reference answer for evaluation.")
    print("SourceRow = zero-based row in the original test CSV (excluding header).")
    for i in (0, 10, 12):
        row = rows[i]
        print(f"\nSample index {i}; original row {row['SourceRow']}; reference {LABEL[int(row['Label'])]}")
        for line in row['Content'].split(' ;-; ')[:3]:
            print(" ", line)
        print("  ... first 3 messages shown")


def preprocessing(dataset="BGL"):
    from customDataset import replace_patterns
    row = read_rows(ROOT / "data" / dataset / "smoke-mixed.csv")[0]
    print(f"Real messages from the prepared {dataset} sample, before and after existing masking.")
    print("<*> is a placeholder for matched variable values.")
    for line in row['Content'].split(' ;-; ')[:3]:
        print(f"\nBefore: {line}\nAfter:  {replace_patterns(line)}")
    print("\nTransformation: customDataset.py -> replace_patterns().")
    print("The masking implementation comes from the upstream LogLLM code.")


def sequences(dataset="BGL"):
    import pandas as pd
    from prepareData.helper import fixedSize_window
    rows = read_rows(ROOT / "data" / dataset / "smoke-mixed.csv")
    messages = rows[0]['Content'].split(' ;-; ')
    print(f"Actual selected sequence: {len(messages)} messages; batch size for inference: 1.")
    print("Model limits: up to 128 messages/sequence and 100 BERT tokens/message.")
    print("Batch size = number of sequences processed together.")
    print("\nWindowing example: six synthetic events with example reference labels.")
    events = pd.DataFrame({'Content': [f'event {i}' for i in range(1, 7)],
                           'Label': [0, 0, 0, 0, 1, 0]})
    for window, step in ((3, 3), (3, 2)):
        print(f"\nWindow size {window}; step {step}:")
        grouped = fixedSize_window(events, window, step)
        for _, row in grouped.iterrows():
            print(f"  {', '.join(row['Content'])} -> reference {LABEL[int(row['Label'])]}")
    print("\nThe helper labels a window anomalous if any event's reference label is anomalous.")
    print("These are reference labels for the grouped windows; model predictions are produced during inference.")
    print("Overlapping windows share events; the helper retains a shorter final window.")


def results(output_dir):
    metadata = json.loads((output_dir / 'run.json').read_text())
    saved_metrics = json.loads((output_dir / 'metrics.json').read_text())
    predictions = read_rows(output_dir / 'predictions.csv')
    data = read_rows(Path(metadata['data']))
    if metadata['limit']:
        data = data[:metadata['limit']]
    if len(predictions) != len(data) or not predictions:
        raise ValueError('Prediction count does not match the recorded input selection.')
    for i, (prediction, source) in enumerate(zip(predictions, data)):
        if int(prediction['sequence_index']) != i or int(prediction['label']) != int(source['Label']):
            raise ValueError('Prediction rows do not align with the recorded input.')
        if int(prediction['prediction']) not in LABEL:
            raise ValueError('Invalid predicted class.')
    tn = sum(int(r['label']) == 0 and int(r['prediction']) == 0 for r in predictions)
    fp = sum(int(r['label']) == 0 and int(r['prediction']) == 1 for r in predictions)
    fn = sum(int(r['label']) == 1 and int(r['prediction']) == 0 for r in predictions)
    tp = sum(int(r['label']) == 1 and int(r['prediction']) == 1 for r in predictions)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    metrics = {'samples': len(predictions), 'accuracy': (tp + tn) / len(predictions),
               'precision': precision, 'recall': recall,
               'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0}
    for key, value in metrics.items():
        if abs(saved_metrics[key] - value) > 1e-8:
            raise ValueError(f'Saved metric disagrees with predictions: {key}')
    print('SAVED RESULTS:', output_dir.resolve())
    print('Displaying saved predictions from the completed inference run.')
    print('Recorded input:', metadata['data'])
    print('Recorded checkpoint:', metadata['checkpoint'])
    print(f"Device: {metadata['device']}; batch size: {metadata['batch_size']}")
    print(f"\nCorrect normal: {tn}; false alarms: {fp}; detected anomalies: {tp}; missed anomalies: {fn}")
    print(json.dumps(metrics, indent=2))
    print('\nExamples selected from these results:')
    for title, actual, predicted in [('Correct normal', 0, 0), ('Detected anomaly', 1, 1), ('Missed anomaly', 1, 0), ('False alarm', 0, 1)]:
        match = next((i for i, row in enumerate(predictions)
                      if int(row['label']) == actual and int(row['prediction']) == predicted), None)
        if match is None:
            print(f'\n{title}: no example in this run')
            continue
        source, prediction = data[match], predictions[match]
        print(f"\n{title}: sample index {match}; source row {source.get('SourceRow', 'not recorded')}")
        print(f"  Reference: {LABEL[actual]}; predicted: {LABEL[predicted]}; model text: {prediction['response'].strip()}")
        for line in source['Content'].split(' ;-; ')[:3]:
            print(' ', line)
        print('  ... first 3 input messages shown for context')
    print('\nMetrics agree with the saved predictions. Input labels and row order match.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['sources', 'raw', 'inputs', 'preprocessing', 'sequences', 'tokens', 'trace', 'results'])
    parser.add_argument('--dataset', choices=['BGL', 'Liberty'], default='BGL')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--trace-file', type=Path)
    args = parser.parse_args()
    try:
        if args.stage == 'results':
            results(args.output_dir or ROOT / "outputs" / f"{args.dataset}-mixed-smoke")
        elif args.stage == 'trace':
            trace(args.dataset, args.trace_file)
        else:
            {'inputs': inputs, 'preprocessing': preprocessing, 'sequences': sequences,
             'sources': sources, 'raw': raw, 'tokens': tokens}[args.stage](args.dataset)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Cannot present this stage: {error}\nFor results, select a completed output directory containing all three result files.\n')


if __name__ == '__main__':
    main()
