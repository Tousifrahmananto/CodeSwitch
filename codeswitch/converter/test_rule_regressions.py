import shutil
import subprocess
from unittest import TestCase, skipUnless

from converter.services import (_c_for_to_python, _py_range_to_c_for, python_to_javascript,
                                javascript_to_python, python_to_c, python_to_java, java_to_python)
from converter import test_conversion_safety as c_safety


class FunctionAndBranchTests(TestCase):
    def test_named_javascript_function_becomes_executable_python(self):
        generated = javascript_to_python('function add(a, b) {\nreturn a + b;\n}\nconst result = add(1, 2);')
        scope = {}
        exec(generated, scope)
        self.assertEqual(scope['result'], 3)
        exec(javascript_to_python('const marker = "function =>";'), scope)
        self.assertEqual(scope['marker'], 'function =>')

    def test_unsupported_javascript_function_forms_are_rejected(self):
        for source in ['const f = (x) => x;', 'const f = function(x) {',
                       'function f(x = 1) {', 'function f(...args) {', 'async function f(x) {']:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'function'):
                javascript_to_python(source)

    def test_nested_branch_ownership_and_balanced_java_blocks(self):
        for x, expected in [(1, 'done'), (0, 'elif\ndone'), (3, 'outer\ndone')]:
            source = f'x = {x}\nif x == 1:\n    if x == 2:\n        print("inner")\nelif x == 0:\n    print("elif")\nelse:\n    print("outer")\nprint("done")'
            for converter in (python_to_c, python_to_java, python_to_javascript):
                with self.subTest(x=x, converter=converter.__name__):
                    generated = converter(source)
                    self.assertEqual(generated.count('{'), generated.count('}'))
                    if converter == python_to_c and shutil.which('gcc'):
                        actual = c_safety.CStringSafetyTests.compile_and_run(generated).decode().replace('\r\n', '\n').strip()
                    elif converter == python_to_javascript and shutil.which('node'):
                        actual = subprocess.check_output(['node', '-e', generated], text=True).strip()
                    elif converter == python_to_java:
                        import contextlib
                        import io
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            exec(java_to_python(generated), {})
                        actual = output.getvalue().strip()
                    else:
                        continue
                    self.assertEqual(actual, expected)

    def test_loop_else_is_explicitly_unsupported(self):
        for converter in (python_to_c, python_to_java, python_to_javascript):
            with self.subTest(converter=converter.__name__), self.assertRaisesRegex(ValueError, 'branch'):
                converter('for i in range(2):\n    print(i)\nelse:\n    print(3)')


class LoopAndDeclarationTests(TestCase):
    def test_c_style_loop_values_preserve_bounds_and_steps(self):
        cases = [
            ('for (int i=0; i<7; i+=2)', [0, 2, 4, 6]),
            ('for (int i=1; i<=7; i+=3)', [1, 4, 7]),
            ('for (int i=5; i>0; i--)', [5, 4, 3, 2, 1]),
            ('for (int i=5; i>=0; i-=2)', [5, 3, 1]),
            ('for (let i=0; i<3; i++)', [0, 1, 2]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                state = {'values': []}
                exec(_c_for_to_python(source) + '\n    values.append(i)', state)
                self.assertEqual(state['values'], expected)

    def test_zero_or_inconsistent_steps_are_rejected(self):
        for source in ['for (int i=0; i<7; i+=0)', 'for (int i=0; i>7; i++)',
                       'for (int i=7; i<0; i--)', 'for (int i=0; j<7; i++)']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                _c_for_to_python(source)
        for args in ('0, 5, 0', '0, 5, unknown', '0, 1, 2, 3'):
            with self.subTest(args=args), self.assertRaises(ValueError):
                _py_range_to_c_for('i', args)

    @skipUnless(shutil.which('node'), 'Node is needed for generated JavaScript execution')
    def test_repeated_assignments_and_accumulation_execute(self):
        for source, expected in [
            ('x = 1\nx = 2\nprint(x)', '2'),
            ('x = 0\nfor i in range(4):\n    x = x + i\nprint(x)', '6'),
            ('x = 1\ndef f(x):\n    x = x + 1\n    return x\nprint(f(x))\nprint(x)', '2\n1'),
            ('i = 0\nfor i in range(3):\n    print(i)\nprint(i)', '0\n1\n2\n2'),
            ('i = 50\nfor i in range(0):\n    print(i)\nprint(i)', '50'),
        ]:
            with self.subTest(source=source):
                output = subprocess.check_output(['node', '-e', python_to_javascript(source)], text=True)
                self.assertEqual(output.strip(), expected)
