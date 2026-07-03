import re


SUPPORTED_LANGUAGES = {'python', 'c', 'java', 'javascript', 'cpp'}
MAX_VISUALIZER_CODE_LENGTH = 20_000

CONCEPT_RECOMMENDATIONS = {
    'variables': ['Variables and Types', 'Data Types'],
    'loops': ['Loops', 'Iteration'],
    'conditionals': ['Conditionals', 'Control Flow'],
    'functions': ['Functions', 'Methods'],
    'arrays': ['Arrays', 'Lists'],
    'returns': ['Functions', 'Return Values'],
    'output': ['Input and Output'],
}


def _clean_line(line):
    return line.strip()


def _line_title(kind):
    titles = {
        'function': 'Function definition',
        'loop': 'Loop iteration',
        'condition': 'Decision point',
        'assignment': 'Variable update',
        'array': 'Collection created',
        'return': 'Return value',
        'output': 'Output produced',
        'call': 'Function call',
        'statement': 'Statement executed',
    }
    return titles.get(kind, 'Code step')


def _statement_kind(line, language):
    stripped = _clean_line(line)
    if not stripped:
        return None

    lower = stripped.lower()
    if language == 'python':
        if re.match(r'def\s+\w+\s*\(', stripped):
            return 'function'
        if re.match(r'(for|while)\s+', stripped):
            return 'loop'
        if re.match(r'(if|elif|else)\b', stripped):
            return 'condition'
        if lower.startswith('return '):
            return 'return'
        if re.search(r'\bprint\s*\(', stripped):
            return 'output'
        if '=' in stripped and not re.search(r'(==|!=|<=|>=)', stripped):
            return 'array' if re.search(r'=\s*[\[\{]', stripped) else 'assignment'
        if re.search(r'\w+\s*\(', stripped):
            return 'call'
        return 'statement'

    if re.search(r'\b(public|private|protected|static|void|int|double|float|char|boolean|String)\b.*\w+\s*\([^;]*\)\s*\{?$', stripped):
        return 'function'
    if re.match(r'(for|while|do)\b', stripped):
        return 'loop'
    if re.match(r'(if|else if|else|switch)\b', stripped):
        return 'condition'
    if lower.startswith('return '):
        return 'return'
    if re.search(r'\b(console\.log|printf|cout|system\.out\.print)', lower):
        return 'output'
    if re.search(r'(\[\]|\{.*\}|new\s+\w+\s*\[)', stripped) and '=' in stripped:
        return 'array'
    if '=' in stripped and not re.search(r'(==|!=|<=|>=)', stripped):
        return 'assignment'
    if re.search(r'\w+\s*\(', stripped) and not stripped.endswith('{'):
        return 'call'
    if stripped in {'{', '}', '};'}:
        return None
    return 'statement'


def _extract_assignment(line, language):
    stripped = _clean_line(line).rstrip(';')
    if '=' not in stripped or re.search(r'(==|!=|<=|>=)', stripped):
        return None, None
    left, right = stripped.split('=', 1)
    left = left.strip()
    right = right.strip()
    if language != 'python':
        left = re.sub(r'\b(const|let|var|final|static|int|double|float|char|boolean|String|long|short|auto)\b', '', left).strip()
        left = left.replace('[]', '').strip()
    name = re.split(r'\s+', left)[-1] if left else ''
    name = re.sub(r'[^A-Za-z0-9_]', '', name)
    return (name or None), right or None


def _concept_for_kind(kind):
    return {
        'assignment': 'variables',
        'array': 'arrays',
        'loop': 'loops',
        'condition': 'conditionals',
        'function': 'functions',
        'return': 'returns',
        'output': 'output',
    }.get(kind)


def _description_for(kind, line, language):
    stripped = _clean_line(line)
    if kind == 'function':
        return 'The program defines a reusable block of logic.'
    if kind == 'loop':
        return 'A loop repeats a block while the iteration rule is true.'
    if kind == 'condition':
        return 'The program chooses a branch based on this condition.'
    if kind == 'assignment':
        name, value = _extract_assignment(stripped, language)
        return f'{name} receives or updates the value {value}.' if name and value else 'A variable is created or updated.'
    if kind == 'array':
        name, value = _extract_assignment(stripped, language)
        return f'{name} stores multiple values as a collection.' if name else 'A collection of values is created.'
    if kind == 'return':
        return 'The function sends a result back to its caller.'
    if kind == 'output':
        return 'The program displays a value to the user.'
    if kind == 'call':
        return 'The program calls a function to perform work.'
    return 'This statement advances the program state.'


def build_visualization(language, code):
    language = (language or '').lower().strip()
    code = code or ''
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f'Unsupported language: {language}.')
    if not code.strip():
        raise ValueError('No code provided.')
    if len(code) > MAX_VISUALIZER_CODE_LENGTH:
        raise ValueError(f'Code must be under {MAX_VISUALIZER_CODE_LENGTH:,} characters.')

    lines = code.replace('\x00', '').splitlines()
    steps = []
    concepts = []
    variables = {}

    for index, line in enumerate(lines, start=1):
        kind = _statement_kind(line, language)
        if not kind:
            continue

        concept = _concept_for_kind(kind)
        if concept and concept not in concepts:
            concepts.append(concept)

        name, value = _extract_assignment(line, language) if kind in {'assignment', 'array'} else (None, None)
        if name and value:
            variables[name] = value

        visual = {
            'focus': kind,
            'variables': [{'name': key, 'value': val} for key, val in variables.items()],
        }
        if kind == 'loop':
            visual['pulse'] = 'loop'
            visual['iteration_label'] = 'repeat'
        elif kind == 'condition':
            visual['pulse'] = 'branch'
        elif kind == 'output':
            visual['pulse'] = 'output'
        elif kind == 'array':
            visual['pulse'] = 'collection'

        steps.append({
            'id': f'step-{len(steps) + 1}',
            'line': index,
            'kind': kind,
            'title': _line_title(kind),
            'description': _description_for(kind, line, language),
            'code': _clean_line(line),
            'visual': visual,
        })

    if not steps:
        steps.append({
            'id': 'step-1',
            'line': 1,
            'kind': 'statement',
            'title': 'Code overview',
            'description': 'This snippet does not contain a recognizable beginner-level control-flow pattern yet.',
            'code': _clean_line(lines[0]) if lines else '',
            'visual': {'focus': 'statement', 'variables': []},
        })

    recommendations = []
    for concept in concepts:
        for title in CONCEPT_RECOMMENDATIONS.get(concept, []):
            if title not in recommendations:
                recommendations.append(title)

    return {
        'language': language,
        'summary': f'Generated {len(steps)} visual steps covering {len(concepts)} concept{"s" if len(concepts) != 1 else ""}.',
        'concepts': concepts,
        'recommendations': recommendations[:6],
        'steps': steps[:80],
    }
