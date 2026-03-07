"""
Management command: seed_quizzes
Seeds 3 questions per lesson for each module's first lesson.
"""
from django.core.management.base import BaseCommand
from learning.models import Lesson, Quiz, QuizQuestion, QuizOption

QUIZ_DATA = {
    1: {  # Lesson: Understanding Code Conversion
        'title': 'Code Conversion Basics',
        'questions': [
            {
                'text': 'What does CodeSwitch use to translate code between languages?',
                'options': [
                    ('A compiler that runs the code', False),
                    ('Rule-based patterns and AI assistance', True),
                    ('Copy-paste from the internet', False),
                    ('A human translator', False),
                ],
            },
            {
                'text': 'Which of these is a benefit of automated code conversion?',
                'options': [
                    ('It always produces perfect code with no errors', False),
                    ('It can speed up porting code to a new language', True),
                    ('It replaces the need to understand the target language', False),
                    ('It only works for Python to C', False),
                ],
            },
            {
                'text': 'What should you do after receiving converted code?',
                'options': [
                    ('Use it immediately without checking', False),
                    ('Review and test it to make sure it is correct', True),
                    ('Delete it as it will never work', False),
                    ('Only use it if the engine badge says AI', False),
                ],
            },
        ],
    },
    9: {  # Lesson: Declaring and Using Strings
        'title': 'Strings Quiz',
        'questions': [
            {
                'text': 'How do you declare a string variable in Python?',
                'options': [
                    ('char name[] = "Alice";', False),
                    ('String name = "Alice";', False),
                    ('name = "Alice"', True),
                    ('var name = "Alice"', False),
                ],
            },
            {
                'text': 'In C, what data type is used to store a sequence of characters?',
                'options': [
                    ('string', False),
                    ('char[]', True),
                    ('text', False),
                    ('varchar', False),
                ],
            },
            {
                'text': 'Which Java class represents a string of characters?',
                'options': [
                    ('Text', False),
                    ('char', False),
                    ('String', True),
                    ('StringBuffer only', False),
                ],
            },
        ],
    },
    15: {  # Lesson: Arrays and Lists
        'title': 'Arrays and Lists Quiz',
        'questions': [
            {
                'text': 'In Python, which built-in type is used as a dynamic array?',
                'options': [
                    ('tuple', False),
                    ('list', True),
                    ('dict', False),
                    ('set', False),
                ],
            },
            {
                'text': 'In C, arrays have a size that is:',
                'options': [
                    ('Dynamic at runtime', False),
                    ('Fixed at declaration time', True),
                    ('Unlimited', False),
                    ('Determined by the OS', False),
                ],
            },
            {
                'text': 'What is the index of the first element in most languages?',
                'options': [
                    ('1', False),
                    ('0', True),
                    ('-1', False),
                    ('It depends on the language', False),
                ],
            },
        ],
    },
    20: {  # Lesson: Classes and Objects
        'title': 'OOP Basics Quiz',
        'questions': [
            {
                'text': 'What keyword is used to define a class in Python?',
                'options': [
                    ('class', True),
                    ('def', False),
                    ('object', False),
                    ('type', False),
                ],
            },
            {
                'text': 'In Python, what is the name of the constructor method?',
                'options': [
                    ('constructor()', False),
                    ('new()', False),
                    ('__init__()', True),
                    ('create()', False),
                ],
            },
            {
                'text': 'In Java, which keyword is used to create an instance of a class?',
                'options': [
                    ('create', False),
                    ('new', True),
                    ('make', False),
                    ('object', False),
                ],
            },
        ],
    },
    24: {  # Lesson: Error Handling Approaches
        'title': 'Error Handling Quiz',
        'questions': [
            {
                'text': 'In Python, which block is used to catch exceptions?',
                'options': [
                    ('catch', False),
                    ('except', True),
                    ('error', False),
                    ('handle', False),
                ],
            },
            {
                'text': 'In Java and C++, which keyword starts an error-catching block?',
                'options': [
                    ('except', False),
                    ('catch', True),
                    ('rescue', False),
                    ('trap', False),
                ],
            },
            {
                'text': 'What does the "finally" block do in try/catch/finally?',
                'options': [
                    ('It runs only when an exception occurs', False),
                    ('It runs only when no exception occurs', False),
                    ('It always runs regardless of exceptions', True),
                    ('It suppresses all exceptions', False),
                ],
            },
        ],
    },
    29: {  # Lesson: What is Recursion?
        'title': 'Recursion Fundamentals Quiz',
        'questions': [
            {
                'text': 'What is recursion?',
                'options': [
                    ('A loop that runs forever', False),
                    ('A function that calls itself', True),
                    ('A type of sorting algorithm', False),
                    ('A data structure', False),
                ],
            },
            {
                'text': 'What is the base case in recursion?',
                'options': [
                    ('The first call to the function', False),
                    ('The condition that stops the recursion', True),
                    ('The recursive call inside the function', False),
                    ('The return type of the function', False),
                ],
            },
            {
                'text': 'What happens if a recursive function has no base case?',
                'options': [
                    ('It returns None automatically', False),
                    ('It runs faster than a loop', False),
                    ('It results in a stack overflow / infinite recursion', True),
                    ('Nothing — it just stops on its own', False),
                ],
            },
        ],
    },
    35: {  # Lesson: Insertion Sort
        'title': 'Insertion Sort Quiz',
        'questions': [
            {
                'text': 'What is the average time complexity of Insertion Sort?',
                'options': [
                    ('O(n log n)', False),
                    ('O(n²)', True),
                    ('O(n)', False),
                    ('O(log n)', False),
                ],
            },
            {
                'text': 'Insertion sort works best when:',
                'options': [
                    ('The array is very large and unsorted', False),
                    ('The array is small or nearly sorted', True),
                    ('You need guaranteed O(n log n) performance', False),
                    ('Memory is extremely limited', False),
                ],
            },
            {
                'text': 'Is Insertion Sort a stable sorting algorithm?',
                'options': [
                    ('No, it swaps equal elements', False),
                    ('Yes, it preserves the relative order of equal elements', True),
                    ('Only when sorting strings', False),
                    ('Only in Python', False),
                ],
            },
        ],
    },
    39: {  # Lesson: What is Dynamic Programming?
        'title': 'Dynamic Programming Quiz',
        'questions': [
            {
                'text': 'What is the key idea behind dynamic programming?',
                'options': [
                    ('Solving problems with recursion only', False),
                    ('Storing solutions to subproblems to avoid recomputation', True),
                    ('Running code in parallel threads', False),
                    ('Using dynamic memory allocation', False),
                ],
            },
            {
                'text': 'Which classic problem is commonly solved with DP?',
                'options': [
                    ('Binary search', False),
                    ('Fibonacci numbers / Knapsack problem', True),
                    ('Bubble sort', False),
                    ('Linear search', False),
                ],
            },
            {
                'text': 'What is "memoization"?',
                'options': [
                    ('A way to manage memory in C', False),
                    ('Caching the result of expensive function calls', True),
                    ('A type of sorting algorithm', False),
                    ('Writing code comments', False),
                ],
            },
        ],
    },
    44: {  # Lesson: What are Graphs?
        'title': 'Graph Theory Basics Quiz',
        'questions': [
            {
                'text': 'A graph consists of:',
                'options': [
                    ('Only edges', False),
                    ('Vertices (nodes) and edges', True),
                    ('Only vertices', False),
                    ('Arrays and pointers', False),
                ],
            },
            {
                'text': 'In a directed graph, edges are:',
                'options': [
                    ('Bidirectional', False),
                    ('Unidirectional (one-way)', True),
                    ('Always weighted', False),
                    ('The same as in an undirected graph', False),
                ],
            },
            {
                'text': 'Which traversal algorithm explores as far as possible along each branch before backtracking?',
                'options': [
                    ('Breadth-First Search (BFS)', False),
                    ('Depth-First Search (DFS)', True),
                    ('Dijkstra\'s algorithm', False),
                    ('Insertion sort', False),
                ],
            },
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed quizzes for the first lesson of each learning module'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for lesson_id, quiz_def in QUIZ_DATA.items():
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Lesson {lesson_id} not found, skipping.'))
                continue

            if hasattr(lesson, 'quiz'):
                self.stdout.write(f'  Quiz for lesson {lesson_id} already exists, skipping.')
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
            self.stdout.write(self.style.SUCCESS(f'  Created quiz for lesson {lesson_id}: {quiz_def["title"]}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Created: {created}, Skipped: {skipped}'))
