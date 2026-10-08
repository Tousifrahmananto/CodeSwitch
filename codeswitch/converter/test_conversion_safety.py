import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, skipUnless

from converter.services import python_to_c, java_to_c, c_to_python, c_to_java


class CStringSafetyTests(TestCase):
    def test_safe_literal_output_is_recognized_by_reverse_converters(self):
        source = 'print("100% 猫")'
        generated = python_to_c(source)
        self.assertEqual(c_to_python(generated), "print('100% 猫')")
        self.assertIn('System.out.println("100% 猫");', c_to_java(generated))

    def test_string_growth_is_rejected_including_utf8_bytes(self):
        for code in ['s = "a"\ns = "longer"', 's = "aa"\ns = "猫"']:
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, 'capacity'):
                python_to_c(code)

    @skipUnless(shutil.which('gcc'), 'GCC is needed for generated C execution')
    def test_generated_literals_compile_and_preserve_output(self):
        fixtures = [
            'print("%s %n 100%")',
            r'''print('quotes " and slash \\ and Unicode 猫')''',
            's = "猫"\ns = "ab"\nprint(s)',
            'x = 3\nprint(f"100% = {x}%")',
            'print(f"100%")',
        ]
        for code in fixtures:
            with self.subTest(code=code):
                expected = subprocess.check_output([sys.executable, '-X', 'utf8', '-c', code])
                self.assertEqual(self.compile_and_run(python_to_c(code)), expected)

    @skipUnless(shutil.which('gcc'), 'GCC is needed for generated C execution')
    def test_java_literal_print_uses_safe_format(self):
        code = 'public class Main {\npublic static void main(String[] args) {\nSystem.out.println("100% %s");\n}\n}'
        self.assertEqual(self.compile_and_run(java_to_c(code)), b'100% %s\r\n' if sys.platform == 'win32' else b'100% %s\n')

    @staticmethod
    def compile_and_run(code):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'main.c'
            executable = Path(directory) / 'main.exe'
            source.write_text(code, encoding='utf-8')
            subprocess.run(['gcc', '-Werror=format', str(source), '-o', str(executable)],
                           check=True, capture_output=True)
            return subprocess.check_output([str(executable)])


class CStringRoundtripTests(TestCase):
    def test_sized_arrays_and_reassignments_roundtrip_to_python(self):
        import contextlib
        import io
        for source in ('s = "hi"\nprint(s)', 's = "猫"\ns = "ab"\nprint(s)',
                       's = "猫"\nprint(s)'):
            with self.subTest(source=source):
                expected = io.StringIO()
                with contextlib.redirect_stdout(expected):
                    exec(source, {})
                actual = io.StringIO()
                with contextlib.redirect_stdout(actual):
                    exec(c_to_python(python_to_c(source)), {})
                self.assertEqual(actual.getvalue(), expected.getvalue())
                java = c_to_java(python_to_c(source))
                self.assertNotIn('char s[', java)
                self.assertNotIn('strcpy', java)
                self.assertIn('String s =', java)

    def test_formatted_percentage_and_unicode_roundtrip(self):
        import contextlib
        import io
        source = 'x = 3\nprint(f"猫 100% = {x}%")'
        expected, actual = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(expected): exec(source,{})
        with contextlib.redirect_stdout(actual): exec(c_to_python(python_to_c(source)),{})
        self.assertEqual(actual.getvalue(), expected.getvalue())

    def test_formatted_strings_translate_to_java_with_decoded_text(self):
        generated = c_to_java(python_to_c('x = 3\nprint(f"猫 100% = {x}%")'))
        self.assertIn('String.format(java.util.Locale.ROOT, "猫 100%% = %d%%", x)', generated)
        self.assertNotIn('printf(', generated)
