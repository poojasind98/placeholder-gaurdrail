"""Build an offline presentation from real local inputs, traces, and completed results."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from customDataset import replace_patterns
from presentation_walkthrough import ROOT, SOURCES, read_rows, raw_example, token_example, trace_path
from presentation_speaking_notes import expand_notes
from presentation_preparation import add_preparation_stages

OUT = ROOT / 'presentations/BGL-Liberty'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(label, value):
    return {'label': label, 'text': value if isinstance(value, str) else json.dumps(value, indent=2)}


def stage(title, owner, explanation, say, blocks=(), links=(), command=''):
    return dict(title=title, owner=owner, explanation=explanation, say=say,
                blocks=list(blocks), links=list(links), command=command)


def dataset_content(name):
    full_path = ROOT / 'data' / name / 'test.csv'
    sample_path = full_path.with_name('smoke-mixed.csv')
    full, sample = read_rows(full_path), read_rows(sample_path)
    expected = [i for label in ('0', '1') for i in [j for j, r in enumerate(full) if r['Label'] == label][:10]]
    assert [int(r['SourceRow']) for r in sample] == expected
    for r in sample:
        original = full[int(r['SourceRow'])]
        assert r['Content'] == original['Content'] and r['Label'] == original['Label']
    result_dir = ROOT / 'outputs' / f'{name}-mixed-smoke'
    predictions = read_rows(result_dir / 'predictions.csv')
    metrics = json.loads((result_dir / 'metrics.json').read_text())
    run = json.loads((result_dir / 'run.json').read_text())
    assert Path(run['data']).resolve() == sample_path.resolve()
    assert Path(run['checkpoint']).resolve() == (ROOT / f'ft_model_{name}').resolve()
    assert len(sample) == len(predictions) == metrics['samples'] == 20
    for i, (r, p) in enumerate(zip(sample, predictions)):
        assert int(p['sequence_index']) == i and p['label'] == r['Label']
    counts = {key: sum(int(p['label']) == actual and int(p['prediction']) == pred for p in predictions)
              for key, actual, pred in [('TN', 0, 0), ('FP', 0, 1), ('FN', 1, 0), ('TP', 1, 1)]}
    tp, tn, fp, fn = (counts[x] for x in ['TP', 'TN', 'FP', 'FN'])
    calculated = {'accuracy': (tp+tn)/20, 'precision': tp/(tp+fp) if tp+fp else 0,
                  'recall': tp/(tp+fn) if tp+fn else 0,
                  'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
    assert all(abs(metrics[k]-v)<1e-8 for k,v in calculated.items())
    trace = json.loads(trace_path(name).read_text())
    trace_run = json.loads(trace_path(name).with_name('run.json').read_text())
    assert Path(trace_run['data']).resolve() == sample_path.resolve() and trace_run['batch_size'] == 1
    tokens = token_example(name)
    assert tokens['input_ids_first_message'] == trace['bert_input']['input_ids_first_message']
    assert tokens['bert_input_shape'] == trace['bert_input']['shape']
    assert trace['responses'][0].strip() == predictions[0]['response'].strip()
    raw = raw_example(name)
    messages = sample[0]['Content'].split(' ;-; ')
    normalized = replace_patterns(sample[0]['Content']).split(' ;-; ')
    links = [{'label': key.replace('_',' ').capitalize(), 'url': value}
             for key, value in SOURCES[name].items() if key != 'format']
    links.append({'label':'LogLLM authors’ preparation and test links','url':'https://github.com/guanwei49/LogLLM'})
    prefix = f'python presentation_walkthrough.py'
    cmd = lambda s: f'{prefix} {s} --dataset {name}'
    stages = [
        stage('Source data and the file used today', 'Pooja',
              f'{name} has {len(full):,} prepared test sequences locally. Our presentation uses the first 10 normal and first 10 anomalous sequences. Original logs, prepared CSVs, and our selected sample are different artifacts.',
              f'We use the authors’ prepared {name} test file. We selected twenty sequences for a short functionality check. The original sources are linked here; we did not collect these logs ourselves.',
              [block('Local input',str(sample_path)),block('Full prepared test label counts',{'normal':sum(r['Label']=='0' for r in full),'anomalous':sum(r['Label']=='1' for r in full)})],links,cmd('sources')),
        stage('Original log record and parsed fields','Nikhil',
              'Actual public-source excerpt parsed using the repository’s format regex. This is a separate format illustration, not a reconstruction of the selected test sequence. The entire raw archive was not reprocessed locally.',
              'This shows how the original record is separated into fields. The Content field holds the message. In upstream preparation, a dash label maps to normal. The existing parser skips unmatched lines, so we do not describe it as a complete validation system.',
              [block('Original record',raw['original_line']),block('Parsed fields',raw['parsed_fields']),block('Excerpt provenance',raw['provenance'])],command=cmd('raw')),
        stage('Prepared sequence and reference label','Nikhil',
              'The preparation script maps event labels to 0/1, splits the structured data 80/20, and forms count-based windows of 100 messages with step 100. A window reference label is 1 if any event label is 1. This describes the provided code; the exact historical run was not reproduced here.',
              'Each CSV row is a sequence. These are the first three messages of sample row zero, not the whole sequence. The label is an answer key for evaluation and is not passed to the inference model.',
              [block('Selected row metadata',{'sample_index':0,'SourceRow':int(sample[0]['SourceRow']),'Label':int(sample[0]['Label']),'messages':len(messages)}),block('Content excerpt; messages separated by ;-;', ' ;-; '.join(messages[:3])),block('Prepared CSV columns',list(full[0]))],command=cmd('inputs')),
        stage('Normalization before BERT','Nikhil',
              'CustomDataset applies replace_patterns() to Content. Regexes mask matched numeric values, IP addresses, paths, and other patterns as <*>. Repeated dots are reduced. The tokenizer later lowercases text. This is the existing LogLLM preprocessing, not a newly trained parser.',
              'Here are the same actual messages before and after normalization. The text becomes more consistent, but values are removed and this can lose information. A word such as error does not by itself establish the reference class.',
              [block('Before', '\n'.join(messages[:3])),block('After', '\n'.join(normalized[:3]))],command=cmd('preprocessing')),
        stage('Sequence boundaries and batch construction','Pooja',
              'Content is split on the exact delimiter " ;-; ". CustomCollator keeps at most 128 messages per sequence, combines messages for BERT tokenization, and records boundaries. Our saved run uses batch size 1.',
              'A sequence is a group of messages; a batch is a group of sequences. Here there are one hundred messages in one sequence. The empty boundary list means no split is needed between multiple sequences in this batch.',
              [block('Normalized message list excerpt',normalized[:3]),block('Batch description',{'sequences':1,'messages':len(normalized),'max_messages_per_sequence':128,'max_tokens_per_message':100,'sequence_split_positions':tokens['sequence_split_positions']})],command=cmd('sequences')),
        stage('Actual BERT tokenizer output','Nikhil / Pooja',
              'The local BERT tokenizer converts text into WordPiece tokens and integer IDs. [CLS] and [SEP] are special tokens; ## means a continuing word piece. Padding makes message rows equal length. The attention mask is 1 for included tokens and 0 for padding, not an anomaly indicator.',
              'These are actual tokens and token IDs for the first message. The input tensor has one row per message. The second dimension depends on the longest tokenized message in this batch, up to the configured limit.',
              [block('Tokens, first message',tokens['tokens_first_message']),block('Token IDs, first message',tokens['input_ids_first_message']),block('Input tensor shape and attention mask',{'shape':tokens['bert_input_shape'],'mask':tokens['attention_mask_first_message']})],command=cmd('tokens')),
        stage('BERT output with the dataset adapter','Vijaya',
              'BERT receives token IDs and attention masks. The code uses pooler_output: one 768-number vector per message. The values below were captured during real inference with the matching adapter; they are not probabilities or human-readable explanations.',
              'BERT changes each message into a numerical representation. For one hundred messages, the observed output contains one hundred vectors of 768 values each. We display only eight values from the first vector.',
              [block('Observed BERT output',trace['bert_output']),block('Adapter folder',str(ROOT/f'ft_model_{name}'/'Bert_ft'))],command=cmd('trace')),
        stage('Projection into Llama’s representation size','Vijaya',
              'The learned linear projection converts each 768-value BERT vector into a 4,096-value vector. The code then casts the projected vectors to float16 before building the Llama input.',
              'This layer connects the two models. It changes the representation size, not the number of messages, and loads its learned weights from projector.pt.',
              [block('Observed projection output before float16 cast',trace['projector_output']),block('Saved weights',str(ROOT/f'ft_model_{name}'/'projector.pt'))],command=cmd('trace')),
        stage('Llama input and generated response','Vijaya',
              'Llama receives embeddings: instruction text embeddings, projected log vectors, question embeddings, and the answer prefix. It generates a short answer token by token using argmax. Reference labels are not included.',
              'Llama does not simply receive the original CSV text. It receives this combined numerical input. The actual captured shape includes the log-message positions plus prompt positions. The output token IDs decode into the classification text.',
              [block('Prompt around the projected messages','Below is a sequence of system log messages: [projected log vectors] . Is this sequence normal or anomalous? \\n The sequence is'),block('Observed Llama input',trace['llama_input']),block('Actual generated output',{'token_ids':trace['generated_token_ids'],'decoded':trace['responses']})],command=cmd('trace')),
        stage('Prediction records and correctness','Vijaya / Viswa',
              'The evaluator maps generated normal/anomalous text to 0/1, then compares it with the separate reference labels. These are saved results from completed inference, not a live model running inside this presentation.',
              'Prediction is the model’s answer. Label is the reference answer. Matching values mean a correct prediction; a label of one with a prediction of zero is a missed anomaly. These are sequence-level decisions, not identified attack types.',
              [block('Completed result file',str(result_dir/'predictions.csv'))],command=cmd('results')),
        stage('Evaluation and reproducibility','Viswa',
              'Metrics below are recomputed and checked against the saved predictions. Both samples were deliberately balanced and selected, not representative benchmarks. Each dataset uses its own adapter checkpoint; this is not a cross-dataset generalization test.',
              'We retain predictions, metrics, and run settings. These small evaluations establish that the two dataset-specific paths execute. They do not establish overall accuracy on the full datasets or explain every model error.',
              [block('Scores for the 20-sequence sample',metrics),block('Confusion counts',counts),block('Recorded run settings',run)],command=cmd('results')),
    ]
    stages[9]['rows'] = [[i,int(r['SourceRow']),int(p['label']),int(p['prediction']),p['response'].strip(), 'Correct' if p['label']==p['prediction'] else 'Missed anomaly' if p['label']=='1' else 'False alarm'] for i,(r,p) in enumerate(zip(sample,predictions))]
    result = {'dataset':name,'stages':stages,'metrics':metrics,'counts':counts,
            'manifest':{'input_sha256':digest(sample_path),'test_sha256':digest(full_path),'trace_path':str(trace_path(name)),
                        'predictions_sha256':digest(result_dir/'predictions.csv'),'selection':'First 10 normal and first 10 anomalous rows; zero-based SourceRow.',
                        'checkpoint_files':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/f'ft_model_{name}'/'Bert_ft/adapter_model.safetensors',ROOT/f'ft_model_{name}'/'Llama_ft/adapter_model.safetensors',ROOT/f'ft_model_{name}'/'projector.pt']}}}
    expand_notes(result)
    add_preparation_stages(result)
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data = {'generated_at':datetime.now(timezone.utc).isoformat(), 'datasets': {name:dataset_content(name) for name in ['BGL','Liberty']}}
    (OUT/'pipeline-evidence.json').write_text(json.dumps(data,indent=2)+'\n')
    template = (ROOT/'presentation_template.html').read_text()
    (OUT/'index.html').write_text(template.replace('__PIPELINE_DATA__',json.dumps(data).replace('<','\\u003c')))
    print('Built',OUT/'index.html')
    print('Verified selected rows, labels, metrics, tokenizer/trace agreement, and checkpoint paths for both datasets.')


if __name__ == '__main__':
    main()
