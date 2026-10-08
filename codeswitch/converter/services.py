"""
CodeSwitch Conversion Engine (v2 - Improved Rule-Based)
-------------------------------------------------------
Translates common patterns between Python, C, and Java.
Handles indentation tracking, flexible for-loop patterns,
closing braces, and common language idioms.
"""
import re
import ast
import json


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _ind(level, width=4):
    return ' ' * (level * width)


def _py_indent_level(line):
    """Return Python indent level (4 spaces or 1 tab = 1 level)."""
    count = 0
    for ch in line:
        if ch == ' ':
            count += 1
        elif ch == '\t':
            count += 4
        else:
            break
    return count // 4


def _c_for_to_python(s):
    body = s.rstrip('{').strip()
    match = re.fullmatch(
        r'for\s*\(\s*(?:(?:int|let|var)\s+)?(?P<var>[a-zA-Z_]\w*)\s*=\s*(?P<start>[^;]+);'
        r'\s*(?P=var)\s*(?P<op>[<>]=?)\s*(?P<end>[^;]+);'
        r'\s*(?P=var)\s*(?P<inc>\+\+|--|\+=\s*\d+|-=\s*\d+)\s*\)', body)
    if not match:
        raise ValueError('Unsupported loop syntax or inconsistent loop variable.')
    var, start, op, end, increment = (match.group(key).strip() for key in ('var', 'start', 'op', 'end', 'inc'))
    step = 1 if increment == '++' else -1 if increment == '--' else int(increment[2:]) * (1 if increment[0] == '+' else -1)
    if step == 0 or (step > 0) != op.startswith('<'):
        raise ValueError('Loop step must be nonzero and agree with its boundary.')
    if op.endswith('='):
        offset = 1 if step > 0 else -1
        try:
            end = str(int(end) + offset)
        except ValueError:
            end = f'({end}) + 1' if offset == 1 else f'({end}) - 1'
    if step == 1:
        arguments = end if start == '0' else f'{start}, {end}'
    else:
        arguments = f'{start}, {end}, {step}'
    return f'for {var} in range({arguments}):'


def _py_range_to_c_for(var, range_str):
    args = [argument.strip() for argument in range_str.split(',')]
    if not 1 <= len(args) <= 3 or any(not argument for argument in args):
        raise ValueError('Unsupported range arguments.')
    start, end = ('0', args[0]) if len(args) == 1 else (args[0], args[1])
    try:
        step = int(args[2]) if len(args) == 3 else 1
    except ValueError as exc:
        raise ValueError('Unsupported range step: a literal integer is required.') from exc
    if step == 0:
        raise ValueError('Range step cannot be zero.')
    condition = f'{var} < {end}' if step > 0 else f'{var} > {end}'
    increment = f'{var}++' if step == 1 else f'{var}--' if step == -1 else f'{var} += {step}' if step > 0 else f'{var} -= {-step}'
    return f'int {var} = {start}', condition, increment


def _printf_to_print(s):
    """Convert C printf(...) to Python print(...). Returns None if no match."""
    literal = _literal_printf_text(s)
    if literal is not None:
        return f'print({literal!r})'
    # printf("text\n");  — no args
    m = re.match(r'printf\("(.*)\\n"\);$', s)
    if m:
        return f'print("{m.group(1)}")'

    # printf("fmt\n", arg1, arg2, ...);
    m = re.match(r'printf\("(.*)\\n",\s*(.+)\);$', s)
    if m:
        fmt = m.group(1)
        args = [a.strip() for a in m.group(2).split(',')]
        result_fmt = fmt
        for arg in args:
            result_fmt = re.sub(r'%(?:\.\d+)?[dsficg]', '{' + arg + '}', result_fmt, count=1)
        if '{' in result_fmt:
            return f'print(f"{result_fmt}")'
        return f'print("{result_fmt}")'

    return None


def _literal_printf_text(s):
    m = re.fullmatch(r'printf\("%s",\s*("(?:\\.|[^"\\])*")\);', s)
    if m:
        text = ast.literal_eval(m.group(1)).encode('latin1').decode('utf-8')
        if text.endswith('\n'):
            return text[:-1]
    return None


def _c_string(value):
    """Encode UTF-8 bytes independently of the compiler's source encoding."""
    if '\0' in value:
        raise ValueError('Embedded null characters are unsupported in C strings.')
    return '"' + ''.join(
        '\\' + chr(byte) if byte in (34, 92) else
        chr(byte) if 32 <= byte < 127 else f'\\{byte:03o}'
        for byte in value.encode('utf-8')
    ) + '"'


def _py_print_to_printf(s, type_map=None):
    """Translate supported print arguments using a fixed or escaped format."""
    type_map = type_map or {}

    def spec(var):
        return {'double': '%.15g', 'char[]': '%s'}.get(type_map.get(var), '%d')

    m = re.fullmatch(r'print\((.+)\)', s)
    if not m:
        return None
    argument = m.group(1)
    if argument.startswith(('"', "'", 'f"', "f'")):
        try:
            expression = ast.parse(argument, mode='eval').body
        except SyntaxError as exc:
            raise ValueError('Unsupported print string literal.') from exc
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            return f'printf("%s", {_c_string(expression.value + chr(10))});'
        if isinstance(expression, ast.JoinedStr):
            fmt, variables = [], []
            for part in expression.values:
                if isinstance(part, ast.Constant):
                    fmt.append(part.value.replace('%', '%%'))
                elif (isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name)
                      and part.conversion == -1 and part.format_spec is None):
                    variables.append(part.value.id)
                    fmt.append(spec(part.value.id))
                else:
                    raise ValueError('Unsupported formatted string expression.')
            return f'printf({_c_string("".join(fmt) + chr(10))}' + (', ' + ', '.join(variables) if variables else '') + ');'
        raise ValueError('Unsupported print string expression.')
    return f'printf("{spec(argument)}\\n", {argument});'


def _py_print_to_println(s):
    """Convert Python print(...) to Java System.out.println(...)."""
    # f-string: print(f"...")
    m = re.match(r'print\(f(["\'])(.*)\1\)', s)
    if m:
        content = m.group(2)
        parts = re.split(r'\{(\w+)\}', content)
        tokens = []
        for i, p in enumerate(parts):
            if not p:
                continue
            if i % 2 == 0:
                tokens.append(f'"{p}"')
            else:
                tokens.append(p)
        if tokens:
            return f'System.out.println({" + ".join(tokens)});'
        return f'System.out.println("");'

    # String literal
    m = re.match(r'print\((["\'])(.*)\1\)', s)
    if m:
        return f'System.out.println("{m.group(2)}");'

    # Variable/expression
    m = re.match(r'print\((.+)\)', s)
    if m:
        return f'System.out.println({m.group(1).strip()});'

    return None


# ─────────────────────────────────────────────
#  PYTHON BODY PROCESSING HELPERS
# ─────────────────────────────────────────────

def _extract_toplevel_funcs(lines):
    """Split Python lines into top-level def blocks and everything else.
    Returns (func_blocks, other_lines).
    """
    func_blocks = []
    other_lines = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped and _py_indent_level(raw) == 0 and re.match(r'def (\w+)\(([^)]*)\):', stripped):
            func_lines = [raw]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and _py_indent_level(nxt) == 0:
                    break
                func_lines.append(nxt)
                i += 1
            func_blocks.append(func_lines)
        else:
            other_lines.append(raw)
            i += 1
    return func_blocks, other_lines


def _has_return_value(func_lines):
    """Return True if any line in a function body is a non-empty return."""
    for line in func_lines[1:]:
        if re.match(r'\s*return\s+\S', line):
            return True
    return False


def _assignment_types(lines):
    types, assignments, loop_vars = {}, [], set()
    initialized = set()
    for raw in lines:
        line = raw.strip()
        loop = re.match(r'for (\w+) in range\(', line)
        if loop:
            loop_vars.add(loop.group(1))
            initialized.add(loop.group(1))
        match = re.fullmatch(r'([a-zA-Z_]\w*)\s*([+*-]?)=\s*(.+)', line)
        if not match:
            continue
        var, operator, expression = match.groups()
        if operator:
            expression = f'{var} {operator} ({expression})'
        assignments.append((var, expression))
        try:
            value = ast.literal_eval(expression)
        except (ValueError, SyntaxError):
            if var not in initialized:
                raise ValueError(f'Unresolved initialization type for {var}.')
            continue
        kind = 'int' if type(value) is int else 'double' if type(value) is float else 'string' if isinstance(value, str) else None
        if kind is None:
            raise ValueError(f'Unsupported assignment type for {var}.')
        if kind in ('int', 'double') and not re.fullmatch(r'-?\d+(?:\.\d+)?', expression):
            raise ValueError(f'Unsupported numeric literal type for {var}.')
        previous = types.get(var)
        if previous and (previous == 'string') != (kind == 'string'):
            raise ValueError(f'Incompatible type change for {var}.')
        types[var] = 'double' if 'double' in (previous, kind) else kind
        initialized.add(var)
    for var in loop_vars:
        if types.get(var, 'int') != 'int':
            raise ValueError(f'Unsupported type change for loop variable {var}.')
        types[var] = 'int'

    # ponytail: infer literals and simple arithmetic; extend only if richer rule conversions are required.
    def numeric_kind(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return 'double' if type(node.value) is float else 'int'
        if isinstance(node, ast.Name) and types.get(node.id) in ('int', 'double'):
            return types[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return numeric_kind(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            return 'double' if 'double' in (numeric_kind(node.left), numeric_kind(node.right)) else 'int'
        raise ValueError('Unresolved numeric assignment type; only simple arithmetic is supported.')

    changed = True
    while changed:
        changed = False
        for var, expression in assignments:
            if var not in types:
                raise ValueError(f'Unresolved assignment type for {var}.')
            try:
                node = ast.parse(expression, mode='eval').body
            except SyntaxError as exc:
                raise ValueError(f'Unresolved assignment type for {var}.') from exc
            if types[var] == 'string':
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    raise ValueError(f'Unresolved string assignment type for {var}.')
            elif numeric_kind(node) == 'double' and types[var] == 'int':
                if var in loop_vars:
                    raise ValueError(f'Unsupported type change for loop variable {var}.')
                types[var] = 'double'
                changed = True
    return types


def _process_python_to_c_body(lines, depth_offset=0, type_map=None):
    """Convert a list of Python lines to C lines (without outer braces).
    depth_offset: base indentation level added to all output.
    type_map: dict {var_name: c_type} for resolving printf format specifiers.
              Modified in place as variable declarations are encountered.
    """
    if type_map is None:
        type_map = {}
    planned_types = _assignment_types(lines)
    result = []
    block_stack = []
    block_kinds = []
    string_capacities = {}

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        py_level = _py_indent_level(raw)

        m_elif = re.match(r'elif (.+):$', stripped)
        if m_elif or stripped == 'else:':
            while block_stack and block_stack[-1] > py_level:
                block_stack.pop()
                block_kinds.pop()
                result.append(_ind(len(block_stack) + depth_offset + 1) + '}')
            if not block_stack or block_stack[-1] != py_level or block_kinds[-1] != 'if':
                raise ValueError('Unsupported branch: else/elif must belong to an if block.')
            block_stack.pop()
            block_kinds.pop()
            ind = _ind(len(block_stack) + depth_offset + 1)
            if m_elif:
                result.append(ind + f'}} else if ({m_elif.group(1)}) {{')
            else:
                result.append(ind + '} else {')
            block_stack.append(py_level)
            block_kinds.append('if' if m_elif else 'other')
            continue

        while block_stack and block_stack[-1] >= py_level:
            block_stack.pop()
            block_kinds.pop()
            depth = len(block_stack) + depth_offset + 1
            result.append(_ind(depth) + '}')

        depth = len(block_stack) + depth_offset + 1
        ind = _ind(depth)
        opens_block = False
        out = None

        printf_out = _py_print_to_printf(stripped, type_map)
        if stripped.startswith('#'):
            out = f'// {stripped.lstrip("#").strip()}'

        elif printf_out is not None:
            out = printf_out

        elif re.match(r'return\s*(.*)', stripped):
            m = re.match(r'return\s*(.*)', stripped)
            val = m.group(1).strip()
            out = f'return {val};' if val else 'return;'

        elif re.match(r'for (\w+) in range\(([^)]+)\):', stripped):
            m = re.match(r'for (\w+) in range\(([^)]+)\):', stripped)
            init, cond, inc = _py_range_to_c_for(m.group(1), m.group(2))
            out = f'for ({init}; {cond}; {inc}) {{'
            opens_block = True

        elif re.match(r'if (.+):$', stripped):
            m = re.match(r'if (.+):$', stripped)
            out = f'if ({m.group(1)}) {{'
            opens_block = True

        elif re.match(r'while (.+):$', stripped):
            m = re.match(r'while (.+):$', stripped)
            out = f'while ({m.group(1)}) {{'
            opens_block = True

        elif re.match(r'(\w+)\s*=\s*(-?\d+)$', stripped):
            m = re.match(r'(\w+)\s*=\s*(-?\d+)$', stripped)
            var = m.group(1)
            if var in type_map:
                out = f'{var} = {m.group(2)};'
            else:
                kind = planned_types[var]
                out = f'{kind} {var} = {m.group(2)};'
                type_map[var] = kind

        elif re.match(r'(\w+)\s*=\s*(-?\d+\.\d+)$', stripped):
            m = re.match(r'(\w+)\s*=\s*(-?\d+\.\d+)$', stripped)
            var = m.group(1)
            if var in type_map:
                out = f'{var} = {m.group(2)};'
            else:
                out = f'double {var} = {m.group(2)};'
                type_map[var] = 'double'

        elif re.match(r'(\w+)\s*=\s*(["\'])(.*)\2$', stripped):
            m = re.match(r'(\w+)\s*=\s*(["\'])(.*)\2$', stripped)
            var = m.group(1)
            value = ast.literal_eval(stripped.split('=', 1)[1].strip())
            capacity = len(value.encode('utf-8')) + 1
            if var in type_map:
                if type_map[var] != 'char[]' or var not in string_capacities:
                    raise ValueError(f'Unsupported string reassignment for {var}.')
                if capacity > string_capacities[var]:
                    raise ValueError(f'String reassignment exceeds UTF-8 capacity for {var}.')
                out = f'strcpy({var}, {_c_string(value)});'
            else:
                out = f'char {var}[{capacity}] = {_c_string(value)};'
                type_map[var] = 'char[]'
                string_capacities[var] = capacity

        else:
            out = f'{stripped};'

        result.append(ind + out)
        if opens_block:
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')

    while block_stack:
        block_stack.pop()
        block_kinds.pop()
        depth = len(block_stack) + depth_offset + 1
        result.append(_ind(depth) + '}')

    return result


def _process_python_to_java_body(lines, depth_offset=0, type_map=None):
    """Convert a list of Python lines to Java lines (without outer braces).
    type_map: dict {var_name: java_type} for tracking declarations.
    """
    if type_map is None:
        type_map = {}
    planned_types = _assignment_types(lines)
    result = []
    block_stack = []
    block_kinds = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        py_level = _py_indent_level(raw)

        m_elif = re.match(r'elif (.+):$', stripped)
        if m_elif or stripped == 'else:':
            while block_stack and block_stack[-1] > py_level:
                block_stack.pop()
                block_kinds.pop()
                result.append(_ind(len(block_stack) + depth_offset + 1) + '}')
            if not block_stack or block_stack[-1] != py_level or block_kinds[-1] != 'if':
                raise ValueError('Unsupported branch: else/elif must belong to an if block.')
            block_stack.pop()
            block_kinds.pop()
            ind = _ind(len(block_stack) + depth_offset + 1)
            if m_elif:
                result.append(ind + f'}} else if ({m_elif.group(1)}) {{')
            else:
                result.append(ind + '} else {')
            block_stack.append(py_level)
            block_kinds.append('if' if m_elif else 'other')
            continue

        while block_stack and block_stack[-1] >= py_level:
            block_stack.pop()
            block_kinds.pop()
            depth = len(block_stack) + depth_offset + 1
            result.append(_ind(depth) + '}')

        depth = len(block_stack) + depth_offset + 1
        ind = _ind(depth)
        opens_block = False
        out = None

        println_out = _py_print_to_println(stripped)
        if stripped.startswith('#'):
            out = f'// {stripped.lstrip("#").strip()}'

        elif println_out is not None:
            out = println_out

        elif re.match(r'return\s*(.*)', stripped):
            m = re.match(r'return\s*(.*)', stripped)
            val = m.group(1).strip()
            out = f'return {val};' if val else 'return;'

        elif re.match(r'for (\w+) in range\(([^)]+)\):', stripped):
            m = re.match(r'for (\w+) in range\(([^)]+)\):', stripped)
            init, cond, inc = _py_range_to_c_for(m.group(1), m.group(2))
            out = f'for ({init}; {cond}; {inc}) {{'
            opens_block = True

        elif re.match(r'if (.+):$', stripped):
            m = re.match(r'if (.+):$', stripped)
            out = f'if ({m.group(1)}) {{'
            opens_block = True

        elif re.match(r'while (.+):$', stripped):
            m = re.match(r'while (.+):$', stripped)
            out = f'while ({m.group(1)}) {{'
            opens_block = True

        elif re.match(r'(\w+)\s*=\s*(-?\d+)$', stripped):
            m = re.match(r'(\w+)\s*=\s*(-?\d+)$', stripped)
            var = m.group(1)
            if var in type_map:
                out = f'{var} = {m.group(2)};'
            else:
                kind = planned_types[var]
                out = f'{kind} {var} = {m.group(2)};'
                type_map[var] = kind

        elif re.match(r'(\w+)\s*=\s*(-?\d+\.\d+)$', stripped):
            m = re.match(r'(\w+)\s*=\s*(-?\d+\.\d+)$', stripped)
            var = m.group(1)
            if var in type_map:
                out = f'{var} = {m.group(2)};'
            else:
                out = f'double {var} = {m.group(2)};'
                type_map[var] = 'double'

        elif re.match(r'(\w+)\s*=\s*(["\'])(.*)\2$', stripped):
            m = re.match(r'(\w+)\s*=\s*(["\'])(.*)\2$', stripped)
            var = m.group(1)
            if var in type_map:
                out = f'{var} = "{m.group(3)}";'
            else:
                out = f'String {var} = "{m.group(3)}";'
                type_map[var] = 'String'

        else:
            out = f'{stripped};'

        result.append(ind + out)
        if opens_block:
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')

    while block_stack:
        block_stack.pop()
        block_kinds.pop()
        depth = len(block_stack) + depth_offset + 1
        result.append(_ind(depth) + '}')

    return result


# ─────────────────────────────────────────────
#  PYTHON → C
# ─────────────────────────────────────────────

def python_to_c(code: str) -> str:
    """Convert Python source to C.
    Top-level def blocks are emitted as standalone C functions (outside main).
    Variable re-declarations are tracked to avoid duplicate type prefixes.
    """
    lines = code.split('\n')
    func_blocks, main_lines = _extract_toplevel_funcs(lines)

    result = ['#include <stdio.h>', '#include <string.h>', '']

    # Emit top-level functions before main()
    for func_lines in func_blocks:
        m = re.match(r'def (\w+)\(([^)]*)\):', func_lines[0].strip())
        ret_type = 'int' if _has_return_value(func_lines) else 'void'
        result.append(f'{ret_type} {m.group(1)}({m.group(2)}) {{')
        body = _process_python_to_c_body(func_lines[1:], depth_offset=0, type_map={})
        result.extend(body)
        result.append('}')
        result.append('')

    result.append('int main() {')
    body = _process_python_to_c_body(main_lines, depth_offset=0, type_map={})
    result.extend(body)
    result.append('    return 0;')
    result.append('}')
    return '\n'.join(result)


# ─────────────────────────────────────────────
#  PYTHON → JAVA
# ─────────────────────────────────────────────

def python_to_java(code: str) -> str:
    """Convert Python source to Java.
    Top-level def blocks are emitted as static methods in the class (outside main).
    Variable re-declarations are tracked to avoid duplicate type prefixes.
    """
    lines = code.split('\n')
    func_blocks, main_lines = _extract_toplevel_funcs(lines)

    result = ['public class Main {']

    # Emit top-level functions as static methods before main()
    for func_lines in func_blocks:
        m = re.match(r'def (\w+)\(([^)]*)\):', func_lines[0].strip())
        ret_type = 'int' if _has_return_value(func_lines) else 'void'
        result.append(f'    static {ret_type} {m.group(1)}({m.group(2)}) {{')
        body = _process_python_to_java_body(func_lines[1:], depth_offset=1, type_map={})
        result.extend(body)
        result.append('    }')
        result.append('')

    result.append('    public static void main(String[] args) {')
    body = _process_python_to_java_body(main_lines, depth_offset=1, type_map={})
    result.extend(body)
    result.append('    }')
    result.append('}')
    return '\n'.join(result)


# ─────────────────────────────────────────────
#  C → PYTHON
# ─────────────────────────────────────────────

def c_to_python(code: str) -> str:
    lines = code.split('\n')
    result = []
    depth = 0  # brace depth → Python indentation level

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        # Skip preprocessor directives and main signature
        if stripped.startswith('#include') or stripped.startswith('#define'):
            continue
        if re.match(r'(?:int|void)\s+main\s*\(', stripped):
            continue
        if stripped in ('return 0;', 'return;'):
            continue

        # Closing brace — decrease depth first, then check for else chains
        if stripped.startswith('}'):
            depth = max(0, depth - 1)
            m = re.match(r'\}\s*else\s+if\s*\((.+)\)\s*\{?', stripped)
            if m:
                result.append(_ind(depth) + f'elif {m.group(1)}:')
                depth += 1
                continue
            if re.match(r'\}\s*else\s*\{?', stripped):
                result.append(_ind(depth) + 'else:')
                depth += 1
                continue
            continue

        ind = _ind(depth)

        # Line comment
        if stripped.startswith('//'):
            result.append(ind + '# ' + stripped[2:].strip())
            continue

        # printf → print
        p = _printf_to_print(stripped)
        if p:
            result.append(ind + p)
            continue

        # scanf → input()
        m_scanf = re.match(r'scanf\s*\("([^"]+)",\s*(.+)\);$', stripped)
        if m_scanf:
            fmt = m_scanf.group(1)
            args = [a.strip().lstrip('&') for a in m_scanf.group(2).split(',')]
            if len(args) == 1:
                if re.search(r'%[di]', fmt):
                    result.append(ind + f'{args[0]} = int(input())')
                elif re.search(r'%[ef]', fmt):
                    result.append(ind + f'{args[0]} = float(input())')
                else:
                    result.append(ind + f'{args[0]} = input()')
            else:
                result.append(ind + ', '.join(args) + ' = map(int, input().split())')
            continue

        # for loop
        if stripped.startswith('for'):
            py_for = _c_for_to_python(stripped)
            if py_for:
                result.append(ind + py_for)
                if stripped.rstrip().endswith('{'):
                    depth += 1
                continue

        # if (cond) {
        m = re.match(r'if\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'if {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # else if (cond) { — without leading }
        m = re.match(r'else\s+if\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'elif {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # else {
        if re.match(r'else\s*\{?$', stripped):
            result.append(ind + 'else:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # while (cond)
        m = re.match(r'while\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'while {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # Standalone opening brace
        if stripped == '{':
            depth += 1
            continue

        # Variable declaration with init: int x = 5;
        m = re.match(r'(?:int|long|short|unsigned\s+int|unsigned)\s+(\w+)\s*=\s*(.+);$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = {m.group(2)}')
            continue

        m = re.match(r'(?:double|float)\s+(\w+)\s*=\s*(.+);$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = {m.group(2)}')
            continue

        m = re.match(r'char\s+(\w+)\[\s*\]\s*=\s*"(.*)";$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = "{m.group(2)}"')
            continue

        # Variable declaration without init: int i; — skip
        if re.match(r'(?:int|long|short|double|float|char|unsigned)\s+\w+(\[\])?;$', stripped):
            continue

        # Inline opening brace at end (e.g. a stray line ending with {)
        if stripped.endswith('{'):
            result.append(ind + stripped.rstrip('{').strip())
            depth += 1
            continue

        # Generic: strip trailing semicolon
        result.append(ind + stripped.rstrip(';'))

    return '\n'.join(result)


# ─────────────────────────────────────────────
#  JAVA → PYTHON
# ─────────────────────────────────────────────

def java_to_python(code: str) -> str:
    lines = code.split('\n')
    result = []
    depth = 0

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        # Skip class/method declarations
        if re.match(r'public\s+class\s+', stripped):
            continue
        if re.match(r'(?:public\s+)?static\s+void\s+main\s*\(', stripped):
            continue
        if re.match(r'public\s+static\s+', stripped):
            continue

        # Closing brace
        if stripped.startswith('}'):
            depth = max(0, depth - 1)
            m = re.match(r'\}\s*else\s+if\s*\((.+)\)\s*\{?', stripped)
            if m:
                result.append(_ind(depth) + f'elif {m.group(1)}:')
                depth += 1
                continue
            if re.match(r'\}\s*else\s*\{?', stripped):
                result.append(_ind(depth) + 'else:')
                depth += 1
                continue
            continue

        if stripped == '{':
            depth += 1
            continue

        ind = _ind(depth)

        if stripped.startswith('//'):
            result.append(ind + '# ' + stripped[2:].strip())
            continue

        # System.out.println("...")
        m = re.match(r'System\.out\.println\("(.*)"\);', stripped)
        if m:
            result.append(ind + f'print("{m.group(1)}")')
            continue

        # System.out.println(var)
        m = re.match(r'System\.out\.println\((.+)\);', stripped)
        if m:
            result.append(ind + f'print({m.group(1).strip()})')
            continue

        # for loop
        if stripped.startswith('for'):
            py_for = _c_for_to_python(stripped)
            if py_for:
                result.append(ind + py_for)
                if stripped.rstrip().endswith('{'):
                    depth += 1
                continue

        # if
        m = re.match(r'if\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'if {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # else if
        m = re.match(r'else\s+if\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'elif {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # else
        if re.match(r'else\s*\{?$', stripped):
            result.append(ind + 'else:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # while
        m = re.match(r'while\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'while {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # int/long var = val;
        m = re.match(r'(?:int|long|short)\s+(\w+)\s*=\s*(.+);$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = {m.group(2)}')
            continue

        # double/float var = val;
        m = re.match(r'(?:double|float)\s+(\w+)\s*=\s*(.+);$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = {m.group(2)}')
            continue

        # String var = "...";
        m = re.match(r'String\s+(\w+)\s*=\s*"(.*)";$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = "{m.group(2)}"')
            continue

        # Declaration without init — skip
        if re.match(r'(?:int|long|short|double|float|String|char)\s+\w+;$', stripped):
            continue

        if stripped.endswith('{'):
            depth += 1
            continue

        result.append(ind + stripped.rstrip(';'))

    return '\n'.join(result)


# ─────────────────────────────────────────────
#  C → JAVA
# ─────────────────────────────────────────────

def c_to_java(code: str) -> str:
    lines = code.split('\n')
    result = ['public class Main {', '    public static void main(String[] args) {']
    depth = 2  # start inside class + main

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        if stripped.startswith('#include') or stripped.startswith('#define'):
            continue
        if re.match(r'(?:int|void)\s+main\s*\(', stripped):
            continue
        if stripped in ('return 0;', 'return;'):
            continue

        # Closing brace
        if stripped.startswith('}'):
            old_depth = depth
            depth = max(2, depth - 1)
            if old_depth <= 2:
                # This is main's (or outer) closing brace — skip it
                continue
            m = re.match(r'\}\s*else\s+if\s*\((.+)\)\s*\{?', stripped)
            if m:
                result.append(_ind(depth) + f'}} else if ({m.group(1)}) {{')
                depth += 1
                continue
            if re.match(r'\}\s*else\s*\{?', stripped):
                result.append(_ind(depth) + '} else {')
                depth += 1
                continue
            result.append(_ind(depth) + '}')
            continue

        if stripped == '{':
            depth += 1
            continue

        ind = _ind(depth)

        if stripped.startswith('//'):
            result.append(ind + stripped)
            continue

        # printf → System.out.println
        literal = _literal_printf_text(stripped)
        if literal is not None:
            result.append(ind + f'System.out.println({json.dumps(literal, ensure_ascii=False)});')
            continue
        m = re.match(r'printf\("(.*)\\n"\);$', stripped)
        if m:
            result.append(ind + f'System.out.println("{m.group(1)}");')
            continue

        m = re.match(r'printf\("(.*)\\n",\s*(.+)\);$', stripped)
        if m:
            fmt = m.group(1)
            args = [a.strip() for a in m.group(2).split(',')]
            # Single format specifier with one arg → direct println
            if re.match(r'^%(?:\.\d+)?[dsficg]$', fmt) and len(args) == 1:
                result.append(ind + f'System.out.println({args[0]});')
            else:
                parts = re.split(r'(%(?:\.\d+)?[dsficg])', fmt)
                arg_idx = 0
                java_parts = []
                for part in parts:
                    if re.match(r'%(?:\.\d+)?[dsficg]', part) and arg_idx < len(args):
                        java_parts.append(args[arg_idx])
                        arg_idx += 1
                    elif part:
                        java_parts.append(f'"{part}"')
                java_str = ' + '.join(java_parts) if java_parts else '""'
                result.append(ind + f'System.out.println({java_str});')
            continue

        # for loop
        if stripped.startswith('for'):
            body = stripped.rstrip('{').strip()
            result.append(ind + body + (' {' if not body.endswith('{') else ''))
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # if/else if/else/while — keep as-is, adjust brace handling
        for pat in [r'if\s*\(', r'else\s+if\s*\(', r'while\s*\(']:
            if re.match(pat, stripped):
                body = stripped.rstrip('{').strip()
                result.append(ind + body + (' {' if stripped.rstrip().endswith('{') else ''))
                if stripped.rstrip().endswith('{'):
                    depth += 1
                break
        else:
            m = re.match(r'else\s*\{?$', stripped)
            if m:
                result.append(ind + 'else {')
                depth += 1
                continue

            # int/long var = val;  — same in Java
            m = re.match(r'(?:int|long|short)\s+(\w+)\s*=\s*(.+);$', stripped)
            if m:
                result.append(ind + f'int {m.group(1)} = {m.group(2)};')
                continue

            m = re.match(r'(?:double|float)\s+(\w+)\s*=\s*(.+);$', stripped)
            if m:
                result.append(ind + f'double {m.group(1)} = {m.group(2)};')
                continue

            # char x[] = "..."; → String x = "...";
            m = re.match(r'char\s+(\w+)\[\s*\]\s*=\s*"(.*)";$', stripped)
            if m:
                result.append(ind + f'String {m.group(1)} = "{m.group(2)}";')
                continue

            # Declaration without init
            if re.match(r'(?:int|long|short|double|float|char)\s+\w+(\[\])?;$', stripped):
                result.append(ind + re.sub(r'^char\s+(\w+)\[\];$', r'String \1;',
                                           re.sub(r'^(int|long|short)\s+', 'int ', stripped)))
                continue

            if stripped.endswith('{'):
                depth += 1

            result.append(ind + stripped)

    result.append('    }')
    result.append('}')
    return '\n'.join(result)


# ─────────────────────────────────────────────
#  JAVA → C
# ─────────────────────────────────────────────

def java_to_c(code: str) -> str:
    lines = code.split('\n')
    result = ['#include <stdio.h>', '#include <string.h>', '', 'int main() {']
    depth = 1  # start inside main

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        if re.match(r'public\s+class\s+', stripped):
            continue
        if re.match(r'(?:public\s+)?static\s+void\s+main\s*\(', stripped):
            continue
        if re.match(r'public\s+static\s+', stripped):
            continue

        # Closing brace
        if stripped.startswith('}'):
            old_depth = depth
            depth = max(1, depth - 1)
            if old_depth <= 1:
                # This is class/main's closing brace — skip it
                continue
            m = re.match(r'\}\s*else\s+if\s*\((.+)\)\s*\{?', stripped)
            if m:
                result.append(_ind(depth) + f'}} else if ({m.group(1)}) {{')
                depth += 1
                continue
            if re.match(r'\}\s*else\s*\{?', stripped):
                result.append(_ind(depth) + '} else {')
                depth += 1
                continue
            result.append(_ind(depth) + '}')
            continue

        if stripped == '{':
            depth += 1
            continue

        ind = _ind(depth)

        if stripped.startswith('//'):
            result.append(ind + stripped)
            continue

        # System.out.println("...")
        m = re.match(r'System\.out\.println\("(.*)"\);', stripped)
        if m:
            result.append(ind + f'printf("%s", {_c_string(ast.literal_eval(chr(34) + m.group(1) + chr(34)) + chr(10))});')
            continue

        # System.out.println(var)
        m = re.match(r'System\.out\.println\((.+)\);', stripped)
        if m:
            arg = m.group(1).strip()
            if re.match(r'^"', arg):
                raise ValueError("Unsupported Java print string expression.")
            else:
                result.append(ind + f'printf("%d\\n", {arg});')
            continue

        # for loop
        if stripped.startswith('for'):
            body = stripped.rstrip('{').strip()
            result.append(ind + body + (' {' if stripped.rstrip().endswith('{') else ''))
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # if/else if/while
        for pat in [r'if\s*\(', r'else\s+if\s*\(', r'while\s*\(']:
            if re.match(pat, stripped):
                body = stripped.rstrip('{').strip()
                result.append(ind + body + (' {' if stripped.rstrip().endswith('{') else ''))
                if stripped.rstrip().endswith('{'):
                    depth += 1
                break
        else:
            if re.match(r'else\s*\{?$', stripped):
                result.append(ind + 'else {')
                depth += 1
                continue

            # String x = "...";  →  char x[] = "...";
            m = re.match(r'String\s+(\w+)\s*=\s*"(.*)";$', stripped)
            if m:
                result.append(ind + f'char {m.group(1)}[] = {_c_string(ast.literal_eval(chr(34) + m.group(2) + chr(34)))};')
                continue

            # int/double var = val;
            m = re.match(r'(?:int|long|short)\s+(\w+)\s*=\s*(.+);$', stripped)
            if m:
                result.append(ind + f'int {m.group(1)} = {m.group(2)};')
                continue

            m = re.match(r'(?:double|float)\s+(\w+)\s*=\s*(.+);$', stripped)
            if m:
                result.append(ind + f'double {m.group(1)} = {m.group(2)};')
                continue

            # String x; → char x[256];
            m = re.match(r'String\s+(\w+);$', stripped)
            if m:
                result.append(ind + f'char {m.group(1)}[256];')
                continue

            if stripped.endswith('{'):
                depth += 1

            result.append(ind + stripped)

    result.append('    return 0;')
    result.append('}')
    return '\n'.join(result)


# ─────────────────────────────────────────────
#  PYTHON → JAVASCRIPT
# ─────────────────────────────────────────────

def python_to_javascript(code: str) -> str:
    lines = code.split('\n')
    result = []
    block_stack = []
    block_kinds = []
    scopes = [(set(), True)]

    def declared(name):
        for names, function_scope in reversed(scopes):
            if name in names:
                return True
            if function_scope:
                break
        return False

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            result.append('')
            continue

        py_level = _py_indent_level(raw)

        # Close open blocks at same or lower indent
        m_elif = re.match(r'elif (.+):$', stripped)
        if m_elif or stripped == 'else:':
            while block_stack and block_stack[-1] > py_level:
                block_stack.pop()
                block_kinds.pop()
                scopes.pop()
                result.append(_ind(len(block_stack)) + '}')
            if not block_stack or block_stack[-1] != py_level or block_kinds[-1] != 'if':
                raise ValueError('Unsupported branch: else/elif must belong to an if block.')
            block_stack.pop()
            block_kinds.pop()
            scopes.pop()
            ind = _ind(len(block_stack))
            if m_elif:
                result.append(ind + f'}} else if ({m_elif.group(1)}) {{')
            else:
                result.append(ind + '} else {')
            block_stack.append(py_level)
            block_kinds.append('if' if m_elif else 'other')
            scopes.append((set(), False))
            continue

        while block_stack and block_stack[-1] >= py_level:
            block_stack.pop()
            block_kinds.pop()
            scopes.pop()
            result.append(_ind(len(block_stack)) + '}')

        ind = _ind(len(block_stack))

        # Comment
        if stripped.startswith('#'):
            result.append(ind + '// ' + stripped.lstrip('#').strip())
            continue

        # print( → console.log(
        m = re.match(r'print\(f(["\'])(.*)\1\)', stripped)
        if m:
            content = m.group(2)
            js_content = re.sub(r'\{(\w+)\}', r'${\1}', content)
            result.append(ind + f'console.log(`{js_content}`);')
            continue
        m = re.match(r'print\((["\'])(.*)\1\)', stripped)
        if m:
            result.append(ind + f'console.log("{m.group(2)}");')
            continue
        m = re.match(r'print\((.+)\)', stripped)
        if m:
            result.append(ind + f'console.log({m.group(1).strip()});')
            continue

        # def → function
        m = re.match(r'def (\w+)\(([^)]*)\):', stripped)
        if m:
            scopes[-1][0].add(m.group(1))
            result.append(ind + f'function {m.group(1)}({m.group(2)}) {{')
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')
            scopes.append(({param.split('=', 1)[0].strip() for param in m.group(2).split(',')}, True))
            continue

        # return
        m = re.match(r'return\s*(.*)', stripped)
        if m:
            val = m.group(1).strip()
            result.append(ind + (f'return {val};' if val else 'return;'))
            continue

        # for i in range(...)
        m = re.match(r'for (\w+) in range\(([^)]+)\):', stripped)
        if m:
            loop_var = m.group(1)
            already_declared = declared(loop_var)
            counter = loop_var
            if already_declared:
                counter = f'codeswitch_{loop_var}'
                while re.search(r'\b' + counter + r'\b', code):
                    counter += '_'
            init, cond, inc = _py_range_to_c_for(counter, m.group(2))
            init_js = re.sub(r'^int ', 'let ', init)
            result.append(ind + f'for ({init_js}; {cond}; {inc}) {{')
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')
            scopes.append(({counter}, False))
            if already_declared:
                result.append(_ind(len(block_stack)) + f'{loop_var} = {counter};')
            continue

        # if / elif / while
        m = re.match(r'if (.+):$', stripped)
        if m:
            result.append(ind + f'if ({m.group(1)}) {{')
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')
            scopes.append((set(), False))
            continue
        m = re.match(r'while (.+):$', stripped)
        if m:
            result.append(ind + f'while ({m.group(1)}) {{')
            block_stack.append(py_level)
            block_kinds.append('if' if stripped.startswith(('if ', 'elif ')) else 'other')
            scopes.append((set(), False))
            continue

        # Variable assignments  x = val  →  let x = val;
        m = re.match(r'([a-zA-Z_]\w*)\s*=\s*(.+)$', stripped)
        if m and not re.match(r'.*[=><!]=$', stripped):
            var = m.group(1)
            prefix = '' if declared(var) else 'let '
            if prefix:
                scopes[-1][0].add(var)
            result.append(ind + f'{prefix}{var} = {m.group(2)};')
            continue

        # Generic: add semicolon
        result.append(ind + stripped + ('' if stripped.endswith(';') else ';'))

    # Close remaining blocks
    while block_stack:
        block_stack.pop()
        block_kinds.pop()
        scopes.pop()
        result.append(_ind(len(block_stack)) + '}')

    return '\n'.join(result)


# ─────────────────────────────────────────────
#  JAVASCRIPT → PYTHON
# ─────────────────────────────────────────────

def javascript_to_python(code: str) -> str:
    lines = code.split('\n')
    result = []
    depth = 0

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        # Closing brace
        if stripped.startswith('}'):
            depth = max(0, depth - 1)
            m = re.match(r'\}\s*else\s+if\s*\((.+)\)\s*\{?', stripped)
            if m:
                result.append(_ind(depth) + f'elif {m.group(1)}:')
                depth += 1
                continue
            if re.match(r'\}\s*else\s*\{?', stripped):
                result.append(_ind(depth) + 'else:')
                depth += 1
                continue
            continue

        if stripped == '{':
            depth += 1
            continue

        ind = _ind(depth)

        # Comment
        if stripped.startswith('//'):
            result.append(ind + '# ' + stripped[2:].strip())
            continue

        # console.log with template literal
        m = re.match(r'console\.log\(`(.*)`\);?$', stripped)
        if m:
            content = m.group(1)
            py_content = re.sub(r'\$\{(\w+)\}', r'{\1}', content)
            result.append(ind + f'print(f"{py_content}")')
            continue

        # console.log("string")
        m = re.match(r'console\.log\("(.*)"\);?$', stripped)
        if m:
            result.append(ind + f'print("{m.group(1)}")')
            continue

        # console.log(expr)
        m = re.match(r'console\.log\((.+)\);?$', stripped)
        if m:
            result.append(ind + f'print({m.group(1).strip()})')
            continue

        # Supported named function declarations only.
        m = re.fullmatch(r'function\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*\{', stripped)
        if m:
            parameters = m.group(2).strip()
            if not re.fullmatch(r'(?:[a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)?', parameters):
                raise ValueError('Unsupported JavaScript function parameters.')
            result.append(ind + f'def {m.group(1)}({parameters}):')
            depth += 1
            continue
        if (re.search(r'^(?:(?:export|default|async)\s+)*function\b|=\s*(?:async\s+)?function\b', stripped)
                or re.search(r'(?:=\s*|^)(?:async\s+)?(?:\([^)]*\)|[a-zA-Z_]\w*)\s*=>', stripped)):
            raise ValueError('Unsupported JavaScript function declaration.')

        # return
        m = re.match(r'return\s*(.*?);?$', stripped)
        if m and stripped.startswith('return'):
            val = m.group(1).strip().rstrip(';')
            result.append(ind + (f'return {val}' if val else 'return'))
            continue

        # for (let i = ...)
        if stripped.startswith('for'):
            py_for = _c_for_to_python(stripped)
            if py_for:
                result.append(ind + py_for)
                if stripped.rstrip().endswith('{'):
                    depth += 1
                continue

        # if
        m = re.match(r'if\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'if {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # while
        m = re.match(r'while\s*\((.+)\)\s*\{?$', stripped)
        if m:
            result.append(ind + f'while {m.group(1)}:')
            if stripped.rstrip().endswith('{'):
                depth += 1
            continue

        # let/const/var declaration
        m = re.match(r'(?:let|const|var)\s+(\w+)\s*=\s*(.+?);?$', stripped)
        if m:
            result.append(ind + f'{m.group(1)} = {m.group(2).rstrip(";")}')
            continue

        # Generic: strip trailing semicolons
        result.append(ind + stripped.rstrip(';'))

    return '\n'.join(result)


# ─────────────────────────────────────────────
#  DISPATCH TABLE & ENTRY POINT
# ─────────────────────────────────────────────

CONVERTERS = {
    ('python', 'c'):          python_to_c,
    ('python', 'java'):       python_to_java,
    ('python', 'javascript'): python_to_javascript,
    ('c', 'python'):          c_to_python,
    ('java', 'python'):       java_to_python,
    ('javascript', 'python'): javascript_to_python,
    ('c', 'java'):            c_to_java,
    ('java', 'c'):            java_to_c,
}


def convert_code(source_lang: str, target_lang: str, code: str, user_key: str = None) -> dict:
    """
    Main entry point for code conversion.

    Strategy:
      1. Try AI-powered conversion first (if AI_API_KEY is configured).
      2. Fall back to the rule-based engine if AI is unavailable or errors.

    Returns {'success': True, 'output': str, 'engine': 'ai'|'rules'}
         or {'success': False, 'error': str}.
    """
    if source_lang == target_lang:
        return {'success': False, 'error': 'Source and target languages must be different.'}

    src = source_lang.lower()
    tgt = target_lang.lower()

    # ── 1. Attempt AI conversion ───────────────────────────────────────────────
    from .ai_service import ai_convert_code
    ai_result = ai_convert_code(src, tgt, code, user_key=user_key)
    if ai_result['success']:
        return ai_result

    metadata = {key: ai_result[key] for key in ('ai_error_code', 'ai_provider') if key in ai_result}

    # ── 2. Fall back to rule-based conversion ──────────────────────────────────
    converter = CONVERTERS.get((src, tgt))
    if not converter:
        return {
            'success': False,
            **metadata,
            'error': (
                f'Conversion from {source_lang} to {target_lang} is not supported. '
                f'(AI fallback reason: {ai_result.get("error", "unknown")})'
            )
        }

    try:
        output = converter(code)
        return {'success': True, 'output': output, 'engine': 'rules', **metadata}
    except Exception as e:
        return {'success': False, 'error': f'Conversion error: {str(e)}', **metadata}
