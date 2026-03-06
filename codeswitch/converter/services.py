"""
CodeSwitch Conversion Engine (v2 - Improved Rule-Based)
-------------------------------------------------------
Translates common patterns between Python, C, and Java.
Handles indentation tracking, flexible for-loop patterns,
closing braces, and common language idioms.
"""
import re


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
    """
    Parse a C-style for loop and return a Python range() string.
    Handles: for(i=0;i<n;i++), for (int i=1; i<=10; i++), etc.
    Returns None if pattern not recognised.
    """
    body = s.rstrip('{').strip()
    m = re.match(
        r'for\s*\(\s*(?:int\s+)?(\w+)\s*=\s*([^;]+);\s*\w+\s*([<>]=?)\s*([^;]+);\s*\w+\s*(\+\+|--|\+=\s*\d+|-=\s*\d+)\s*\)',
        body
    )
    if not m:
        return None

    var = m.group(1)
    start = m.group(2).strip()
    op = m.group(3)
    end = m.group(4).strip()
    inc_raw = m.group(5).strip()

    if inc_raw == '++':
        step = 1
    elif inc_raw == '--':
        step = -1
    else:
        sm = re.match(r'([+-])=\s*(\d+)', inc_raw)
        if sm:
            step = int(sm.group(2)) if sm.group(1) == '+' else -int(sm.group(2))
        else:
            step = 1

    if step > 0:
        if op == '<':
            if start == '0':
                return f'for {var} in range({end}):'
            return f'for {var} in range({start}, {end}):'
        else:  # <=
            try:
                end_expr = str(int(end) + 1)
            except ValueError:
                end_expr = f'{end} + 1'
            if start == '0':
                return f'for {var} in range({end_expr}):'
            return f'for {var} in range({start}, {end_expr}):'
    else:
        if op == '>':
            try:
                end_expr = str(int(end) - 1)
            except ValueError:
                end_expr = f'{end} - 1'
            return f'for {var} in range({start}, {end_expr}, {step}):'
        else:  # >=
            if end == '0':
                return f'for {var} in range({start}, -1, {step}):'
            try:
                end_expr = str(int(end) - 1)
            except ValueError:
                end_expr = f'{end} - 1'
            return f'for {var} in range({start}, {end_expr}, {step}):'


def _py_range_to_c_for(var, range_str):
    """Convert Python range() args to C for-loop (init, cond, inc) tuple."""
    args = [a.strip() for a in range_str.split(',')]
    if len(args) == 1:
        return f'int {var} = 0', f'{var} < {args[0]}', f'{var}++'
    elif len(args) == 2:
        return f'int {var} = {args[0]}', f'{var} < {args[1]}', f'{var}++'
    else:
        try:
            step = int(args[2])
            if step == 1:
                return f'int {var} = {args[0]}', f'{var} < {args[1]}', f'{var}++'
            elif step == -1:
                return f'int {var} = {args[0]}', f'{var} > {args[1]}', f'{var}--'
            elif step > 0:
                return f'int {var} = {args[0]}', f'{var} < {args[1]}', f'{var} += {step}'
            else:
                return f'int {var} = {args[0]}', f'{var} > {args[1]}', f'{var} -= {-step}'
        except ValueError:
            return f'int {var} = {args[0]}', f'{var} < {args[1]}', f'{var} += {args[2]}'


def _printf_to_print(s):
    """Convert C printf(...) to Python print(...). Returns None if no match."""
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
            result_fmt = re.sub(r'%[dsfic]', '{' + arg + '}', result_fmt, count=1)
        if '{' in result_fmt:
            return f'print(f"{result_fmt}")'
        return f'print("{result_fmt}")'

    return None


def _py_print_to_printf(s, type_map=None):
    """Convert Python print(...) to C printf(...).
    type_map: dict of {var_name: c_type} used to pick the right format specifier.
    """
    if type_map is None:
        type_map = {}

    def _spec(var):
        t = type_map.get(var)
        if t == 'double':
            return '%f'
        if t == 'char[]':
            return '%s'
        return '%d'  # default to int — safer than %s for untyped variables

    # f-string: print(f"...")
    m = re.match(r'print\(f(["\'])(.*)\1\)', s)
    if m:
        content = m.group(2)
        vars_found = re.findall(r'\{(\w+)\}', content)
        fmt = content
        for v in vars_found:
            fmt = re.sub(r'\{' + v + r'\}', _spec(v), fmt, count=1)
        if vars_found:
            return f'printf("{fmt}\\n", {", ".join(vars_found)});'
        return f'printf("{fmt}\\n");'

    # String literal: print("...")
    m = re.match(r'print\((["\'])(.*)\1\)', s)
    if m:
        return f'printf("{m.group(2)}\\n");'

    # Variable/expression: print(x)
    m = re.match(r'print\((.+)\)', s)
    if m:
        arg = m.group(1).strip()
        if re.match(r'^[\w.]+$', arg):
            return f'printf("{_spec(arg)}\\n", {arg});'
        return f'printf("%d\\n", {arg});'

    return None


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


def _process_python_to_c_body(lines, depth_offset=0, type_map=None):
    """Convert a list of Python lines to C lines (without outer braces).
    depth_offset: base indentation level added to all output.
    type_map: dict {var_name: c_type} for resolving printf format specifiers.
              Modified in place as variable declarations are encountered.
    """
    if type_map is None:
        type_map = {}
    result = []
    block_stack = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        py_level = _py_indent_level(raw)

        m_elif = re.match(r'elif (.+):$', stripped)
        if m_elif or stripped == 'else:':
            while block_stack and block_stack[-1] >= py_level:
                block_stack.pop()
            depth = len(block_stack) + depth_offset + 1
            if m_elif:
                result.append(_ind(depth) + f'}} else if ({m_elif.group(1)}) {{')
            else:
                result.append(_ind(depth) + '} else {')
            block_stack.append(py_level)
            continue

        while block_stack and block_stack[-1] >= py_level:
            block_stack.pop()
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
                out = f'int {var} = {m.group(2)};'
                type_map[var] = 'int'

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
                out = f'strcpy({var}, "{m.group(3)}");'
            else:
                out = f'char {var}[] = "{m.group(3)}";'
                type_map[var] = 'char[]'

        else:
            out = f'{stripped};'

        result.append(ind + out)
        if opens_block:
            block_stack.append(py_level)

    while block_stack:
        block_stack.pop()
        depth = len(block_stack) + depth_offset + 1
        result.append(_ind(depth) + '}')

    return result


def _process_python_to_java_body(lines, depth_offset=0, type_map=None):
    """Convert a list of Python lines to Java lines (without outer braces).
    type_map: dict {var_name: java_type} for tracking declarations.
    """
    if type_map is None:
        type_map = {}
    result = []
    block_stack = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        py_level = _py_indent_level(raw)

        m_elif = re.match(r'elif (.+):$', stripped)
        if m_elif or stripped == 'else:':
            while block_stack and block_stack[-1] >= py_level:
                block_stack.pop()
            depth = len(block_stack) + depth_offset + 1
            if m_elif:
                result.append(_ind(depth) + f'}} else if ({m_elif.group(1)}) {{')
            else:
                result.append(_ind(depth) + '} else {')
            block_stack.append(py_level)
            continue

        while block_stack and block_stack[-1] >= py_level:
            block_stack.pop()
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
                out = f'int {var} = {m.group(2)};'
                type_map[var] = 'int'

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

    while block_stack:
        block_stack.pop()
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
        m = re.match(r'printf\("(.*)\\n"\);$', stripped)
        if m:
            result.append(ind + f'System.out.println("{m.group(1)}");')
            continue

        m = re.match(r'printf\("(.*)\\n",\s*(.+)\);$', stripped)
        if m:
            fmt = m.group(1)
            args = [a.strip() for a in m.group(2).split(',')]
            # Single format specifier with one arg → direct println
            if re.match(r'^%[dsfic]$', fmt) and len(args) == 1:
                result.append(ind + f'System.out.println({args[0]});')
            else:
                parts = re.split(r'(%[dsfic])', fmt)
                arg_idx = 0
                java_parts = []
                for part in parts:
                    if re.match(r'%[dsfic]', part) and arg_idx < len(args):
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
            result.append(ind + f'printf("{m.group(1)}\\n");')
            continue

        # System.out.println(var)
        m = re.match(r'System\.out\.println\((.+)\);', stripped)
        if m:
            arg = m.group(1).strip()
            if re.match(r'^"', arg):
                result.append(ind + f'printf("{arg[1:-1]}\\n");')
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
                result.append(ind + f'char {m.group(1)}[] = "{m.group(2)}";')
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
#  DISPATCH TABLE & ENTRY POINT
# ─────────────────────────────────────────────

CONVERTERS = {
    ('python', 'c'):    python_to_c,
    ('python', 'java'): python_to_java,
    ('c', 'python'):    c_to_python,
    ('java', 'python'): java_to_python,
    ('c', 'java'):      c_to_java,
    ('java', 'c'):      java_to_c,
}


def convert_code(source_lang: str, target_lang: str, code: str) -> dict:
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
    ai_result = ai_convert_code(src, tgt, code)
    if ai_result['success']:
        return ai_result

    # ── 2. Fall back to rule-based conversion ──────────────────────────────────
    converter = CONVERTERS.get((src, tgt))
    if not converter:
        return {
            'success': False,
            'error': (
                f'Conversion from {source_lang} to {target_lang} is not supported. '
                f'(AI fallback reason: {ai_result.get("error", "unknown")})'
            )
        }

    try:
        output = converter(code)
        return {'success': True, 'output': output, 'engine': 'rules'}
    except Exception as e:
        return {'success': False, 'error': f'Conversion error: {str(e)}'}
