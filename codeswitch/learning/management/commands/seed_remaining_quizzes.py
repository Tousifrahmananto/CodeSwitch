"""
Management command: seed_remaining_quizzes
Seeds 3 questions per lesson for every lesson that does not yet have a quiz.
Covers all pages (lessons) across all 9 modules.
"""
from django.core.management.base import BaseCommand
from learning.models import Lesson, Quiz, QuizQuestion, QuizOption

QUIZ_DATA = {
    # ── Module 1: CodeSwitch Learning Module ──────────────────────────────
    2: {  # Key Differences: C, Python, and Java
        'title': 'Language Differences Quiz',
        'questions': [
            {
                'text': 'How does Python define code blocks compared to C and Java?',
                'options': [
                    ('Using curly braces { } like C and Java', False),
                    ('Using indentation', True),
                    ('Using BEGIN / END keywords', False),
                    ('Using semicolons at the end of each block', False),
                ],
            },
            {
                'text': 'Which languages require explicit type declarations for variables?',
                'options': [
                    ('Python only', False),
                    ('C and Java', True),
                    ('Java only', False),
                    ('None of them — all are dynamically typed', False),
                ],
            },
            {
                'text': 'How do you print output to the console in Java?',
                'options': [
                    ('print()', False),
                    ('printf()', False),
                    ('System.out.println()', True),
                    ('echo()', False),
                ],
            },
        ],
    },
    3: {  # Converting Basic Input and Output
        'title': 'Input and Output Quiz',
        'questions': [
            {
                'text': 'How do you read user input from the console in Python?',
                'options': [
                    ('scanf()', False),
                    ('input()', True),
                    ('readline()', False),
                    ('read()', False),
                ],
            },
            {
                'text': 'In C, which function is used to print formatted output?',
                'options': [
                    ('print()', False),
                    ('echo()', False),
                    ('printf()', True),
                    ('output()', False),
                ],
            },
            {
                'text': 'In Java, which class is used to read user input from the console?',
                'options': [
                    ('InputReader', False),
                    ('BufferedReader only', False),
                    ('Scanner', True),
                    ('Console', False),
                ],
            },
        ],
    },
    4: {  # Converting Conditional Statements
        'title': 'Conditional Statements Quiz',
        'questions': [
            {
                'text': 'How does Python define the body of an if statement?',
                'options': [
                    ('Using curly braces { }', False),
                    ('Using indentation', True),
                    ('Using BEGIN / END keywords', False),
                    ('Using parentheses', False),
                ],
            },
            {
                'text': 'Which syntax is correct for a Python if-else statement?',
                'options': [
                    ('if (x > 5) { } else { }', False),
                    ('if x > 5 then ... end', False),
                    ('if x > 5:\\n    ...\\nelse:\\n    ...', True),
                    ('if x > 5 | else', False),
                ],
            },
            {
                'text': 'In C, what character ends most statements inside an if block?',
                'options': [
                    ('A newline', False),
                    ('Indentation', False),
                    ('A semicolon ;', True),
                    ('A comma ,', False),
                ],
            },
        ],
    },
    5: {  # Converting Loops
        'title': 'Loops Quiz',
        'questions': [
            {
                'text': 'What numbers does Python\'s range(1, 6) produce?',
                'options': [
                    ('1, 2, 3, 4, 5, 6', False),
                    ('1, 2, 3, 4, 5', True),
                    ('0, 1, 2, 3, 4, 5', False),
                    ('0, 1, 2, 3, 4', False),
                ],
            },
            {
                'text': 'Which C syntax correctly writes a for loop that counts from 0 to 4?',
                'options': [
                    ('for i in range(5):', False),
                    ('for (int i = 0; i < 5; i++)', True),
                    ('for (i = 0; i <= 4)', False),
                    ('loop i from 0 to 4', False),
                ],
            },
            {
                'text': 'What is the Python equivalent of a C for-loop when iterating over a range of numbers?',
                'options': [
                    ('A while loop', False),
                    ('A do-while loop', False),
                    ('A for loop using range()', True),
                    ('A foreach loop', False),
                ],
            },
        ],
    },
    6: {  # Converting Functions and Methods
        'title': 'Functions and Methods Quiz',
        'questions': [
            {
                'text': 'In Python, which keyword is used to define a function?',
                'options': [
                    ('function', False),
                    ('func', False),
                    ('def', True),
                    ('method', False),
                ],
            },
            {
                'text': 'In Java, where must all methods be defined?',
                'options': [
                    ('At the top of the file, before imports', False),
                    ('Inside a class', True),
                    ('Inside main() only', False),
                    ('In a separate module file', False),
                ],
            },
            {
                'text': 'In C, what must you specify immediately before a function\'s name?',
                'options': [
                    ('The function\'s purpose as a comment', False),
                    ('The return type', True),
                    ('The number of parameters', False),
                    ('The calling convention', False),
                ],
            },
        ],
    },
    7: {  # Learning Through CodeSwitch
        'title': 'Using CodeSwitch Quiz',
        'questions': [
            {
                'text': 'Which CodeSwitch feature lets you instantly see code in another language?',
                'options': [
                    ('The File Manager', False),
                    ('The Converter', True),
                    ('The Admin Panel', False),
                    ('The Dashboard', False),
                ],
            },
            {
                'text': 'Where can you save interesting conversions for future reference in CodeSwitch?',
                'options': [
                    ('Converter history only', False),
                    ('My Files', True),
                    ('The Learning module', False),
                    ('The Dashboard', False),
                ],
            },
            {
                'text': 'What is the best way to learn code conversion with CodeSwitch?',
                'options': [
                    ('Memorise every syntax rule before trying anything', False),
                    ('Experiment by converting and comparing code across languages', True),
                    ('Only read the documentation without running examples', False),
                    ('Avoid the Try It sandbox to reduce confusion', False),
                ],
            },
        ],
    },
    8: {  # Recommended Learning Path
        'title': 'Learning Path Quiz',
        'questions': [
            {
                'text': 'What is the recommended first step when starting the CodeSwitch learning path?',
                'options': [
                    ('Jump immediately to advanced modules', False),
                    ('Understand the key differences between C, Python, and Java', True),
                    ('Start with graph algorithms', False),
                    ('Write full programs from scratch in three languages at once', False),
                ],
            },
            {
                'text': 'After completing each lesson, what activity helps reinforce your learning?',
                'options': [
                    ('Reading the lesson a second time without doing anything else', False),
                    ('Using the Converter to try the examples yourself', True),
                    ('Skipping immediately to the next module', False),
                    ('Watching unrelated programming videos online', False),
                ],
            },
            {
                'text': 'What is the benefit of saving conversions to My Files?',
                'options': [
                    ('It unlocks access to advanced modules automatically', False),
                    ('It builds a personal reference library for future use', True),
                    ('It earns achievement points in the system', False),
                    ('It makes the converter run faster', False),
                ],
            },
        ],
    },

    # ── Module 2: Working with Strings ────────────────────────────────────
    10: {  # String Concatenation
        'title': 'String Concatenation Quiz',
        'questions': [
            {
                'text': 'In Python, which operator concatenates two strings?',
                'options': [
                    ('&', False),
                    ('.', False),
                    ('+', True),
                    ('*', False),
                ],
            },
            {
                'text': 'In C, which standard library function concatenates two character arrays?',
                'options': [
                    ('strcpy()', False),
                    ('strcat()', True),
                    ('strcmp()', False),
                    ('strlen()', False),
                ],
            },
            {
                'text': 'In Java, which StringBuilder method appends text to the end of the buffer?',
                'options': [
                    ('concat()', False),
                    ('add()', False),
                    ('append()', True),
                    ('join()', False),
                ],
            },
        ],
    },
    11: {  # String Length and Accessing Characters
        'title': 'String Length and Characters Quiz',
        'questions': [
            {
                'text': 'In Python, how do you find the length of a string s?',
                'options': [
                    ('s.size()', False),
                    ('s.length()', False),
                    ('len(s)', True),
                    ('s.count()', False),
                ],
            },
            {
                'text': 'In C, which function returns the number of characters in a string?',
                'options': [
                    ('sizeof()', False),
                    ('strlen()', True),
                    ('stringlen()', False),
                    ('length()', False),
                ],
            },
            {
                'text': 'In Python, how do you access the first character of a string s?',
                'options': [
                    ('s.first()', False),
                    ('s[1]', False),
                    ('s[0]', True),
                    ('s.char(0)', False),
                ],
            },
        ],
    },
    12: {  # Substrings and Slicing
        'title': 'Substrings and Slicing Quiz',
        'questions': [
            {
                'text': 'In Python, what does s[2:5] return?',
                'options': [
                    ('Characters at index 2 and index 5 only', False),
                    ('Characters from index 2 up to and including index 5', False),
                    ('Characters from index 2 up to but not including index 5', True),
                    ('Characters from index 2 to the end of the string', False),
                ],
            },
            {
                'text': 'In Java, which String method extracts a portion of a string?',
                'options': [
                    ('slice()', False),
                    ('substr()', False),
                    ('substring()', True),
                    ('mid()', False),
                ],
            },
            {
                'text': 'In C, which function copies a limited number of characters from one string to another?',
                'options': [
                    ('strslice()', False),
                    ('strncpy()', True),
                    ('strcopy()', False),
                    ('strsub()', False),
                ],
            },
        ],
    },
    13: {  # Searching in Strings
        'title': 'Searching in Strings Quiz',
        'questions': [
            {
                'text': 'In Python, which string method returns the index of the first occurrence of a substring (or -1 if not found)?',
                'options': [
                    ('search()', False),
                    ('index()', False),
                    ('find()', True),
                    ('locate()', False),
                ],
            },
            {
                'text': 'In C, which function searches for a substring within a string and returns a pointer to it?',
                'options': [
                    ('strsearch()', False),
                    ('strfind()', False),
                    ('strstr()', True),
                    ('strloc()', False),
                ],
            },
            {
                'text': 'In Java, which String method checks whether a string contains a given substring?',
                'options': [
                    ('has()', False),
                    ('includes()', False),
                    ('contains()', True),
                    ('search()', False),
                ],
            },
        ],
    },
    14: {  # String Formatting
        'title': 'String Formatting Quiz',
        'questions': [
            {
                'text': 'Which Python syntax correctly embeds a variable into a string using an f-string?',
                'options': [
                    ('"Hello {name}"', False),
                    ('f"Hello {name}"', True),
                    ('"Hello %name"', False),
                    ('"Hello" + name', False),
                ],
            },
            {
                'text': 'In C, which printf() format specifier is used to print a string?',
                'options': [
                    ('%d', False),
                    ('%c', False),
                    ('%s', True),
                    ('%f', False),
                ],
            },
            {
                'text': 'In Java, which method creates a formatted string using format specifiers like %s and %d?',
                'options': [
                    ('String.format()', True),
                    ('String.printf()', False),
                    ('String.formatString()', False),
                    ('text.format()', False),
                ],
            },
        ],
    },

    # ── Module 3: Data Structures ──────────────────────────────────────────
    16: {  # Adding and Removing Elements
        'title': 'Adding and Removing Elements Quiz',
        'questions': [
            {
                'text': 'In Python, which list method adds an element to the end of a list?',
                'options': [
                    ('add()', False),
                    ('insert()', False),
                    ('append()', True),
                    ('push()', False),
                ],
            },
            {
                'text': 'In Python, which list method removes and returns the last element?',
                'options': [
                    ('remove()', False),
                    ('delete()', False),
                    ('pop()', True),
                    ('drop()', False),
                ],
            },
            {
                'text': 'In Java, which ArrayList method adds an element to the collection?',
                'options': [
                    ('insert()', False),
                    ('append()', False),
                    ('add()', True),
                    ('push()', False),
                ],
            },
        ],
    },
    17: {  # 2D Arrays and Matrices
        'title': '2D Arrays and Matrices Quiz',
        'questions': [
            {
                'text': 'In Python, how do you access the element in the second row, third column of a 2D list called grid?',
                'options': [
                    ('grid[2][3]', False),
                    ('grid[1][2]', True),
                    ('grid(2, 3)', False),
                    ('grid.get(1, 2)', False),
                ],
            },
            {
                'text': 'In C, how do you declare a 2D integer array with 3 rows and 4 columns?',
                'options': [
                    ('int arr[][] = new int[3][4];', False),
                    ('int arr[3][4];', True),
                    ('int[3][4] arr;', False),
                    ('int arr = new int[3, 4];', False),
                ],
            },
            {
                'text': 'In Java, what is the correct way to create a 2D int array with 3 rows and 4 columns?',
                'options': [
                    ('int arr[3][4];', False),
                    ('int[][] arr = new int[3][4];', True),
                    ('int[3,4] arr = new int[][];', False),
                    ('int arr = int[3][4];', False),
                ],
            },
        ],
    },
    18: {  # Linear Search
        'title': 'Linear Search Quiz',
        'questions': [
            {
                'text': 'What is the worst-case time complexity of linear search?',
                'options': [
                    ('O(1)', False),
                    ('O(log n)', False),
                    ('O(n)', True),
                    ('O(n²)', False),
                ],
            },
            {
                'text': 'When is linear search preferred over binary search?',
                'options': [
                    ('When the array is very large and sorted', False),
                    ('When the array is unsorted or small', True),
                    ('When maximum performance is required', False),
                    ('When all elements are unique', False),
                ],
            },
            {
                'text': 'How does linear search find an element?',
                'options': [
                    ('It divides the array in half each step', False),
                    ('It checks each element one by one from the start', True),
                    ('It starts from the middle of the array', False),
                    ('It sorts the array first, then searches', False),
                ],
            },
        ],
    },
    19: {  # Bubble Sort
        'title': 'Bubble Sort Quiz',
        'questions': [
            {
                'text': 'What is the worst-case time complexity of Bubble Sort?',
                'options': [
                    ('O(n)', False),
                    ('O(n log n)', False),
                    ('O(n²)', True),
                    ('O(log n)', False),
                ],
            },
            {
                'text': 'How does Bubble Sort work?',
                'options': [
                    ('It selects the minimum element and places it first', False),
                    ('It repeatedly swaps adjacent elements that are in the wrong order', True),
                    ('It divides the array recursively into halves', False),
                    ('It inserts each element into a sorted portion', False),
                ],
            },
            {
                'text': 'Is Bubble Sort efficient for sorting large datasets?',
                'options': [
                    ('Yes, it runs in O(n log n) time', False),
                    ('No, it is one of the slowest algorithms for large data', True),
                    ('Yes, because it uses no extra memory at all', False),
                    ('Only when the data contains duplicate values', False),
                ],
            },
        ],
    },

    # ── Module 4: Object-Oriented Programming ─────────────────────────────
    21: {  # Methods and Behaviour
        'title': 'Methods and Behaviour Quiz',
        'questions': [
            {
                'text': 'In Python, what is the conventional name for the first parameter of an instance method?',
                'options': [
                    ('this', False),
                    ('me', False),
                    ('self', True),
                    ('instance', False),
                ],
            },
            {
                'text': 'In Java, which keyword refers to the current object instance inside a method?',
                'options': [
                    ('self', False),
                    ('current', False),
                    ('this', True),
                    ('me', False),
                ],
            },
            {
                'text': 'What is the purpose of a method defined inside a class?',
                'options': [
                    ('To store data as attributes only', False),
                    ('To define behaviour that objects of the class can perform', True),
                    ('To create new classes at runtime', False),
                    ('To import external libraries into the class', False),
                ],
            },
        ],
    },
    22: {  # Inheritance
        'title': 'Inheritance Quiz',
        'questions': [
            {
                'text': 'In Python, how do you define a class Child that inherits from Parent?',
                'options': [
                    ('class Child inherits Parent:', False),
                    ('class Child extends Parent:', False),
                    ('class Child(Parent):', True),
                    ('class Child -> Parent:', False),
                ],
            },
            {
                'text': 'In Java, which keyword makes one class inherit from another?',
                'options': [
                    ('implements', False),
                    ('inherits', False),
                    ('extends', True),
                    ('derives', False),
                ],
            },
            {
                'text': 'What does inheritance allow a subclass to do?',
                'options': [
                    ('Access only the private fields of the parent class', False),
                    ('Reuse and extend the functionality of the parent class', True),
                    ('Completely replace the parent class in memory', False),
                    ('Compile faster than standalone classes', False),
                ],
            },
        ],
    },
    23: {  # Encapsulation
        'title': 'Encapsulation Quiz',
        'questions': [
            {
                'text': 'What is encapsulation in object-oriented programming?',
                'options': [
                    ('The ability to inherit from multiple classes simultaneously', False),
                    ('Hiding internal details and exposing only what is necessary', True),
                    ('The process of converting code to a different language', False),
                    ('Creating multiple instances of the same class', False),
                ],
            },
            {
                'text': 'In Java, which access modifier restricts a field so only the declaring class can access it?',
                'options': [
                    ('public', False),
                    ('protected', False),
                    ('private', True),
                    ('internal', False),
                ],
            },
            {
                'text': 'What are getter and setter methods used for?',
                'options': [
                    ('To delete object attributes permanently', False),
                    ('To provide controlled access to private fields', True),
                    ('To override methods inherited from a parent class', False),
                    ('To import other classes into the current file', False),
                ],
            },
        ],
    },

    # ── Module 5: Error Handling and File I/O ─────────────────────────────
    25: {  # Try / Catch / Except
        'title': 'Try / Catch / Except Quiz',
        'questions': [
            {
                'text': 'In Python, which keyword begins a block that handles an exception?',
                'options': [
                    ('catch', False),
                    ('except', True),
                    ('error', False),
                    ('rescue', False),
                ],
            },
            {
                'text': 'In Java, which block catches exceptions thrown inside a try block?',
                'options': [
                    ('except', False),
                    ('catch', True),
                    ('handle', False),
                    ('rescue', False),
                ],
            },
            {
                'text': 'What is the purpose of the try block?',
                'options': [
                    ('To define functions that are allowed to throw errors', False),
                    ('To wrap code that might raise or throw an exception', True),
                    ('To suppress and log all error messages silently', False),
                    ('To skip code that contains known errors', False),
                ],
            },
        ],
    },
    26: {  # Throwing and Raising Exceptions
        'title': 'Throwing and Raising Exceptions Quiz',
        'questions': [
            {
                'text': 'In Python, which keyword manually triggers an exception?',
                'options': [
                    ('throw', False),
                    ('raise', True),
                    ('error', False),
                    ('trigger', False),
                ],
            },
            {
                'text': 'In Java, which keyword is used to throw an exception from a method?',
                'options': [
                    ('raise', False),
                    ('throw', True),
                    ('error', False),
                    ('trigger', False),
                ],
            },
            {
                'text': 'Why would you deliberately raise or throw an exception in code?',
                'options': [
                    ('To crash the program intentionally for testing', False),
                    ('To signal that an unexpected or invalid condition has occurred', True),
                    ('To skip the finally block in a try statement', False),
                    ('To improve the performance of the program', False),
                ],
            },
        ],
    },
    27: {  # Reading from Files
        'title': 'Reading from Files Quiz',
        'questions': [
            {
                'text': 'In Python, which built-in function opens a file for reading or writing?',
                'options': [
                    ('read()', False),
                    ('file()', False),
                    ('open()', True),
                    ('load()', False),
                ],
            },
            {
                'text': 'In Python, which mode string passed to open() opens a file for reading?',
                'options': [
                    ('"w"', False),
                    ('"a"', False),
                    ('"r"', True),
                    ('"x"', False),
                ],
            },
            {
                'text': 'In Java, which combination of classes is commonly used to read text from a file line by line?',
                'options': [
                    ('FileReader and BufferedReader', True),
                    ('FileWriter and PrintWriter', False),
                    ('OutputStream and DataInputStream', False),
                    ('Scanner and FileOutputStream', False),
                ],
            },
        ],
    },
    28: {  # Writing to Files
        'title': 'Writing to Files Quiz',
        'questions': [
            {
                'text': 'In Python, which open() mode overwrites a file with new content?',
                'options': [
                    ('"r"', False),
                    ('"a"', False),
                    ('"w"', True),
                    ('"x"', False),
                ],
            },
            {
                'text': 'In Python, which open() mode appends content to a file without erasing it?',
                'options': [
                    ('"w"', False),
                    ('"r"', False),
                    ('"a"', True),
                    ('"rw"', False),
                ],
            },
            {
                'text': 'In Java, which classes are commonly used to write text to a file?',
                'options': [
                    ('FileReader or BufferedReader', False),
                    ('InputStream and DataReader', False),
                    ('FileWriter or PrintWriter', True),
                    ('BufferedReader and Scanner', False),
                ],
            },
        ],
    },

    # ── Module 6: Algorithms and Recursion ────────────────────────────────
    30: {  # Recursive Factorial
        'title': 'Recursive Factorial Quiz',
        'questions': [
            {
                'text': 'What is the base case in a recursive factorial function?',
                'options': [
                    ('factorial(n) when n equals 10', False),
                    ('factorial(0) = 1 (or factorial(1) = 1)', True),
                    ('factorial(n) = n * factorial(n)', False),
                    ('factorial(n) when n is an even number', False),
                ],
            },
            {
                'text': 'What does factorial(5) equal?',
                'options': [
                    ('15', False),
                    ('25', False),
                    ('120', True),
                    ('100', False),
                ],
            },
            {
                'text': 'What is the correct recursive case for the factorial function?',
                'options': [
                    ('return 1', False),
                    ('return n * factorial(n - 1)', True),
                    ('return n + factorial(n - 1)', False),
                    ('return factorial(n + 1) / n', False),
                ],
            },
        ],
    },
    31: {  # Recursive Fibonacci
        'title': 'Recursive Fibonacci Quiz',
        'questions': [
            {
                'text': 'What are the base cases for the recursive Fibonacci function?',
                'options': [
                    ('fib(0) = 0 and fib(1) = 1', True),
                    ('fib(0) = 1 and fib(1) = 1', False),
                    ('fib(1) = 0 and fib(2) = 2', False),
                    ('fib(0) = 0 is the only base case', False),
                ],
            },
            {
                'text': 'What is fib(6) using the standard Fibonacci sequence (fib(0)=0, fib(1)=1)?',
                'options': [
                    ('5', False),
                    ('8', True),
                    ('13', False),
                    ('3', False),
                ],
            },
            {
                'text': 'Why is naive recursive Fibonacci inefficient for large inputs?',
                'options': [
                    ('It uses too many local variables', False),
                    ('It recomputes the same subproblems many times', True),
                    ('It only works correctly for small numbers', False),
                    ('It requires floating-point arithmetic', False),
                ],
            },
        ],
    },
    32: {  # Binary Search
        'title': 'Binary Search Quiz',
        'questions': [
            {
                'text': 'What precondition must be met for binary search to work correctly?',
                'options': [
                    ('The array must contain only integers', False),
                    ('The array must be sorted', True),
                    ('The array must have an even number of elements', False),
                    ('The array must be stored in a hash map', False),
                ],
            },
            {
                'text': 'What is the time complexity of binary search?',
                'options': [
                    ('O(n)', False),
                    ('O(n²)', False),
                    ('O(log n)', True),
                    ('O(1)', False),
                ],
            },
            {
                'text': 'How does binary search decide which half of the array to continue searching?',
                'options': [
                    ('By comparing the target to the middle element', True),
                    ('By randomly selecting a half each time', False),
                    ('By counting how many elements are in each half', False),
                    ('By sorting each half independently first', False),
                ],
            },
        ],
    },
    33: {  # Selection Sort
        'title': 'Selection Sort Quiz',
        'questions': [
            {
                'text': 'How does Selection Sort work?',
                'options': [
                    ('It inserts each element into its correct position in a sorted portion', False),
                    ('It finds the minimum element and moves it to the front, repeating for the rest', True),
                    ('It divides the array recursively into smaller halves', False),
                    ('It repeatedly swaps adjacent elements that are out of order', False),
                ],
            },
            {
                'text': 'What is the time complexity of Selection Sort?',
                'options': [
                    ('O(n)', False),
                    ('O(n log n)', False),
                    ('O(n²)', True),
                    ('O(log n)', False),
                ],
            },
            {
                'text': 'Is Selection Sort a stable sorting algorithm?',
                'options': [
                    ('Yes, it always preserves the relative order of equal elements', False),
                    ('No, it may change the relative order of equal elements', True),
                    ('Only when sorting integer arrays', False),
                    ('Only in Python implementations', False),
                ],
            },
        ],
    },
    34: {  # Recursion vs Loops
        'title': 'Recursion vs Loops Quiz',
        'questions': [
            {
                'text': 'When is recursion typically preferred over an iterative loop?',
                'options': [
                    ('When the problem has no base case', False),
                    ('When the problem has a naturally recursive structure, such as tree traversal', True),
                    ('When raw performance is the only consideration', False),
                    ('When the language does not support loops', False),
                ],
            },
            {
                'text': 'What is a potential risk of deep recursion?',
                'options': [
                    ('It always produces incorrect answers', False),
                    ('It can cause a stack overflow due to too many nested calls', True),
                    ('It always runs slower than an equivalent loop', False),
                    ('It requires more local variables than loops', False),
                ],
            },
            {
                'text': 'What is tail recursion?',
                'options': [
                    ('Recursion with no base case', False),
                    ('A recursive call that is the very last operation in a function', True),
                    ('Recursion that starts from the last element of a list', False),
                    ('A loop embedded inside a recursive function', False),
                ],
            },
        ],
    },

    # ── Module 7: Advanced Sorting Algorithms ─────────────────────────────
    36: {  # Merge Sort
        'title': 'Merge Sort Quiz',
        'questions': [
            {
                'text': 'What is the time complexity of Merge Sort in all cases?',
                'options': [
                    ('O(n²)', False),
                    ('O(n)', False),
                    ('O(n log n)', True),
                    ('O(log n)', False),
                ],
            },
            {
                'text': 'Merge Sort is an example of which algorithmic strategy?',
                'options': [
                    ('Greedy algorithm', False),
                    ('Dynamic programming', False),
                    ('Divide and conquer', True),
                    ('Backtracking', False),
                ],
            },
            {
                'text': 'Is Merge Sort a stable sorting algorithm?',
                'options': [
                    ('No, it reorders equal elements', False),
                    ('Only for arrays of even length', False),
                    ('Yes, it preserves the relative order of equal elements', True),
                    ('Only when sorting strings', False),
                ],
            },
        ],
    },
    37: {  # Quick Sort
        'title': 'Quick Sort Quiz',
        'questions': [
            {
                'text': 'How does Quick Sort sort an array?',
                'options': [
                    ('By repeatedly merging sorted halves', False),
                    ('By choosing a pivot and partitioning elements around it', True),
                    ('By inserting each element into a sorted portion', False),
                    ('By finding the minimum and placing it at the front', False),
                ],
            },
            {
                'text': 'What is the worst-case time complexity of Quick Sort?',
                'options': [
                    ('O(n log n)', False),
                    ('O(n)', False),
                    ('O(n²)', True),
                    ('O(log n)', False),
                ],
            },
            {
                'text': 'When does Quick Sort perform at its worst?',
                'options': [
                    ('When the array has an odd number of elements', False),
                    ('When the pivot consistently produces highly unbalanced partitions', True),
                    ('When all elements in the array are distinct', False),
                    ('When the array has fewer than ten elements', False),
                ],
            },
        ],
    },
    38: {  # Comparing Sorting Algorithms
        'title': 'Comparing Sorting Algorithms Quiz',
        'questions': [
            {
                'text': 'Which sorting algorithm guarantees O(n log n) performance even in the worst case?',
                'options': [
                    ('Bubble Sort', False),
                    ('Quick Sort', False),
                    ('Merge Sort', True),
                    ('Insertion Sort', False),
                ],
            },
            {
                'text': 'For a small or nearly-sorted array, which algorithm is most efficient in practice?',
                'options': [
                    ('Merge Sort', False),
                    ('Quick Sort', False),
                    ('Insertion Sort', True),
                    ('Selection Sort', False),
                ],
            },
            {
                'text': 'Which sorting algorithm requires O(n) additional memory for the merge step?',
                'options': [
                    ('Quick Sort', False),
                    ('Bubble Sort', False),
                    ('Merge Sort', True),
                    ('Insertion Sort', False),
                ],
            },
        ],
    },

    # ── Module 8: Dynamic Programming ─────────────────────────────────────
    40: {  # Memoization — Fibonacci Revisited
        'title': 'Memoization Quiz',
        'questions': [
            {
                'text': 'What problem does memoization solve in the recursive Fibonacci calculation?',
                'options': [
                    ('Stack overflow errors on deep recursion', False),
                    ('Recomputing the same subproblem results multiple times', True),
                    ('Incorrect results for very large Fibonacci numbers', False),
                    ('Memory allocation failures on the heap', False),
                ],
            },
            {
                'text': 'Where does memoization store previously computed values?',
                'options': [
                    ('In a database table', False),
                    ('In a cache such as a dictionary or array', True),
                    ('In a file on disk', False),
                    ('In a separate background process', False),
                ],
            },
            {
                'text': 'What is the time complexity of computing Fibonacci with memoization?',
                'options': [
                    ('O(2ⁿ)', False),
                    ('O(n²)', False),
                    ('O(n)', True),
                    ('O(log n)', False),
                ],
            },
        ],
    },
    41: {  # Coin Change — Minimum Coins
        'title': 'Coin Change Quiz',
        'questions': [
            {
                'text': 'How does dynamic programming approach the minimum coin change problem?',
                'options': [
                    ('Try all possible combinations and pick the shortest', False),
                    ('Build up the optimal solution from smaller subproblems', True),
                    ('Always use a greedy approach, taking the largest coin first', False),
                    ('Apply binary search on the sorted list of coin values', False),
                ],
            },
            {
                'text': 'What does the DP table represent in the minimum coin change problem?',
                'options': [
                    ('The total number of available coin denominations', False),
                    ('The minimum number of coins needed to make each amount', True),
                    ('The total monetary value of coins used', False),
                    ('The largest coin denomination used for each amount', False),
                ],
            },
            {
                'text': 'Why does a greedy approach not always solve the coin change problem optimally?',
                'options': [
                    ('Greedy algorithms are too slow for this problem', False),
                    ('A locally optimal (greedy) choice may not lead to a globally optimal solution', True),
                    ('Greedy algorithms only work with sorted coin arrays', False),
                    ('Greedy algorithms always require memoization to be correct', False),
                ],
            },
        ],
    },
    42: {  # Longest Common Subsequence
        'title': 'Longest Common Subsequence Quiz',
        'questions': [
            {
                'text': 'What is a subsequence of a sequence?',
                'options': [
                    ('A contiguous portion of the sequence (a subarray)', False),
                    ('Elements that appear in the same relative order but not necessarily contiguously', True),
                    ('The reversed version of the sequence', False),
                    ('The shortest possible sequence within a sequence', False),
                ],
            },
            {
                'text': 'What is the length of the LCS of "ABCBDAB" and "BDCAB"?',
                'options': [
                    ('2', False),
                    ('3', False),
                    ('4', True),
                    ('7', False),
                ],
            },
            {
                'text': 'What is the time complexity of the DP solution for LCS?',
                'options': [
                    ('O(n)', False),
                    ('O(n log n)', False),
                    ('O(m × n), where m and n are the lengths of the two sequences', True),
                    ('O(n²) only when the sequences are equal length', False),
                ],
            },
        ],
    },
    43: {  # 0/1 Knapsack
        'title': '0/1 Knapsack Quiz',
        'questions': [
            {
                'text': 'In the 0/1 Knapsack problem, what does "0/1" mean?',
                'options': [
                    ('Items can be taken in any fractional amount', False),
                    ('Each item is either fully included or completely excluded', True),
                    ('Only items with value 0 or 1 are considered', False),
                    ('The knapsack can hold exactly 0 or 1 item', False),
                ],
            },
            {
                'text': 'What does each cell in the 0/1 Knapsack DP table represent?',
                'options': [
                    ('The maximum total weight of items taken', False),
                    ('The maximum value achievable given a capacity and the first i items', True),
                    ('The list of items currently in the knapsack', False),
                    ('The minimum number of items needed to fill the knapsack', False),
                ],
            },
            {
                'text': 'What is the time complexity of the 0/1 Knapsack DP solution?',
                'options': [
                    ('O(n)', False),
                    ('O(n log n)', False),
                    ('O(n × W), where n is the number of items and W is the capacity', True),
                    ('O(2ⁿ) like brute-force enumeration', False),
                ],
            },
        ],
    },

    # ── Module 9: Graph Algorithms ─────────────────────────────────────────
    45: {  # Representing Graphs
        'title': 'Representing Graphs Quiz',
        'questions': [
            {
                'text': 'What are the two most common ways to represent a graph in code?',
                'options': [
                    ('Array and linked list', False),
                    ('Adjacency matrix and adjacency list', True),
                    ('Hash table and stack', False),
                    ('Binary tree and heap', False),
                ],
            },
            {
                'text': 'Which graph representation is more memory-efficient for sparse graphs?',
                'options': [
                    ('Adjacency matrix', False),
                    ('Adjacency list', True),
                    ('Both use the same amount of memory', False),
                    ('Neither is memory-efficient for sparse graphs', False),
                ],
            },
            {
                'text': 'In an adjacency matrix, what does a value of 1 at position [i][j] typically indicate?',
                'options': [
                    ('There is no edge between vertex i and vertex j', False),
                    ('There is an edge between vertex i and vertex j', True),
                    ('Vertex i has the value j assigned to it', False),
                    ('The graph contains exactly j edges in total', False),
                ],
            },
        ],
    },
    46: {  # Breadth-First Search (BFS)
        'title': 'Breadth-First Search Quiz',
        'questions': [
            {
                'text': 'Which data structure does BFS use to track nodes waiting to be visited?',
                'options': [
                    ('Stack', False),
                    ('Queue', True),
                    ('Heap', False),
                    ('Binary tree', False),
                ],
            },
            {
                'text': 'In what order does BFS explore a graph?',
                'options': [
                    ('Deepest nodes first, then backtracking', False),
                    ('Level by level, visiting all neighbours before going deeper', True),
                    ('In a random order determined at runtime', False),
                    ('In ascending order of node values', False),
                ],
            },
            {
                'text': 'What is BFS most commonly used for?',
                'options': [
                    ('Sorting elements stored in a graph', False),
                    ('Finding the shortest path in an unweighted graph', True),
                    ('Detecting negative-weight cycles', False),
                    ('Computing minimum spanning trees directly', False),
                ],
            },
        ],
    },
    47: {  # Depth-First Search (DFS)
        'title': 'Depth-First Search Quiz',
        'questions': [
            {
                'text': 'Which data structure does an iterative DFS implementation use?',
                'options': [
                    ('Queue', False),
                    ('Stack', True),
                    ('Heap', False),
                    ('Circular linked list', False),
                ],
            },
            {
                'text': 'How does DFS explore a graph?',
                'options': [
                    ('By visiting all immediate neighbours before going deeper', False),
                    ('By going as deep as possible along each branch before backtracking', True),
                    ('By visiting nodes in sorted numerical order', False),
                    ('By always starting from the node with the most edges', False),
                ],
            },
            {
                'text': 'Which graph traversal is typically used to detect cycles within a graph?',
                'options': [
                    ('BFS', False),
                    ('DFS', True),
                    ('Binary search', False),
                    ('Bubble sort', False),
                ],
            },
        ],
    },
    48: {  # Dijkstra's Shortest Path
        'title': "Dijkstra's Algorithm Quiz",
        'questions': [
            {
                'text': "What type of graph is Dijkstra's algorithm designed for?",
                'options': [
                    ('Unweighted graphs only', False),
                    ('Weighted graphs with non-negative edge weights', True),
                    ('Graphs that may contain negative edge weights', False),
                    ('Trees only — it does not work on general graphs', False),
                ],
            },
            {
                'text': "Which data structure is used to optimise Dijkstra's algorithm?",
                'options': [
                    ('Stack', False),
                    ('Regular queue', False),
                    ('Priority queue (min-heap)', True),
                    ('Adjacency matrix only', False),
                ],
            },
            {
                'text': "What does Dijkstra's algorithm compute?",
                'options': [
                    ('The minimum spanning tree of the graph', False),
                    ('The topological ordering of all nodes', False),
                    ('The shortest path from a source node to every other node', True),
                    ('The longest path in the graph', False),
                ],
            },
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed quizzes for all lessons that do not yet have one (pages 2+ of every module)'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        missing = 0

        for lesson_id, quiz_def in QUIZ_DATA.items():
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  Lesson {lesson_id} not found, skipping.')
                )
                missing += 1
                continue

            if hasattr(lesson, 'quiz'):
                self.stdout.write(
                    f'  Quiz for lesson {lesson_id} ("{lesson.title}") already exists, skipping.'
                )
                skipped += 1
                continue

            quiz = Quiz.objects.create(
                lesson=lesson,
                title=quiz_def['title'],
                passing_score=70,
            )
            for i, q_data in enumerate(quiz_def['questions'], 1):
                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    question_text=q_data['text'],
                    order=i,
                )
                for opt_text, is_correct in q_data['options']:
                    QuizOption.objects.create(
                        question=question,
                        option_text=opt_text,
                        is_correct=is_correct,
                    )
            created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Created quiz for lesson {lesson_id} ("{lesson.title}"): {quiz_def["title"]}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created: {created}, Skipped: {skipped}, Not found: {missing}'
            )
        )
