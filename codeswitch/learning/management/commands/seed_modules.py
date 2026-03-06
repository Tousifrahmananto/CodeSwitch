import json
from django.core.management.base import BaseCommand
from learning.models import LearningModule, Lesson

MODULES = [
    # ── Module 2: Working with Strings (beginner) ────────────────────────
    {
        'meta': {
            'title': 'Working with Strings',
            'description': 'Learn how C, Python, and Java handle text. Covers string creation, concatenation, slicing, searching, and formatting.',
            'difficulty': 'beginner',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'Declaring and Using Strings',
                'content': (
                    'Strings represent text in a program. The three languages store them very differently.\n\n'
                    'In C, a string is a character array ending with a null character (\\0). '
                    'In Python and Java, strings are full objects with built-in methods. '
                    'This means Python and Java strings are much easier to work with, '
                    'but understanding the C approach helps you appreciate what higher-level languages abstract away.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    char greeting[20] = "Hello, World!";\n'
                        '    printf("%s\\n", greeting);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': 'greeting = "Hello, World!"\nprint(greeting)',
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String greeting = "Hello, World!";\n'
                        '        System.out.println(greeting);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 1,
            },
            {
                'title': 'String Concatenation',
                'content': (
                    'Joining two strings together is called concatenation.\n\n'
                    'Python and Java use the + operator. C requires the strcat() function from string.h '
                    'and pre-allocated buffers, making it more error-prone but giving you full control over memory.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int main() {\n'
                        '    char result[40] = "Hello";\n'
                        '    strcat(result, " World");\n'
                        '    printf("%s\\n", result);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'first = "Hello"\n'
                        'second = " World"\n'
                        'result = first + second\n'
                        'print(result)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String first = "Hello";\n'
                        '        String second = " World";\n'
                        '        String result = first + second;\n'
                        '        System.out.println(result);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'String Length and Accessing Characters',
                'content': (
                    'You often need to know how long a string is or access individual characters.\n\n'
                    'C uses strlen() for length and bracket indexing for characters. '
                    'Python uses len() and the same bracket indexing, but also supports negative indices (text[-1] = last character). '
                    'Java uses the .length() method and .charAt(index).'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int main() {\n'
                        '    char text[] = "Hello";\n'
                        '    int len = strlen(text);\n'
                        '    printf("Length: %d\\n", len);\n'
                        '    printf("First: %c\\n", text[0]);\n'
                        '    printf("Last: %c\\n", text[len - 1]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'text = "Hello"\n'
                        'print("Length:", len(text))\n'
                        'print("First:", text[0])\n'
                        'print("Last:", text[-1])'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String text = "Hello";\n'
                        '        System.out.println("Length: " + text.length());\n'
                        '        System.out.println("First: " + text.charAt(0));\n'
                        '        System.out.println("Last: " + text.charAt(text.length() - 1));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Substrings and Slicing',
                'content': (
                    'Extracting part of a string is a very common operation.\n\n'
                    'C uses strncpy() which copies a fixed number of characters but requires manual null termination. '
                    'Python slicing syntax (text[start:end]) is elegant and safe. '
                    'Java uses substring(start, end) which returns a new String object.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int main() {\n'
                        '    char text[] = "Hello World";\n'
                        '    char sub[6];\n'
                        '    strncpy(sub, text, 5);\n'
                        '    sub[5] = \'\\0\';\n'
                        '    printf("%s\\n", sub);  // Hello\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'text = "Hello World"\n'
                        'sub = text[0:5]  # Hello\n'
                        'print(sub)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String text = "Hello World";\n'
                        '        String sub = text.substring(0, 5);  // Hello\n'
                        '        System.out.println(sub);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': 'Searching in Strings',
                'content': (
                    'Finding whether a word or character appears inside a string is called searching.\n\n'
                    'C uses strstr() which returns a pointer to the match (or NULL). '
                    'Python uses find() which returns the index (-1 if not found) or the in operator for a simple yes/no. '
                    'Java uses indexOf() returning -1 if not found, or contains() for a boolean result.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int main() {\n'
                        '    char text[] = "Hello World";\n'
                        '    char *pos = strstr(text, "World");\n'
                        '    if (pos != NULL) {\n'
                        '        printf("Found at index: %ld\\n", pos - text);\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'text = "Hello World"\n'
                        'index = text.find("World")\n'
                        'if index != -1:\n'
                        '    print("Found at index:", index)\n'
                        'print("Contains World:", "World" in text)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String text = "Hello World";\n'
                        '        int index = text.indexOf("World");\n'
                        '        if (index != -1) {\n'
                        '            System.out.println("Found at index: " + index);\n'
                        '        }\n'
                        '        System.out.println("Contains World: " + text.contains("World"));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
            {
                'title': 'String Formatting',
                'content': (
                    'Embedding variable values into a string for output is called string formatting.\n\n'
                    'C uses printf placeholders (%s for string, %d for integer). '
                    'Python f-strings (f"...{variable}...") were introduced in Python 3.6 and are very readable. '
                    'Java uses String.format() or printf(), which are similar to C but object-oriented.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    char name[] = "Alice";\n'
                        '    int age = 25;\n'
                        '    printf("Name: %s, Age: %d\\n", name, age);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'name = "Alice"\n'
                        'age = 25\n'
                        'print(f"Name: {name}, Age: {age}")'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        String name = "Alice";\n'
                        '        int age = 25;\n'
                        '        System.out.printf("Name: %s, Age: %d%n", name, age);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 6,
            },
        ],
    },

    # ── Module 3: Data Structures (intermediate) ─────────────────────────
    {
        'meta': {
            'title': 'Data Structures',
            'description': 'Explore arrays, lists, 2D arrays, and sorting. Learn how C, Python, and Java store and manipulate collections of data.',
            'difficulty': 'intermediate',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'Arrays and Lists',
                'content': (
                    'Arrays store multiple values of the same type in a sequence.\n\n'
                    'In C and Java, arrays are fixed-size — you must declare their length upfront and cannot grow them. '
                    'Python lists are dynamic: you can append, remove, and resize freely. '
                    'Java also has ArrayList for dynamic collections, but the plain array is still commonly used.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    int nums[5] = {10, 20, 30, 40, 50};\n'
                        '    for (int i = 0; i < 5; i++) {\n'
                        '        printf("%d\\n", nums[i]);\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'nums = [10, 20, 30, 40, 50]\n'
                        'for n in nums:\n'
                        '    print(n)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] nums = {10, 20, 30, 40, 50};\n'
                        '        for (int n : nums) {\n'
                        '            System.out.println(n);\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 1,
            },
            {
                'title': 'Adding and Removing Elements',
                'content': (
                    'Dynamic collections let you add and remove elements at runtime.\n\n'
                    'C arrays are fixed-size, so you simulate dynamic behavior by tracking a size variable and writing to slots manually. '
                    'Python lists have append() and remove() built in. '
                    'Java ArrayList (from java.util) provides the same convenience with add() and remove().'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    int arr[10] = {1, 2, 3, 4, 5};\n'
                        '    int size = 5;\n'
                        '    // "append" to the next slot\n'
                        '    arr[size] = 6;\n'
                        '    size++;\n'
                        '    printf("Size: %d, Last: %d\\n", size, arr[size - 1]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'nums = [1, 2, 3, 4, 5]\n'
                        'nums.append(6)\n'
                        'print("Size:", len(nums), " Last:", nums[-1])\n'
                        'nums.remove(3)\n'
                        'print("After removing 3:", nums)'
                    ),
                    'java': (
                        'import java.util.ArrayList;\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        ArrayList<Integer> nums = new ArrayList<>();\n'
                        '        for (int i = 1; i <= 5; i++) nums.add(i);\n'
                        '        nums.add(6);\n'
                        '        System.out.println("Size: " + nums.size() + " Last: " + nums.get(nums.size() - 1));\n'
                        '        nums.remove(Integer.valueOf(3));\n'
                        '        System.out.println("After removing 3: " + nums);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': '2D Arrays and Matrices',
                'content': (
                    'A 2D array is a grid of values — useful for matrices, grids, and tables.\n\n'
                    'C and Java declare 2D arrays with double brackets: int[3][3]. '
                    'Python uses a list of lists. Iterating requires nested loops in all three languages, '
                    'though Python\'s for-in loop over rows is the most readable.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    int matrix[3][3] = {\n'
                        '        {1, 2, 3},\n'
                        '        {4, 5, 6},\n'
                        '        {7, 8, 9}\n'
                        '    };\n'
                        '    for (int i = 0; i < 3; i++) {\n'
                        '        for (int j = 0; j < 3; j++) {\n'
                        '            printf("%d ", matrix[i][j]);\n'
                        '        }\n'
                        '        printf("\\n");\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'matrix = [\n'
                        '    [1, 2, 3],\n'
                        '    [4, 5, 6],\n'
                        '    [7, 8, 9]\n'
                        ']\n'
                        'for row in matrix:\n'
                        '    print(*row)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        int[][] matrix = {\n'
                        '            {1, 2, 3},\n'
                        '            {4, 5, 6},\n'
                        '            {7, 8, 9}\n'
                        '        };\n'
                        '        for (int[] row : matrix) {\n'
                        '            for (int val : row) System.out.print(val + " ");\n'
                        '            System.out.println();\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Linear Search',
                'content': (
                    'Searching for a value by checking each element one by one is called linear search.\n\n'
                    'It works on unsorted data and returns the index of the found element (or -1 if not found). '
                    'Linear search is O(n) — it gets slower as the list grows. '
                    'The algorithm is identical across languages; only the syntax differs.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int linearSearch(int arr[], int size, int target) {\n'
                        '    for (int i = 0; i < size; i++) {\n'
                        '        if (arr[i] == target) return i;\n'
                        '    }\n'
                        '    return -1;\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int nums[] = {4, 2, 7, 1, 9};\n'
                        '    printf("Found at index: %d\\n", linearSearch(nums, 5, 7));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def linear_search(arr, target):\n'
                        '    for i, val in enumerate(arr):\n'
                        '        if val == target:\n'
                        '            return i\n'
                        '    return -1\n\n'
                        'nums = [4, 2, 7, 1, 9]\n'
                        'print("Found at index:", linear_search(nums, 7))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int linearSearch(int[] arr, int target) {\n'
                        '        for (int i = 0; i < arr.length; i++) {\n'
                        '            if (arr[i] == target) return i;\n'
                        '        }\n'
                        '        return -1;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] nums = {4, 2, 7, 1, 9};\n'
                        '        System.out.println("Found at index: " + linearSearch(nums, 7));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': 'Bubble Sort',
                'content': (
                    'Bubble sort is one of the simplest sorting algorithms. It repeatedly steps through the list, '
                    'compares adjacent elements, and swaps them if they are in the wrong order.\n\n'
                    'It is not efficient for large datasets (O(n²)) but is easy to understand and a great starting point '
                    'for learning sorting. The logic is identical in all three languages.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'void bubbleSort(int arr[], int n) {\n'
                        '    for (int i = 0; i < n - 1; i++) {\n'
                        '        for (int j = 0; j < n - i - 1; j++) {\n'
                        '            if (arr[j] > arr[j + 1]) {\n'
                        '                int temp = arr[j];\n'
                        '                arr[j] = arr[j + 1];\n'
                        '                arr[j + 1] = temp;\n'
                        '            }\n'
                        '        }\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int nums[] = {5, 3, 8, 1, 2};\n'
                        '    bubbleSort(nums, 5);\n'
                        '    for (int i = 0; i < 5; i++) printf("%d ", nums[i]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def bubble_sort(arr):\n'
                        '    n = len(arr)\n'
                        '    for i in range(n - 1):\n'
                        '        for j in range(n - i - 1):\n'
                        '            if arr[j] > arr[j + 1]:\n'
                        '                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n'
                        '    return arr\n\n'
                        'nums = [5, 3, 8, 1, 2]\n'
                        'print(bubble_sort(nums))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static void bubbleSort(int[] arr) {\n'
                        '        int n = arr.length;\n'
                        '        for (int i = 0; i < n - 1; i++) {\n'
                        '            for (int j = 0; j < n - i - 1; j++) {\n'
                        '                if (arr[j] > arr[j + 1]) {\n'
                        '                    int temp = arr[j];\n'
                        '                    arr[j] = arr[j + 1];\n'
                        '                    arr[j + 1] = temp;\n'
                        '                }\n'
                        '            }\n'
                        '        }\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] nums = {5, 3, 8, 1, 2};\n'
                        '        bubbleSort(nums);\n'
                        '        for (int n : nums) System.out.print(n + " ");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
        ],
    },

    # ── Module 4: Object-Oriented Programming (intermediate) ─────────────
    {
        'meta': {
            'title': 'Object-Oriented Programming',
            'description': 'Understand classes, objects, inheritance, and encapsulation. See how OOP works in Python and Java, and how C approximates it with structs.',
            'difficulty': 'intermediate',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'Classes and Objects',
                'content': (
                    'A class is a blueprint for creating objects. An object is an instance of a class — it has data (fields/attributes) and behaviour (methods).\n\n'
                    'Python and Java have full class support. C has no classes, but structs group related data together and standalone functions act as the "methods". '
                    'Understanding the C struct approach makes Java and Python classes easier to appreciate.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        '// C uses structs as the closest equivalent\n'
                        'struct Person {\n'
                        '    char name[50];\n'
                        '    int age;\n'
                        '};\n\n'
                        'int main() {\n'
                        '    struct Person p;\n'
                        '    strcpy(p.name, "Alice");\n'
                        '    p.age = 25;\n'
                        '    printf("%s is %d years old\\n", p.name, p.age);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'class Person:\n'
                        '    def __init__(self, name, age):\n'
                        '        self.name = name\n'
                        '        self.age = age\n\n'
                        'p = Person("Alice", 25)\n'
                        'print(f"{p.name} is {p.age} years old")'
                    ),
                    'java': (
                        'public class Person {\n'
                        '    String name;\n'
                        '    int age;\n\n'
                        '    Person(String name, int age) {\n'
                        '        this.name = name;\n'
                        '        this.age = age;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        Person p = new Person("Alice", 25);\n'
                        '        System.out.println(p.name + " is " + p.age + " years old");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 1,
            },
            {
                'title': 'Methods and Behaviour',
                'content': (
                    'Methods are functions that belong to an object. They define what an object can do.\n\n'
                    'In Python, methods always take self as their first parameter — this refers to the current instance. '
                    'In Java, the equivalent keyword is this (implicit in most cases). '
                    'In C, you pass a pointer to the struct explicitly, since functions are not attached to types.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'struct Rectangle {\n'
                        '    double width;\n'
                        '    double height;\n'
                        '};\n\n'
                        'double area(struct Rectangle r) {\n'
                        '    return r.width * r.height;\n'
                        '}\n\n'
                        'int main() {\n'
                        '    struct Rectangle r = {5.0, 3.0};\n'
                        '    printf("Area: %.1f\\n", area(r));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'class Rectangle:\n'
                        '    def __init__(self, width, height):\n'
                        '        self.width = width\n'
                        '        self.height = height\n\n'
                        '    def area(self):\n'
                        '        return self.width * self.height\n\n'
                        'r = Rectangle(5.0, 3.0)\n'
                        'print("Area:", r.area())'
                    ),
                    'java': (
                        'public class Rectangle {\n'
                        '    double width, height;\n\n'
                        '    Rectangle(double width, double height) {\n'
                        '        this.width = width;\n'
                        '        this.height = height;\n'
                        '    }\n\n'
                        '    double area() {\n'
                        '        return width * height;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        Rectangle r = new Rectangle(5.0, 3.0);\n'
                        '        System.out.println("Area: " + r.area());\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Inheritance',
                'content': (
                    'Inheritance lets one class extend another, inheriting its fields and methods.\n\n'
                    'Python uses class Dog(Animal): syntax. Java uses class Dog extends Animal. '
                    'C does not support inheritance — the common workaround is embedding one struct inside another as the first member, '
                    'then casting pointers, but this is complex and rarely used compared to OOP languages.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        '// C: embed base struct to simulate inheritance\n'
                        'struct Animal {\n'
                        '    char name[50];\n'
                        '};\n\n'
                        'struct Dog {\n'
                        '    struct Animal base;\n'
                        '    char breed[50];\n'
                        '};\n\n'
                        'int main() {\n'
                        '    struct Dog d;\n'
                        '    strcpy(d.base.name, "Rex");\n'
                        '    strcpy(d.breed, "Labrador");\n'
                        '    printf("%s (%s)\\n", d.base.name, d.breed);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'class Animal:\n'
                        '    def __init__(self, name):\n'
                        '        self.name = name\n\n'
                        '    def speak(self):\n'
                        '        print(f"{self.name} speaks")\n\n'
                        'class Dog(Animal):\n'
                        '    def __init__(self, name, breed):\n'
                        '        super().__init__(name)\n'
                        '        self.breed = breed\n\n'
                        '    def speak(self):\n'
                        '        print(f"{self.name} says: Woof!")\n\n'
                        'd = Dog("Rex", "Labrador")\n'
                        'd.speak()'
                    ),
                    'java': (
                        'class Animal {\n'
                        '    String name;\n'
                        '    Animal(String name) { this.name = name; }\n'
                        '    void speak() { System.out.println(name + " speaks"); }\n'
                        '}\n\n'
                        'class Dog extends Animal {\n'
                        '    String breed;\n'
                        '    Dog(String name, String breed) {\n'
                        '        super(name);\n'
                        '        this.breed = breed;\n'
                        '    }\n'
                        '    void speak() { System.out.println(name + " says: Woof!"); }\n'
                        '}\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        Dog d = new Dog("Rex", "Labrador");\n'
                        '        d.speak();\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Encapsulation',
                'content': (
                    'Encapsulation means hiding internal data and only exposing it through controlled methods. '
                    'This prevents external code from putting an object into an invalid state.\n\n'
                    'Python uses double underscores (__balance) to make attributes private by convention. '
                    'Java uses the private keyword, which the compiler enforces strictly. '
                    'In C, you control access by only exposing functions in the header and keeping struct fields internal.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'struct BankAccount {\n'
                        '    double balance;  // "private" by convention\n'
                        '};\n\n'
                        'void deposit(struct BankAccount *acc, double amount) {\n'
                        '    if (amount > 0) acc->balance += amount;\n'
                        '}\n\n'
                        'double getBalance(struct BankAccount *acc) {\n'
                        '    return acc->balance;\n'
                        '}\n\n'
                        'int main() {\n'
                        '    struct BankAccount acc = {0.0};\n'
                        '    deposit(&acc, 500.0);\n'
                        '    deposit(&acc, 200.0);\n'
                        '    printf("Balance: %.2f\\n", getBalance(&acc));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'class BankAccount:\n'
                        '    def __init__(self):\n'
                        '        self.__balance = 0.0  # private\n\n'
                        '    def deposit(self, amount):\n'
                        '        if amount > 0:\n'
                        '            self.__balance += amount\n\n'
                        '    def get_balance(self):\n'
                        '        return self.__balance\n\n'
                        'acc = BankAccount()\n'
                        'acc.deposit(500.0)\n'
                        'acc.deposit(200.0)\n'
                        'print("Balance:", acc.get_balance())'
                    ),
                    'java': (
                        'public class BankAccount {\n'
                        '    private double balance = 0.0;\n\n'
                        '    public void deposit(double amount) {\n'
                        '        if (amount > 0) balance += amount;\n'
                        '    }\n\n'
                        '    public double getBalance() { return balance; }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        BankAccount acc = new BankAccount();\n'
                        '        acc.deposit(500.0);\n'
                        '        acc.deposit(200.0);\n'
                        '        System.out.println("Balance: " + acc.getBalance());\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
        ],
    },

    # ── Module 5: Error Handling & File I/O (advanced) ───────────────────
    {
        'meta': {
            'title': 'Error Handling and File I/O',
            'description': 'Handle errors gracefully and read/write files. Covers try/catch/except, raising exceptions, and file operations across all three languages.',
            'difficulty': 'advanced',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'Error Handling Approaches',
                'content': (
                    'Every language has a strategy for dealing with things that go wrong at runtime.\n\n'
                    'C uses return codes: functions return an integer where 0 means success and negative values indicate errors. '
                    'The caller must manually check every return value. This is powerful but easy to ignore.\n\n'
                    'Python and Java use exceptions: when something goes wrong, an exception object is thrown. '
                    'If nothing catches it, the program crashes with a helpful error message. '
                    'This is safer because you cannot silently ignore an exception.'
                ),
                'example_code': '',
                'order': 1,
            },
            {
                'title': 'Try / Catch / Except',
                'content': (
                    'Wrapping risky code in a try block lets you catch errors without crashing.\n\n'
                    'Python uses try/except. Java uses try/catch. C has no exception mechanism — '
                    'instead, you check return values and use if statements to handle error conditions.\n\n'
                    'Notice how Python and Java let you name the specific error type, '
                    'which makes it easy to handle different problems differently.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        '// C: return codes instead of exceptions\n'
                        'int divide(int a, int b, int *result) {\n'
                        '    if (b == 0) return -1;  // error\n'
                        '    *result = a / b;\n'
                        '    return 0;  // success\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int result;\n'
                        '    if (divide(10, 0, &result) != 0) {\n'
                        '        printf("Error: Division by zero\\n");\n'
                        '    } else {\n'
                        '        printf("Result: %d\\n", result);\n'
                        '    }\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'try:\n'
                        '    result = 10 / 0\n'
                        '    print("Result:", result)\n'
                        'except ZeroDivisionError:\n'
                        '    print("Error: Division by zero")\n'
                        'except Exception as e:\n'
                        '    print("Unexpected error:", e)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        try {\n'
                        '            int result = 10 / 0;\n'
                        '            System.out.println("Result: " + result);\n'
                        '        } catch (ArithmeticException e) {\n'
                        '            System.out.println("Error: Division by zero");\n'
                        '        } catch (Exception e) {\n'
                        '            System.out.println("Unexpected: " + e.getMessage());\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Throwing and Raising Exceptions',
                'content': (
                    'You can create your own error conditions using raise (Python) or throw (Java).\n\n'
                    'This is useful for enforcing rules in your functions — for example, rejecting negative ages. '
                    'In C, the equivalent is calling exit() or returning an error code and printing to stderr. '
                    'Python and Java let you attach a message to the exception so callers know exactly what went wrong.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <stdlib.h>\n\n'
                        'void checkAge(int age) {\n'
                        '    if (age < 0) {\n'
                        '        fprintf(stderr, "Error: Age cannot be negative\\n");\n'
                        '        exit(1);\n'
                        '    }\n'
                        '    printf("Age is valid: %d\\n", age);\n'
                        '}\n\n'
                        'int main() {\n'
                        '    checkAge(25);\n'
                        '    checkAge(-1);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def check_age(age):\n'
                        '    if age < 0:\n'
                        '        raise ValueError("Age cannot be negative")\n'
                        '    print("Age is valid:", age)\n\n'
                        'try:\n'
                        '    check_age(25)\n'
                        '    check_age(-1)\n'
                        'except ValueError as e:\n'
                        '    print("Error:", e)'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static void checkAge(int age) {\n'
                        '        if (age < 0) {\n'
                        '            throw new IllegalArgumentException("Age cannot be negative");\n'
                        '        }\n'
                        '        System.out.println("Age is valid: " + age);\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        try {\n'
                        '            checkAge(25);\n'
                        '            checkAge(-1);\n'
                        '        } catch (IllegalArgumentException e) {\n'
                        '            System.out.println("Error: " + e.getMessage());\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Reading from Files',
                'content': (
                    'Reading a file line by line is a fundamental operation in most programs.\n\n'
                    'C uses fopen() to get a file pointer and fgets() to read lines; you must always call fclose(). '
                    'Python\'s with statement automatically closes the file when the block ends — no risk of forgetting. '
                    'Java uses BufferedReader wrapped around a FileReader; the try-with-resources syntax (try(...)) handles closing automatically.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    FILE *file = fopen("data.txt", "r");\n'
                        '    if (file == NULL) {\n'
                        '        printf("Error: Could not open file\\n");\n'
                        '        return 1;\n'
                        '    }\n'
                        '    char line[100];\n'
                        '    while (fgets(line, sizeof(line), file)) {\n'
                        '        printf("%s", line);\n'
                        '    }\n'
                        '    fclose(file);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'try:\n'
                        '    with open("data.txt", "r") as file:\n'
                        '        for line in file:\n'
                        '            print(line, end="")\n'
                        'except FileNotFoundError:\n'
                        '    print("Error: Could not open file")'
                    ),
                    'java': (
                        'import java.io.*;\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        try (BufferedReader reader = new BufferedReader(new FileReader("data.txt"))) {\n'
                        '            String line;\n'
                        '            while ((line = reader.readLine()) != null) {\n'
                        '                System.out.println(line);\n'
                        '            }\n'
                        '        } catch (FileNotFoundException e) {\n'
                        '            System.out.println("Error: Could not open file");\n'
                        '        } catch (IOException e) {\n'
                        '            System.out.println("Read error: " + e.getMessage());\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': 'Writing to Files',
                'content': (
                    'Writing data to a file lets your program save results that persist after it closes.\n\n'
                    'C uses fprintf() to write formatted text to a file pointer opened with "w" mode. '
                    'Python uses file.write() inside a with block. '
                    'Java uses PrintWriter wrapped around a FileWriter; println() works the same way as System.out.\n\n'
                    'All three languages overwrite the file if it already exists when opened in write mode.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int main() {\n'
                        '    FILE *file = fopen("output.txt", "w");\n'
                        '    if (file == NULL) {\n'
                        '        printf("Error: Could not create file\\n");\n'
                        '        return 1;\n'
                        '    }\n'
                        '    fprintf(file, "Hello from C!\\n");\n'
                        '    fprintf(file, "Line 2\\n");\n'
                        '    fclose(file);\n'
                        '    printf("File written successfully\\n");\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'with open("output.txt", "w") as file:\n'
                        '    file.write("Hello from Python!\\n")\n'
                        '    file.write("Line 2\\n")\n'
                        'print("File written successfully")'
                    ),
                    'java': (
                        'import java.io.*;\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        try (PrintWriter writer = new PrintWriter(new FileWriter("output.txt"))) {\n'
                        '            writer.println("Hello from Java!");\n'
                        '            writer.println("Line 2");\n'
                        '            System.out.println("File written successfully");\n'
                        '        } catch (IOException e) {\n'
                        '            System.out.println("Error: " + e.getMessage());\n'
                        '        }\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
        ],
    },

    # ── Module 6: Algorithms and Recursion (advanced) ────────────────────
    {
        'meta': {
            'title': 'Algorithms and Recursion',
            'description': 'Tackle recursion, binary search, and selection sort. Understand how the same algorithm expresses itself differently in C, Python, and Java.',
            'difficulty': 'advanced',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'What is Recursion?',
                'content': (
                    'Recursion is when a function calls itself to solve a smaller version of the same problem.\n\n'
                    'Every recursive function needs two things:\n\n'
                    '1. A base case — a condition that stops the recursion (otherwise it runs forever)\n'
                    '2. A recursive case — where the function calls itself with a simpler input\n\n'
                    'Recursion is particularly elegant for problems that are naturally hierarchical or repetitive, '
                    'such as calculating factorials, traversing trees, or searching through nested structures. '
                    'The syntax for recursion is identical in concept across C, Python, and Java.'
                ),
                'example_code': '',
                'order': 1,
            },
            {
                'title': 'Recursive Factorial',
                'content': (
                    'Factorial (n!) multiplies all integers from 1 to n. For example: 5! = 5 × 4 × 3 × 2 × 1 = 120.\n\n'
                    'The recursive definition is: factorial(n) = n × factorial(n-1), with factorial(0) = 1 as the base case. '
                    'Each call shrinks the problem by 1 until it reaches the base case, then the results multiply back up the call stack.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int factorial(int n) {\n'
                        '    if (n <= 1) return 1;  // base case\n'
                        '    return n * factorial(n - 1);\n'
                        '}\n\n'
                        'int main() {\n'
                        '    printf("5! = %d\\n", factorial(5));\n'
                        '    printf("10! = %d\\n", factorial(10));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def factorial(n):\n'
                        '    if n <= 1:  # base case\n'
                        '        return 1\n'
                        '    return n * factorial(n - 1)\n\n'
                        'print("5! =", factorial(5))\n'
                        'print("10! =", factorial(10))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int factorial(int n) {\n'
                        '        if (n <= 1) return 1;  // base case\n'
                        '        return n * factorial(n - 1);\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        System.out.println("5! = " + factorial(5));\n'
                        '        System.out.println("10! = " + factorial(10));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Recursive Fibonacci',
                'content': (
                    'The Fibonacci sequence starts 0, 1, 1, 2, 3, 5, 8, 13... where each number is the sum of the previous two.\n\n'
                    'The recursive definition is: fib(n) = fib(n-1) + fib(n-2), with fib(0)=0 and fib(1)=1 as base cases. '
                    'Note: this naive recursive version is slow for large n because it recalculates the same values many times. '
                    'It is ideal for learning recursion, but in practice a loop or memoization is faster.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int fibonacci(int n) {\n'
                        '    if (n <= 1) return n;\n'
                        '    return fibonacci(n - 1) + fibonacci(n - 2);\n'
                        '}\n\n'
                        'int main() {\n'
                        '    for (int i = 0; i < 8; i++) {\n'
                        '        printf("%d ", fibonacci(i));\n'
                        '    }\n'
                        '    printf("\\n");\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def fibonacci(n):\n'
                        '    if n <= 1:\n'
                        '        return n\n'
                        '    return fibonacci(n - 1) + fibonacci(n - 2)\n\n'
                        'for i in range(8):\n'
                        '    print(fibonacci(i), end=" ")\n'
                        'print()'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int fibonacci(int n) {\n'
                        '        if (n <= 1) return n;\n'
                        '        return fibonacci(n - 1) + fibonacci(n - 2);\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        for (int i = 0; i < 8; i++) {\n'
                        '            System.out.print(fibonacci(i) + " ");\n'
                        '        }\n'
                        '        System.out.println();\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Binary Search',
                'content': (
                    'Binary search finds a value in a sorted array by repeatedly halving the search space.\n\n'
                    'At each step: look at the middle element. If it matches, return its index. '
                    'If the target is smaller, search the left half. If larger, search the right half. '
                    'This is O(log n) — far faster than linear search for large sorted arrays. '
                    'The algorithm is identical in all three languages.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int binarySearch(int arr[], int size, int target) {\n'
                        '    int left = 0, right = size - 1;\n'
                        '    while (left <= right) {\n'
                        '        int mid = (left + right) / 2;\n'
                        '        if (arr[mid] == target) return mid;\n'
                        '        else if (arr[mid] < target) left = mid + 1;\n'
                        '        else right = mid - 1;\n'
                        '    }\n'
                        '    return -1;\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int arr[] = {1, 3, 5, 7, 9, 11, 13};\n'
                        '    printf("Found at index: %d\\n", binarySearch(arr, 7, 7));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def binary_search(arr, target):\n'
                        '    left, right = 0, len(arr) - 1\n'
                        '    while left <= right:\n'
                        '        mid = (left + right) // 2\n'
                        '        if arr[mid] == target:\n'
                        '            return mid\n'
                        '        elif arr[mid] < target:\n'
                        '            left = mid + 1\n'
                        '        else:\n'
                        '            right = mid - 1\n'
                        '    return -1\n\n'
                        'arr = [1, 3, 5, 7, 9, 11, 13]\n'
                        'print("Found at index:", binary_search(arr, 7))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int binarySearch(int[] arr, int target) {\n'
                        '        int left = 0, right = arr.length - 1;\n'
                        '        while (left <= right) {\n'
                        '            int mid = (left + right) / 2;\n'
                        '            if (arr[mid] == target) return mid;\n'
                        '            else if (arr[mid] < target) left = mid + 1;\n'
                        '            else right = mid - 1;\n'
                        '        }\n'
                        '        return -1;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] arr = {1, 3, 5, 7, 9, 11, 13};\n'
                        '        System.out.println("Found at index: " + binarySearch(arr, 7));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': 'Selection Sort',
                'content': (
                    'Selection sort divides the array into a sorted part (left) and an unsorted part (right). '
                    'It repeatedly finds the minimum element in the unsorted part and moves it to the end of the sorted part.\n\n'
                    'Like bubble sort it is O(n²), but it makes fewer swaps — at most n-1. '
                    'It is easy to trace by hand and helps build intuition for more advanced sorting algorithms.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'void selectionSort(int arr[], int n) {\n'
                        '    for (int i = 0; i < n - 1; i++) {\n'
                        '        int minIdx = i;\n'
                        '        for (int j = i + 1; j < n; j++) {\n'
                        '            if (arr[j] < arr[minIdx]) minIdx = j;\n'
                        '        }\n'
                        '        int temp = arr[minIdx];\n'
                        '        arr[minIdx] = arr[i];\n'
                        '        arr[i] = temp;\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int arr[] = {64, 25, 12, 22, 11};\n'
                        '    selectionSort(arr, 5);\n'
                        '    for (int i = 0; i < 5; i++) printf("%d ", arr[i]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def selection_sort(arr):\n'
                        '    for i in range(len(arr) - 1):\n'
                        '        min_idx = i\n'
                        '        for j in range(i + 1, len(arr)):\n'
                        '            if arr[j] < arr[min_idx]:\n'
                        '                min_idx = j\n'
                        '        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n'
                        '    return arr\n\n'
                        'arr = [64, 25, 12, 22, 11]\n'
                        'print(selection_sort(arr))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static void selectionSort(int[] arr) {\n'
                        '        for (int i = 0; i < arr.length - 1; i++) {\n'
                        '            int minIdx = i;\n'
                        '            for (int j = i + 1; j < arr.length; j++) {\n'
                        '                if (arr[j] < arr[minIdx]) minIdx = j;\n'
                        '            }\n'
                        '            int temp = arr[minIdx];\n'
                        '            arr[minIdx] = arr[i];\n'
                        '            arr[i] = temp;\n'
                        '        }\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] arr = {64, 25, 12, 22, 11};\n'
                        '        selectionSort(arr);\n'
                        '        for (int n : arr) System.out.print(n + " ");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
            {
                'title': 'Recursion vs Loops',
                'content': (
                    'Both recursion and loops repeat work — but they do it differently, and each has strengths.\n\n'
                    '- Loops (for/while) are usually faster and use less memory because they do not build up a call stack\n'
                    '- Recursion is more readable for problems that are naturally self-similar (trees, nested structures, divide-and-conquer)\n'
                    '- Every recursive solution can be rewritten as a loop, and vice versa\n'
                    '- C and Java have a fixed call stack limit — deep recursion can cause a stack overflow\n'
                    '- Python also has a recursion limit (default 1000 calls) but it can be raised with sys.setrecursionlimit()\n\n'
                    'Rule of thumb: use loops for simple counting and iteration; use recursion when the problem naturally breaks into identical sub-problems.'
                ),
                'example_code': '',
                'order': 6,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed additional learning modules (beginner to advanced progression)'

    def handle(self, *args, **options):
        titles = [m['meta']['title'] for m in MODULES]
        deleted = LearningModule.objects.filter(title__in=titles).delete()

        created = 0
        for module_data in MODULES:
            module = LearningModule.objects.create(**module_data['meta'])
            for lesson_data in module_data['lessons']:
                Lesson.objects.create(module=module, **lesson_data)
            created += 1
            self.stdout.write(
                f'  Created "{module.title}" ({len(module_data["lessons"])} lessons, {module.difficulty})'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} modules created with '
            f'{sum(len(m["lessons"]) for m in MODULES)} total lessons.'
        ))
