import json
from django.core.management.base import BaseCommand
from learning.models import LearningModule, Lesson


class Command(BaseCommand):
    help = 'Seed the learning module content from the CodeSwitch curriculum'

    def handle(self, *args, **options):
        LearningModule.objects.filter(title='CodeSwitch Learning Module').delete()

        module = LearningModule.objects.create(
            title='CodeSwitch Learning Module',
            description='Master code conversion between C, Python, and Java. Learn the key differences and how to translate programs across languages.',
            difficulty='beginner',
            language='general',
        )

        lessons = [
            {
                'title': 'Understanding Code Conversion',
                'content': (
                    'Code conversion means transforming a program written in one language into a functionally '
                    'equivalent program in another language. Each language has different syntax and conventions, '
                    'but the underlying logic remains the same.\n\n'
                    'CodeSwitch helps you learn these differences by showing how familiar programs look in '
                    'different languages. Whether you are moving from C to Python for readability, or from '
                    'Python to Java for type safety, the core logic stays the same — only the syntax changes.'
                ),
                'example_code': '',
                'order': 1,
            },
            {
                'title': 'Key Differences: C, Python, and Java',
                'content': (
                    'Before converting code, it helps to understand the major differences between the three languages:\n\n'
                    '| Concept | C | Python | Java |\n'
                    '| Program Structure | Functions + main() | Scripts / functions | Classes + main() |\n'
                    '| Printing Output | printf() | print() | System.out.println() |\n'
                    '| User Input | scanf() | input() | Scanner class |\n'
                    '| Syntax Style | Curly braces, semicolons | Indentation-based | Curly braces, semicolons |\n'
                    '| Typing | Static (explicit types) | Dynamic (no declarations) | Static (explicit types) |\n\n'
                    'Understanding these differences is the foundation of code conversion.'
                ),
                'example_code': '',
                'order': 2,
            },
            {
                'title': 'Converting Basic Input and Output',
                'content': (
                    'Input and output (I/O) is one of the most common things a program does. '
                    'Below is the same program — reading a name and printing a greeting — written in all three languages.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    char name[50];\n'
                        '    printf("Enter your name: ");\n'
                        '    scanf("%s", name);\n'
                        '    printf("Hello, %s!\\n", name);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'name = input("Enter your name: ")\n'
                        'print(f"Hello, {name}!")'
                    ),
                    'java': (
                        'import java.util.Scanner;\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        Scanner sc = new Scanner(System.in);\n'
                        '        System.out.print("Enter your name: ");\n'
                        '        String name = sc.nextLine();\n'
                        '        System.out.println("Hello, " + name + "!");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Converting Conditional Statements',
                'content': (
                    'Conditional statements let programs make decisions. The logic is identical across languages '
                    '— only the syntax differs. Python uses indentation to define blocks, while C and Java use curly braces.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    int x = 10;\n'
                        '    if (x > 5) {\n'
                        '        printf("x is greater than 5\\n");\n'
                        '    } else {\n'
                        '        printf("x is 5 or less\\n");\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'x = 10\n'
                        'if x > 5:\n'
                        '    print("x is greater than 5")\n'
                        'else:\n'
                        '    print("x is 5 or less")'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        int x = 10;\n'
                        '        if (x > 5) {\n'
                        '            System.out.println("x is greater than 5");\n'
                        '        } else {\n'
                        '            System.out.println("x is 5 or less");\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': 'Converting Loops',
                'content': (
                    'Loops repeat a block of code. Here is a for loop that counts from 1 to 5. '
                    "Notice how Python's range() replaces manual counter initialization from C and Java."
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    for (int i = 1; i <= 5; i++) {\n'
                        '        printf("%d\\n", i);\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'for i in range(1, 6):\n'
                        '    print(i)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        for (int i = 1; i <= 5; i++) {\n'
                        '            System.out.println(i);\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
            {
                'title': 'Converting Functions and Methods',
                'content': (
                    'Functions allow code reuse. Here is a function that adds two numbers. '
                    'In Java, all functions must live inside a class, whereas C and Python allow standalone functions.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int add(int a, int b) {\n'
                        '    return a + b;\n'
                        '}\n\n'
                        'int main() {\n'
                        '    printf("%d\\n", add(3, 4));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def add(a, b):\n'
                        '    return a + b\n\n'
                        'print(add(3, 4))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int add(int a, int b) {\n'
                        '        return a + b;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        System.out.println(add(3, 4));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 6,
            },
            {
                'title': 'Learning Through CodeSwitch',
                'content': (
                    'CodeSwitch is designed to make learning code conversion easy and interactive. '
                    'Here is how to get the most out of it:\n\n'
                    '- Use the Converter to paste real code and see the result instantly\n'
                    '- Save interesting conversions to My Files for future reference\n'
                    '- Compare how different languages structure the same logic\n'
                    '- Learn by experimenting — change a detail and convert again\n'
                    '- Revisit these lessons whenever you encounter unfamiliar syntax'
                ),
                'example_code': '',
                'order': 7,
            },
            {
                'title': 'Recommended Learning Path',
                'content': (
                    'Follow these steps to build your code conversion skills:\n\n'
                    '1. Start with the Language Comparison lesson to understand the key differences\n'
                    '2. Work through I/O, Conditionals, Loops, and Functions in order\n'
                    '3. After each lesson, open the Converter and try converting one of the examples yourself\n'
                    '4. Save interesting conversions to My Files to build a personal reference library\n'
                    '5. Return to these lessons whenever you encounter unfamiliar syntax in a conversion'
                ),
                'example_code': '',
                'order': 8,
            },
        ]

        for data in lessons:
            Lesson.objects.create(module=module, **data)

        self.stdout.write(self.style.SUCCESS(
            f'Created module "{module.title}" with {len(lessons)} lessons.'
        ))
