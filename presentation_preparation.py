"""Explain the existing raw-data preparation workflow in the presentation."""


def add_preparation_stages(dataset):
    name = dataset['dataset']
    links = dataset['stages'][0]['links']
    overview = {
        'title': 'Where the pipeline starts', 'owner': '',
        'explanation': 'The complete workflow starts with public raw system logs. Dataset preparation creates labeled training and test sequences. Our current evaluation starts later, with the authors’ prepared test.csv and an existing checkpoint.',
        'blocks': [
            {'label': 'Complete workflow described by the repository', 'text':
             'Original public log archive\n  ↓ download and extract\nRaw log records\n  ↓ parse fields and convert reference labels\nStructured records\n  ↓ first 80% / remaining 20% split\nSeparate training and test records\n  ↓ group each split into message sequences\ntrain.csv                         test.csv\n  ↓ fine-tuning                     ↓ inference with saved weights\nAdapters + projection weights ───→ Predictions\n                                    ↓ compare with reference labels\n                                  Metrics'},
            {'label': 'What we actually ran locally', 'text':
             f'Authors’ prepared {name} test.csv\n  ↓ select first 10 normal + first 10 anomalous\nsmoke-mixed.csv\n  ↓ normalize → tokenize → BERT → projection → Llama\nPredictions and evaluation files\n\nLoaded checkpoint: ft_model_{name}\nRaw-source excerpts: separate parsing illustrations\nFull raw-data preparation and training: not rerun for this presentation'},
        ],
        'links': links, 'command': f'python presentation_walkthrough.py sources --dataset {name}',
        'say': f'''What I am explaining: the beginning of the full workflow and where our current experiment enters it.

“The original input is a public collection of records written by the {name} system. Those records must be prepared before this model can train or evaluate on them. Preparation extracts the message fields, converts reference labels, divides records into training and test portions, and groups messages into sequences.

The training branch uses train.csv to learn adapter and projection weights. The evaluation branch uses test.csv with saved weights to generate predictions. The test labels are used afterward to check correctness, not supplied as answers during inference.

For our local demonstration, we downloaded the authors’ prepared test.csv and selected twenty sequences. We loaded the existing dataset-specific checkpoint. We did not regenerate the full training/test files or retrain the models during this presentation. The next sections explain both the original preparation process and the actual steps we executed.”

Point to: the two branches in the complete workflow, then the starting point in our local workflow.

Transition: “First, here are the original dataset links and the prepared file we downloaded.”''',
    }
    selection = ('Use the complete BGL raw log: start_line = 0; end_line = None.' if name == 'BGL' else
                 'For Liberty, the README instructs start_line = 40000000 and end_line = 45000000. The code uses zero-based indices with an exclusive end, selecting up to five million raw records before parsing.')
    preparation = {
        'title': 'How train.csv and test.csv are created', 'owner': '',
        'explanation': 'These are instructions implemented in prepareData/sliding_window.py and prepareData/helper.py. They describe how to prepare full raw logs; the current downloaded CSVs were not regenerated locally.',
        'blocks': [
            {'label': '1 · Download and configure', 'text':
             f'Download and extract the original {name} archive.\nSet data_dir to its directory and log_name to the extracted log filename.\nThe filename must identify the dataset for the script’s format selection.\n{selection}\nSet output_dir to a separate destination to preserve the downloaded CSVs.\nThe three-line raw-excerpt.log is insufficient for full dataset preparation.'},
            {'label': '2 · Parse and convert labels', 'text':
             'structure_log() extracts named fields using the dataset format regex.\nOutput: <log_name>_structured.csv\nRetain Content and the reference Label for grouping.\nRaw Label "-" → 0 (normal); other tags → 1 (anomalous).\nUnmatched raw records are skipped by the existing parser.'},
            {'label': '3 · Split, then group', 'text':
             'train_ratio = 0.8\nFirst 80% of parsed records → training\nRemaining 20% → testing\nNo random shuffle in this BGL/Liberty preparation path.\n\nwindow_size = 100; step_size = 100\nGroup each split separately to avoid a window crossing its boundary.\nWindow reference label = maximum of its event labels.\nThe existing helper retains a shorter final window if needed.'},
            {'label': '4 · Save CSV files', 'text':
             'train.csv / test.csv columns:\nContent        Messages joined with " ;-; "\nLabel          Reference class for the whole sequence\nitem_Label     List of individual message reference labels\nsession_length Number of messages in the sequence\n\nSourceRow is added later by our sample-selection step; it is not an original prepared-file column.\nRegex normalization and BERT tokenization happen later in the loader, not in this preparation step.'},
            {'label': 'Preparation command — only after paths and raw data are configured', 'text':
             'cd /Users/poojasindham/Desktop/gaurdrail\nsource .venv-logllm/bin/activate\npython prepareData/sliding_window.py\n\nThis command writes preparation outputs; it is not executed by this presentation.'},
        ],
        'links': [{'label': 'Upstream preparation instructions', 'url': 'https://github.com/guanwei49/LogLLM#3-prepare-training-and-testing-data'}],
        'command': 'sed -n \'1,110p\' prepareData/sliding_window.py',
        'say': f'''What I am explaining: how the repository can turn original {name} records into train.csv and test.csv.

“We first obtain and extract the full raw archive. The script needs its directory and filename configured. {selection} The repository currently contains hardcoded paths, so this is not a command to run unchanged.

The parser separates each record into fields and writes an intermediate structured CSV. The raw reference label is converted into zero or one. This is preparing the answer key; it is not predicting anomalies. Invalid-format records can be skipped by the existing parser.

The code then divides the parsed records in their existing order: the first eighty percent are training records and the remaining twenty percent are test records. Only after that split does it form windows separately within each portion. With a window size and step of one hundred, consecutive groups do not overlap. A final group may be shorter.

If any event in a group has reference label one, the sequence receives reference label one. The script joins each group’s messages into Content and saves the sequence label, the individual event labels, and the message count. These become train.csv and test.csv.

This preparation code exists in the repository. Our local test.csv files were downloaded already prepared, so we have not established that rerunning the current script reproduces those files exactly. Normalization and tokenization still happen afterward when the model loader reads the sequences.”

Point to: the split before windowing, the four saved columns, and the preparation command’s configuration requirement.

Transition: “Now we can inspect a row of the prepared test file and follow it through our actual evaluation.”''',
    }
    dataset['stages'].insert(0, overview)
    dataset['stages'].insert(3, preparation)
