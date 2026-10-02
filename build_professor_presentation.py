"""Create a separate team-voice presentation without altering the original."""
import copy
import hashlib
import json
import re
from pathlib import Path
from presentation_code_flow import add_code_flow
from presentation_story import connect_story

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 'presentations/BGL-Liberty'


def team_voice(value):
    if isinstance(value, dict):
        return {key: team_voice(item) for key, item in value.items()}
    if isinstance(value, list):
        return [team_voice(item) for item in value]
    if not isinstance(value, str):
        return value
    replacements = [
        ('What I am explaining:', 'What we are explaining:'),
        ('First, I will illustrate', 'First, we will illustrate'),
        ('the authors’ prepared', 'the publicly provided'),
        ('Authors’ prepared', 'Publicly provided'),
        ('the authors’ already-prepared', 'the publicly provided, already-prepared'),
        ('the authors’ preparation', 'the LogLLM preparation'),
        ('published by the LogLLM authors', 'provided with LogLLM'),
        ('LogLLM authors’ preparation and test links', 'LogLLM preparation and dataset references'),
        ('the original LogLLM authors', 'the LogLLM project'),
        ('the original authors', 'the LogLLM project'),
        ('existing upstream normalization function', 'existing LogLLM normalization function'),
        ('existing upstream window helper', 'existing LogLLM window helper'),
        ('upstream preparation', 'the existing preparation workflow'),
        ('Upstream preparation instructions', 'LogLLM preparation instructions'),
        ('the existing upstream', 'the existing LogLLM'),
        ('not a newly trained parser', 'a deterministic regex step'),
        ('whose authorship', 'whose training provenance'),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def main():
    original_path = DIRECTORY / 'index.html'
    original = original_path.read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    html = original.decode()
    pattern = r'(<script id="evidence" type="application/json">)(.*?)(</script>)'
    match = re.search(pattern, html, flags=re.S)
    if match is None:
        raise ValueError('No embedded presentation data found.')
    source = json.loads(match.group(2))
    result = team_voice(copy.deepcopy(source))
    for name, dataset in result['datasets'].items():
        add_code_flow(dataset)
        connect_story(dataset)
        dataset['stages'][0]['say'] = (
            '“We are presenting Guardrail’s log-anomaly detection component. '
            'Our work here brings together model loading, local execution, '
            'sample selection, evaluation, and inspectable outputs. '
            'Our Guardrail pipeline uses public datasets and '
            'pretrained base models with dataset-specific checkpoints.”\n\n'
            + dataset['stages'][0]['say']
        )
        # Keep source URLs and executable commands intact; use project-facing prose.
        for stage in dataset['stages']:
            for field in ('say', 'explanation', 'codeFlow'):
                if field not in stage:
                    continue
                stage[field] = (stage[field]
                    .replace('provided with LogLLM', 'provided with the source implementation')
                    .replace('existing LogLLM normalization function', 'existing normalization function')
                    .replace('LogLLM.__init__()', 'the model class’s __init__()')
                    .replace('LogLLM.forward()', 'the model class’s forward()'))
            for link in stage['links']:
                link['label'] = link['label'].replace('LogLLM preparation', 'Preparation')
        # Preserve ordering, technical evidence, metrics, commands, and links.
        old = source['datasets'][name]
        assert len(dataset['stages']) == len(old['stages']) == 13
        assert dataset['metrics'] == old['metrics'] and dataset['counts'] == old['counts']
        assert dataset['manifest'] == old['manifest']
        for a, b in zip(dataset['stages'], old['stages']):
            assert a['title'] == b['title'] and a['command'] == b['command']
            assert a.get('rows') == b.get('rows')
            assert [link['url'] for link in a['links']] == [link['url'] for link in b['links']]
    professor = re.sub(pattern, lambda m: m.group(1) + json.dumps(result).replace('<', '\\u003c') + m.group(3), html, flags=re.S)
    professor = professor.replace('<title>Guardrail | BGL and Liberty walkthrough</title>',
                                  '<title>Guardrail | Professor presentation</title>')
    professor = professor.replace(
        '<button id="notesToggle" aria-pressed="true">Hide speaking notes</button>',
        '<button id="notesToggle" role="switch" aria-checked="true" '
        'aria-label="Speaking notes" aria-controls="notes"></button>')
    professor = professor.replace(
        "el('notesToggle').textContent=showNotes?'Hide speaking notes':'Show speaking notes';"
        "el('notesToggle').setAttribute('aria-pressed',String(showNotes));",
        "el('notesToggle').setAttribute('aria-checked',String(showNotes));")
    professor = professor.replace('</style>', '''
#notesToggle{position:relative;width:46px;height:26px;padding:0;border-radius:999px;background:#777;border:1px solid transparent;flex-shrink:0}
#notesToggle::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:white;transition:transform .15s}
#notesToggle[aria-checked="true"]{background:var(--accent)}
#notesToggle[aria-checked="true"]::after{transform:translateX(20px)}
@media(prefers-reduced-motion:reduce){#notesToggle::after{transition:none}}
</style>''')
    professor = professor.replace('<section><h3>Show this stage in Terminal</h3>',
        '<section id="code-flow"><h3>Related code and file flow</h3>'
        '<pre id="fileFlow" style="max-height:none"></pre></section>'
        '<section><h3>Show this stage in Terminal</h3>')
    professor = professor.replace('<div class="links" id="links">',
        '<section class="notes" aria-label="Story flow"><h3 id="storyChapter"></h3>'
        '<p><strong>We start with: </strong><span id="storyInput"></span></p>'
        '<p><strong>This step gives us: </strong><span id="storyOutput"></span></p></section>'
        '<div class="links" id="links">')
    professor = professor.replace('<div class="foot">',
        '<section class="notes"><h3>Where we go next</h3><p id="nextConnection"></p></section>'
        '<section id="acknowledgment" hidden><h3>Source acknowledgment</h3>'
        '<p>Guardrail builds on the open-source '
        '<a href="https://github.com/guanwei49/LogLLM">LogLLM project</a>, '
        'including its BERT–projection–Llama architecture and the dataset-specific '
        'checkpoints used here. We use public datasets and pretrained base models. '
        'Our demonstrated work covers local integration, execution, evaluation, '
        'and inspectable pipeline outputs.</p></section><div class="foot">')
    professor = professor.replace("el('command').textContent=s.command;",
        "el('command').textContent=s.command;el('fileFlow').textContent=s.codeFlow;"
        "el('acknowledgment').hidden=index!==stages.length-1;"
        "for(const key of ['storyChapter','storyInput','storyOutput','nextConnection'])el(key).textContent=s[key];")
    assert 'id="owner" style="display:none"' in professor
    (DIRECTORY / 'professor.html').write_text(professor)
    (DIRECTORY / 'professor-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == original_hash
    print('Created professor.html; original index.html is byte-for-byte unchanged.')


if __name__ == '__main__':
    main()
