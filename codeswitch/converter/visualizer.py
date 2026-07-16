import ast
import json
import operator
import re
import subprocess
import sys
from django.conf import settings


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

MAX_TRACE_STEPS = 120
MAX_LOOP_ITERATIONS = 40
MAX_TRACE_OUTPUT_LENGTH = 12_000
PYTHON_TRACE_TIMEOUT_SECONDS = 4


class _ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
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


def _safe_repr(value):
    text = repr(value)
    return text if len(text) <= 80 else f'{text[:77]}...'


def _target_name(target):
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
        return target.value.id
    return None


def _concepts_from_steps(steps):
    concepts = []
    for step in steps:
        concept = _concept_for_kind(step['kind'])
        if concept and concept not in concepts:
            concepts.append(concept)
    return concepts


class _PythonTraceBuilder:
    def __init__(self, code):
        self.code = code
        self.lines = code.splitlines()
        self.steps = []
        self.output = []
        self.functions = {}

    def trace(self):
        tree = ast.parse(self.code)
        module_frame = {'name': '<module>', 'locals': {}}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.functions[node.name] = node
                self._record(node, 'function', module_frame, 'Function definition',
                             f'{node.name} is stored so it can be called later.')
            else:
                self._exec_stmt(node, module_frame, [module_frame])
            if len(self.steps) >= MAX_TRACE_STEPS:
                break
        return self.steps

    def _line(self, node):
        lineno = getattr(node, 'lineno', 1)
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ''

    def _frame_state(self, stack):
        return [
            {
                'name': frame['name'],
                'variables': [
                    {'name': key, 'value': _safe_repr(value)}
                    for key, value in frame['locals'].items()
                    if not key.startswith('__')
                ],
            }
            for frame in stack
        ]

    def _record(self, node, kind, frame, title, description, stack=None, return_value=None):
        if len(self.steps) >= MAX_TRACE_STEPS:
            return
        stack = stack or [frame]
        variables = self._frame_state(stack)[-1]['variables'] if stack else []
        visual = {
            'focus': kind,
            'variables': variables,
            'stack': self._frame_state(stack),
            'output': list(self.output),
        }
        if return_value is not None:
            visual['return_value'] = _safe_repr(return_value)
        if kind == 'loop':
            visual['pulse'] = 'loop'
        elif kind == 'condition':
            visual['pulse'] = 'branch'
        elif kind == 'output':
            visual['pulse'] = 'output'
        elif kind == 'array':
            visual['pulse'] = 'collection'

        self.steps.append({
            'id': f'step-{len(self.steps) + 1}',
            'line': getattr(node, 'lineno', 1),
            'kind': kind,
            'title': title,
            'description': description,
            'code': self._line(node),
            'visual': visual,
        })

    def _eval_expr(self, node, frame, stack):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            for candidate in reversed(stack):
                if node.id in candidate['locals']:
                    return candidate['locals'][node.id]
            return f'<unknown {node.id}>'
        if isinstance(node, ast.List):
            return [self._eval_expr(item, frame, stack) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_expr(item, frame, stack) for item in node.elts)
        if isinstance(node, ast.Dict):
            return {
                self._eval_expr(key, frame, stack): self._eval_expr(value, frame, stack)
                for key, value in zip(node.keys, node.values)
                if key is not None
            }
        if isinstance(node, ast.Subscript):
            value = self._eval_expr(node.value, frame, stack)
            index = self._eval_expr(node.slice, frame, stack)
            try:
                return value[index]
            except Exception:
                return f'<{ast.unparse(node) if hasattr(ast, "unparse") else "subscript"}>'
        if isinstance(node, ast.UnaryOp):
            value = self._eval_expr(node.operand, frame, stack)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.Not):
                return not value
        if isinstance(node, ast.BoolOp):
            values = [self._eval_expr(value, frame, stack) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        if isinstance(node, ast.BinOp):
            left = self._eval_expr(node.left, frame, stack)
            right = self._eval_expr(node.right, frame, stack)
            fn = _BIN_OPS.get(type(node.op))
            if fn:
                try:
                    return fn(left, right)
                except Exception:
                    return ast.unparse(node) if hasattr(ast, 'unparse') else '<expression>'
        if isinstance(node, ast.Compare):
            left = self._eval_expr(node.left, frame, stack)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_expr(comparator, frame, stack)
                fn = _COMPARE_OPS.get(type(op))
                if not fn or not fn(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            return self._call(node, frame, stack)
        return ast.unparse(node) if hasattr(ast, 'unparse') else '<expression>'

    def _call(self, node, frame, stack):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        if name == 'print':
            values = [self._eval_expr(arg, frame, stack) for arg in node.args]
            text = ' '.join(str(value) for value in values)
            self.output.append(text)
            self._record(node, 'output', frame, 'Output produced', f'print displays {_safe_repr(text)}.', stack)
            return None
        if name == 'range':
            args = [self._eval_expr(arg, frame, stack) for arg in node.args]
            return range(*args)
        if name in {'len', 'sum', 'min', 'max', 'list', 'str', 'int', 'float', 'bool'}:
            args = [self._eval_expr(arg, frame, stack) for arg in node.args]
            builtins = {
                'len': len,
                'sum': sum,
                'min': min,
                'max': max,
                'list': list,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
            }
            try:
                return builtins[name](*args)
            except Exception:
                return f'<call {name}>'
        if name in self.functions:
            func = self.functions[name]
            args = [self._eval_expr(arg, frame, stack) for arg in node.args]
            local_frame = {'name': name, 'locals': {}}
            for param, value in zip(func.args.args, args):
                local_frame['locals'][param.arg] = value
            call_stack = stack + [local_frame]
            self._record(node, 'call', local_frame, 'Function call',
                         f'{name} is called and a new stack frame is created.', call_stack)
            try:
                for stmt in func.body:
                    self._exec_stmt(stmt, local_frame, call_stack)
            except _ReturnSignal as signal:
                self._record(node, 'return', local_frame, 'Return value',
                             f'{name} returns {_safe_repr(signal.value)} to its caller.',
                             call_stack, return_value=signal.value)
                return signal.value
            return None
        return f'<call {name or "function"}>'

    def _exec_stmt(self, node, frame, stack):
        if len(self.steps) >= MAX_TRACE_STEPS:
            return
        if isinstance(node, ast.Assign):
            value = self._eval_expr(node.value, frame, stack)
            for target in node.targets:
                name = _target_name(target)
                if name:
                    frame['locals'][name] = value
            kind = 'array' if isinstance(value, (list, tuple, dict, set)) else 'assignment'
            self._record(node, kind, frame, _line_title(kind),
                         f'{", ".join(_target_name(t) or "value" for t in node.targets)} becomes {_safe_repr(value)}.',
                         stack)
            return
        if isinstance(node, ast.AnnAssign):
            value = self._eval_expr(node.value, frame, stack) if node.value else None
            name = _target_name(node.target)
            if name:
                frame['locals'][name] = value
            self._record(node, 'assignment', frame, 'Variable update',
                         f'{name or "value"} becomes {_safe_repr(value)}.', stack)
            return
        if isinstance(node, ast.AugAssign):
            name = _target_name(node.target)
            current = frame['locals'].get(name, 0) if name else 0
            value = self._eval_expr(node.value, frame, stack)
            fn = _BIN_OPS.get(type(node.op))
            try:
                updated = fn(current, value) if fn else value
            except Exception:
                updated = value
            if name:
                frame['locals'][name] = updated
            self._record(node, 'assignment', frame, 'Variable update',
                         f'{name or "value"} becomes {_safe_repr(updated)}.', stack)
            return
        if isinstance(node, ast.Expr):
            self._eval_expr(node.value, frame, stack)
            if not isinstance(node.value, ast.Call) or getattr(node.value.func, 'id', '') != 'print':
                self._record(node, 'statement', frame, 'Statement executed',
                             'This expression is evaluated.', stack)
            return
        if isinstance(node, ast.For):
            iterable = list(self._eval_expr(node.iter, frame, stack))
            target = _target_name(node.target) or 'item'
            for idx, item in enumerate(iterable[:MAX_LOOP_ITERATIONS], start=1):
                frame['locals'][target] = item
                self._record(node, 'loop', frame, 'Loop iteration',
                             f'Iteration {idx}: {target} is {_safe_repr(item)}.', stack)
                for stmt in node.body:
                    self._exec_stmt(stmt, frame, stack)
            return
        if isinstance(node, ast.While):
            count = 0
            while self._eval_expr(node.test, frame, stack) and count < MAX_LOOP_ITERATIONS:
                count += 1
                self._record(node, 'loop', frame, 'While loop',
                             f'Iteration {count}: the condition is true.', stack)
                for stmt in node.body:
                    self._exec_stmt(stmt, frame, stack)
            return
        if isinstance(node, ast.If):
            result = bool(self._eval_expr(node.test, frame, stack))
            self._record(node, 'condition', frame, 'Decision point',
                         f'The condition is {result}. The {"if" if result else "else"} branch runs.', stack)
            for stmt in (node.body if result else node.orelse):
                self._exec_stmt(stmt, frame, stack)
            return
        if isinstance(node, ast.Return):
            value = self._eval_expr(node.value, frame, stack) if node.value else None
            self._record(node, 'return', frame, 'Return value',
                         f'The function returns {_safe_repr(value)}.', stack, return_value=value)
            raise _ReturnSignal(value)
        self._record(node, 'statement', frame, 'Statement executed',
                     'This statement is reached during execution.', stack)


def _build_python_trace(code):
    try:
        return _PythonTraceBuilder(code).trace()
    except Exception:
        return None


PYTHON_SUBPROCESS_TRACER = r'''
import builtins
import json
import sys
import traceback
import types

payload = json.loads(sys.stdin.read() or "{}")
user_code = payload.get("code") or ""
max_steps = int(payload.get("max_steps") or 120)
max_output = int(payload.get("max_output") or 12000)

trace = []
output_parts = []
object_labels = {}
object_counter = 0


class StepLimitExceeded(Exception):
    pass


class OutputLimitExceeded(Exception):
    pass


class CaptureStdout:
    def write(self, text):
        if not isinstance(text, str):
            text = str(text)
        current = ''.join(output_parts)
        remaining = max_output - len(current)
        if remaining <= 0:
            raise OutputLimitExceeded("Output limit exceeded.")
        output_parts.append(text[:remaining])
        if len(text) > remaining:
            raise OutputLimitExceeded("Output limit exceeded.")
        return len(text)

    def flush(self):
        return None


def object_id(value):
    global object_counter
    real = id(value)
    if real not in object_labels:
        object_counter += 1
        object_labels[real] = f"obj-{object_counter}"
    return object_labels[real]


def is_mutable_like(value):
    return isinstance(value, (list, tuple, dict, set)) or (
        hasattr(value, "__dict__")
        and not callable(value)
        and not isinstance(value, (type, types.ModuleType))
    )


def primitive_or_repr(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    text = repr(value)
    return text if len(text) <= 120 else text[:117] + "..."


def snapshot_value(value, heap, seen):
    if is_mutable_like(value):
        ref = object_id(value)
        if ref in seen:
            return {"$ref": ref}
        seen.add(ref)

        if isinstance(value, dict):
            items = {}
            for key, item in list(value.items())[:80]:
                items[primitive_or_repr(key)] = snapshot_value(item, heap, seen)
            heap[ref] = {"type": "dict", "items": items}
        elif isinstance(value, (list, tuple)):
            heap[ref] = {
                "type": "list" if isinstance(value, list) else "tuple",
                "items": [snapshot_value(item, heap, seen) for item in list(value)[:80]],
            }
        elif isinstance(value, set):
            heap[ref] = {
                "type": "set",
                "items": [snapshot_value(item, heap, seen) for item in list(value)[:80]],
            }
        else:
            attrs = {}
            for key, item in list(getattr(value, "__dict__", {}).items())[:80]:
                if not str(key).startswith("_"):
                    attrs[str(key)] = snapshot_value(item, heap, seen)
            heap[ref] = {
                "type": "object",
                "items": attrs,
                "repr": primitive_or_repr(value),
            }
        return {"$ref": ref}

    return primitive_or_repr(value)


def snapshot_frames(frame, event, arg=None):
    if len(trace) >= max_steps:
        raise StepLimitExceeded("Trace step limit exceeded.")

    chain = []
    current = frame
    while current is not None:
        if current.f_code.co_filename == "<user_code>":
            chain.append(current)
        current = current.f_back
    chain.reverse()

    heap = {}
    frames = []
    for current_frame in chain:
        local_seen = set()
        variables = {}
        for key, value in current_frame.f_locals.items():
            if key.startswith("__"):
                continue
            variables[key] = snapshot_value(value, heap, local_seen)

        code_name = current_frame.f_code.co_name
        frames.append({
            "id": f"frame-{id(current_frame)}",
            "name": "<module>" if code_name == "<module>" else f"{code_name}()",
            "variables": variables,
        })

    step = {
        "id": f"trace-{len(trace) + 1}",
        "line": frame.f_lineno,
        "event": event,
        "frames": frames,
        "heap": heap,
        "stdout": ''.join(output_parts),
    }
    if event == "return":
        step["return_value"] = primitive_or_repr(arg)
    trace.append(step)


def tracer(frame, event, arg):
    if frame.f_code.co_filename != "<user_code>":
        return tracer
    if event in {"call", "line", "return", "exception"}:
        snapshot_frames(frame, event, arg)
    return tracer


allowed_import_roots = {
    "bisect",
    "collections",
    "copy",
    "decimal",
    "fractions",
    "functools",
    "heapq",
    "itertools",
    "math",
    "operator",
    "random",
    "re",
    "statistics",
    "string",
}


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0:
        raise ImportError("Relative imports are not available in the visualizer.")
    root = (name or "").split(".", 1)[0]
    if root not in allowed_import_roots:
        raise ImportError(f"Import '{name}' is blocked in the visualizer sandbox.")
    return builtins.__import__(name, globals, locals, fromlist, level)


safe_builtins = {
    "__build_class__": builtins.__build_class__,
    "__import__": safe_import,
    "abs": abs,
    "all": all,
    "any": any,
    "ArithmeticError": ArithmeticError,
    "AssertionError": AssertionError,
    "BaseException": BaseException,
    "bool": bool,
    "callable": callable,
    "chr": chr,
    "classmethod": classmethod,
    "complex": complex,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "Exception": Exception,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "getattr": getattr,
    "hasattr": hasattr,
    "hex": hex,
    "IndexError": IndexError,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "KeyError": KeyError,
    "len": len,
    "list": list,
    "LookupError": LookupError,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "object": object,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "property": property,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "setattr": setattr,
    "slice": slice,
    "sorted": sorted,
    "staticmethod": staticmethod,
    "str": str,
    "sum": sum,
    "super": super,
    "tuple": tuple,
    "type": type,
    "ValueError": ValueError,
    "zip": zip,
    "ZeroDivisionError": ZeroDivisionError,
}

old_stdout = sys.stdout
sys.stdout = CaptureStdout()
error = None

try:
    globals_dict = {"__builtins__": safe_builtins, "__name__": "__main__"}
    sys.settrace(tracer)
    exec(compile(user_code, "<user_code>", "exec"), globals_dict, globals_dict)
except Exception as exc:
    line = None
    tb = exc.__traceback__
    while tb:
        if tb.tb_frame.f_code.co_filename == "<user_code>":
            line = tb.tb_lineno
        tb = tb.tb_next
    error = {"message": str(exc) or exc.__class__.__name__, "line": line}
    if not trace or trace[-1].get("event") != "exception":
        trace.append({
            "id": f"trace-{len(trace) + 1}",
            "line": line or (trace[-1]["line"] if trace else 1),
            "event": "exception",
            "frames": trace[-1]["frames"] if trace else [],
            "heap": trace[-1]["heap"] if trace else {},
            "stdout": ''.join(output_parts),
            "error": error,
        })
finally:
    sys.settrace(None)
    sys.stdout = old_stdout

print(json.dumps({"trace": trace[:max_steps], "error": error}))
'''


def _kind_from_trace_step(step):
    event = step.get('event')
    if event == 'call':
        return 'call'
    if event == 'return':
        return 'return'
    if event == 'exception':
        return 'statement'
    line = step.get('code', '')
    return _statement_kind(line, 'python') or 'statement'


def _trace_to_steps(trace, lines):
    steps = []
    previous_stdout = ''
    for index, trace_step in enumerate(trace, start=1):
        line_no = trace_step.get('line') or 1
        code = lines[line_no - 1].strip() if 1 <= line_no <= len(lines) else ''
        trace_step['code'] = code
        kind = _kind_from_trace_step(trace_step)
        if trace_step.get('stdout', '') != previous_stdout:
            kind = 'output'
        if trace_step.get('event') == 'exception':
            title = 'Runtime error'
            description = trace_step.get('error', {}).get('message') or 'Execution stopped with an error.'
        elif trace_step.get('event') == 'return':
            title = 'Return value'
            description = 'The function returns to its caller.'
        else:
            title = _line_title(kind)
            description = _description_for(kind, code, 'python')

        stack = []
        for frame in trace_step.get('frames', []):
            stack.append({
                'name': frame.get('name', '<frame>'),
                'variables': [
                    {'name': key, 'value': _safe_repr(value)}
                    for key, value in frame.get('variables', {}).items()
                ],
            })

        visual = {
            'focus': kind,
            'variables': stack[-1]['variables'] if stack else [],
            'stack': stack,
            'output': trace_step.get('stdout', '').splitlines(),
        }
        if trace_step.get('return_value') is not None:
            visual['return_value'] = _safe_repr(trace_step.get('return_value'))
        if kind == 'loop':
            visual['pulse'] = 'loop'
        elif kind == 'condition':
            visual['pulse'] = 'branch'
        elif kind == 'output':
            visual['pulse'] = 'output'
        elif kind == 'array':
            visual['pulse'] = 'collection'

        steps.append({
            'id': f'step-{index}',
            'line': line_no,
            'kind': kind,
            'title': title,
            'description': description,
            'code': code,
            'visual': visual,
        })
        previous_stdout = trace_step.get('stdout', '')
    return steps


def _build_python_subprocess_trace(code):
    try:
        completed = subprocess.run(
            [sys.executable, '-I', '-c', PYTHON_SUBPROCESS_TRACER],
            input=json.dumps({
                'code': code,
                'max_steps': MAX_TRACE_STEPS,
                'max_output': MAX_TRACE_OUTPUT_LENGTH,
            }),
            text=True,
            capture_output=True,
            timeout=PYTHON_TRACE_TIMEOUT_SECONDS,
            env={'PYTHONIOENCODING': 'utf-8'},
        )
    except subprocess.TimeoutExpired:
        return {
            'trace': [{
                'id': 'trace-1',
                'line': 1,
                'event': 'exception',
                'frames': [],
                'heap': {},
                'stdout': '',
                'error': {'message': 'Execution timed out.', 'line': 1},
            }],
            'error': {'message': 'Execution timed out.', 'line': 1},
        }
    if completed.returncode != 0 and not completed.stdout:
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


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
    output = []

    if language == 'python' and settings.PYTHON_EXECUTION_TRACING_ENABLED:
        trace_result = _build_python_subprocess_trace(code.replace('\x00', ''))
        if trace_result and trace_result.get('trace'):
            trace = trace_result.get('trace', [])[:MAX_TRACE_STEPS]
            traced_steps = _trace_to_steps(trace, lines)
            concepts = _concepts_from_steps(traced_steps)
            recommendations = []
            for concept in concepts:
                for title in CONCEPT_RECOMMENDATIONS.get(concept, []):
                    if title not in recommendations:
                        recommendations.append(title)
            response = {
                'language': language,
                'mode': 'execution_trace',
                'summary': f'Traced {len(trace)} Python execution steps with stack frames, heap objects, and output.',
                'concepts': concepts,
                'recommendations': recommendations[:6],
                'trace': trace,
                'steps': traced_steps[:80],
            }
            if trace_result.get('error'):
                response['error'] = trace_result['error']
            return response

        traced_steps = _build_python_trace(code.replace('\x00', ''))
        if traced_steps:
            concepts = _concepts_from_steps(traced_steps)
            recommendations = []
            for concept in concepts:
                for title in CONCEPT_RECOMMENDATIONS.get(concept, []):
                    if title not in recommendations:
                        recommendations.append(title)
            return {
                'language': language,
                'mode': 'execution_trace',
                'summary': f'Traced {len(traced_steps)} Python execution steps with stack frames and output.',
                'concepts': concepts,
                'recommendations': recommendations[:6],
                'trace': [],
                'steps': traced_steps[:80],
            }

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

        if kind == 'output':
            output.append(f'Output expression: {_clean_line(line)}')

        variable_snapshot = [
            {'name': key, 'value': val}
            for key, val in variables.items()
        ]
        visual = {
            'focus': kind,
            'variables': variable_snapshot,
            'stack': [{
                'name': 'Program state',
                'variables': variable_snapshot,
            }],
            'output': list(output),
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
        'mode': 'concept_trace',
        'summary': f'Generated {len(steps)} visual steps covering {len(concepts)} concept{"s" if len(concepts) != 1 else ""}.',
        'concepts': concepts,
        'recommendations': recommendations[:6],
        'steps': steps[:80],
    }
