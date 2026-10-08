import shutil
import subprocess
from unittest import TestCase, skipUnless

from converter.services import _c_for_to_python, _py_range_to_c_for, python_to_javascript


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
