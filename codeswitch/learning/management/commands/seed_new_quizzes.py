"""
Management command: seed_new_quizzes
Seeds 3 questions per lesson for the 4 new modules:
  - Pointers & Memory Management
  - Linked Lists
  - Stacks & Queues
  - Hash Tables & Dictionaries

Looks up lessons by (module title, lesson title) so it works regardless of IDs.
"""
from django.core.management.base import BaseCommand
from learning.models import Lesson, LearningModule, Quiz, QuizQuestion, QuizOption

# Structure: { module_title: { lesson_title: { title, questions: [(text, [(option, is_correct)])] } } }
QUIZ_DATA = {
    # ── Module 10: Pointers & Memory Management ───────────────────────────────
    'Pointers & Memory Management': {
        'What is a Pointer?': {
            'title': 'Pointer Basics Quiz',
            'questions': [
                {
                    'text': 'What does the & operator do in C?',
                    'options': [
                        ('Dereferences a pointer to get its value', False),
                        ('Returns the memory address of a variable', True),
                        ('Allocates memory on the heap', False),
                        ('Compares two values bitwise', False),
                    ],
                },
                {
                    'text': 'Given int x = 5; int *p = &x; what does *p refer to?',
                    'options': [
                        ('The address of x', False),
                        ('The value of p itself', False),
                        ('The value stored at x, i.e., 5', True),
                        ('A new copy of x', False),
                    ],
                },
                {
                    'text': 'How do Python variables differ from C pointers?',
                    'options': [
                        ('Python variables store raw memory addresses, just like C', False),
                        ('Python variables are high-level references managed by the runtime, with no manual address arithmetic', True),
                        ('Python has no concept of references at all', False),
                        ('Python uses the * operator to dereference references', False),
                    ],
                },
            ],
        },
        'Pointer Arithmetic': {
            'title': 'Pointer Arithmetic Quiz',
            'questions': [
                {
                    'text': 'If int *p points to arr[0] and sizeof(int) is 4, where does p+1 point?',
                    'options': [
                        ('1 byte ahead of arr[0]', False),
                        ('arr[1] (4 bytes ahead)', True),
                        ('arr[4]', False),
                        ('It is undefined behaviour', False),
                    ],
                },
                {
                    'text': 'Which expression is equivalent to arr[i] in C?',
                    'options': [
                        ('&(arr + i)', False),
                        ('*(arr + i)', True),
                        ('arr + i', False),
                        ('*arr[i]', False),
                    ],
                },
                {
                    'text': 'Can you perform pointer arithmetic in Python or Java?',
                    'options': [
                        ('Yes, using the + operator on references', False),
                        ('Yes, but only for array types', False),
                        ('No — neither language exposes raw memory addresses', True),
                        ('Only in Java with the Unsafe class', False),
                    ],
                },
            ],
        },
        'Pointers and Arrays': {
            'title': 'Pointers and Arrays Quiz',
            'questions': [
                {
                    'text': 'When you pass an array to a function in C, what is actually passed?',
                    'options': [
                        ('A full copy of the array', False),
                        ('A pointer to the first element (pointer decay)', True),
                        ('The size of the array', False),
                        ('A reference counted wrapper', False),
                    ],
                },
                {
                    'text': 'Why must you pass the array length as a separate parameter in C?',
                    'options': [
                        ('Because C does not automatically track the length of arrays', True),
                        ('Because the pointer value contains the length', False),
                        ('Because all C arrays have a fixed length of 100', False),
                        ('To allow the function to allocate a larger array', False),
                    ],
                },
                {
                    'text': 'In Python, if you pass a list to a function and modify it inside, what happens to the original list?',
                    'options': [
                        ('Nothing — Python always makes a copy', False),
                        ('The modifications affect the original list because the function receives a reference', True),
                        ('An error is raised because lists are immutable', False),
                        ('Only the first element is modified', False),
                    ],
                },
            ],
        },
        'Dynamic Memory (malloc and free)': {
            'title': 'Dynamic Memory Quiz',
            'questions': [
                {
                    'text': 'What does malloc(n) return in C?',
                    'options': [
                        ('An integer equal to n', False),
                        ('A void pointer to a newly allocated block of n bytes', True),
                        ('A pointer to already-initialised memory', False),
                        ('The number of bytes successfully allocated', False),
                    ],
                },
                {
                    'text': 'What happens if you forget to call free() on a malloc-allocated block?',
                    'options': [
                        ('The OS automatically reclaims it when that variable goes out of scope', False),
                        ('The program crashes immediately', False),
                        ('A memory leak occurs — the memory is not returned until the process exits', True),
                        ('The next malloc call frees the previous block automatically', False),
                    ],
                },
                {
                    'text': 'How does Python handle memory deallocation compared to C?',
                    'options': [
                        ('Python requires the programmer to call del() on every object', False),
                        ("Python's garbage collector handles deallocation automatically via reference counting", True),
                        ('Python objects are stack-allocated and freed automatically on return', False),
                        ('Python uses the same malloc/free functions as C internally', False),
                    ],
                },
            ],
        },
        'Common Pointer Pitfalls': {
            'title': 'Pointer Pitfalls Quiz',
            'questions': [
                {
                    'text': 'What is a dangling pointer?',
                    'options': [
                        ('A pointer that was never initialised', False),
                        ('A pointer that still holds an address after the memory it points to has been freed', True),
                        ('A pointer to NULL', False),
                        ('A pointer used in a different function scope', False),
                    ],
                },
                {
                    'text': 'What is the best practice after calling free(p) in C?',
                    'options': [
                        ('Call free(p) a second time to ensure it is released', False),
                        ('Set p = NULL to prevent accidental dangling pointer use', True),
                        ('Immediately reallocate p with malloc', False),
                        ('Leave p unchanged — the OS handles it', False),
                    ],
                },
                {
                    'text': 'What Java exception is the closest equivalent to a C NULL pointer dereference?',
                    'options': [
                        ('ArrayIndexOutOfBoundsException', False),
                        ('StackOverflowError', False),
                        ('NullPointerException', True),
                        ('ClassCastException', False),
                    ],
                },
            ],
        },
    },

    # ── Module 11: Linked Lists ──────────────────────────────────────────────
    'Linked Lists': {
        'What is a Linked List?': {
            'title': 'Linked List Concepts Quiz',
            'questions': [
                {
                    'text': 'What is the primary advantage of a linked list over an array?',
                    'options': [
                        ('O(1) access by index', False),
                        ('O(1) insertion and deletion at the head without shifting elements', True),
                        ('Less memory usage per element', False),
                        ('Cache-friendly linear memory layout', False),
                    ],
                },
                {
                    'text': 'In a singly linked list, what does the tail node\'s next pointer contain?',
                    'options': [
                        ('The address of the head node', False),
                        ('NULL (or None / null in Python/Java)', True),
                        ('The number of nodes in the list', False),
                        ('A pointer back to itself', False),
                    ],
                },
                {
                    'text': 'What is the time complexity of accessing the k-th element in a linked list?',
                    'options': [
                        ('O(1)', False),
                        ('O(log n)', False),
                        ('O(n)', True),
                        ('O(k log k)', False),
                    ],
                },
            ],
        },
        'Building a Singly Linked List': {
            'title': 'Building Linked Lists Quiz',
            'questions': [
                {
                    'text': 'What is the time complexity of prepending a node to the head of a singly linked list?',
                    'options': [
                        ('O(n) — must traverse to the end', False),
                        ('O(log n)', False),
                        ('O(1) — just update the head pointer', True),
                        ('O(n²)', False),
                    ],
                },
                {
                    'text': 'Why is appending to the tail O(n) without a tail pointer?',
                    'options': [
                        ('Because the list must be sorted first', False),
                        ('Because you must traverse the entire list to find the last node', True),
                        ('Because memory must be reallocated', False),
                        ('Because each node must be copied', False),
                    ],
                },
                {
                    'text': 'When prepending a new node, which pointer is updated?',
                    'options': [
                        ('The previous tail\'s next pointer', False),
                        ('The new node\'s next pointer (to old head) and then the head pointer', True),
                        ('Only the new node\'s data field', False),
                        ('The previous head\'s prev pointer', False),
                    ],
                },
            ],
        },
        'Traversal and Search': {
            'title': 'Linked List Traversal Quiz',
            'questions': [
                {
                    'text': 'What is the correct traversal pattern for a singly linked list?',
                    'options': [
                        ('Start at the tail and walk backwards using prev pointers', False),
                        ('Start at the head and follow next pointers until NULL', True),
                        ('Use binary search with two pointers', False),
                        ('Access nodes by index directly', False),
                    ],
                },
                {
                    'text': 'What is the time complexity of searching for a value in an unsorted linked list?',
                    'options': [
                        ('O(1)', False),
                        ('O(log n)', False),
                        ('O(n)', True),
                        ('O(n log n)', False),
                    ],
                },
                {
                    'text': 'What does a search function return when the target is not found in a C linked list?',
                    'options': [
                        ('0', False),
                        ('NULL (a null pointer)', True),
                        ('The head pointer', False),
                        ('An empty node', False),
                    ],
                },
            ],
        },
        'Insertion and Deletion': {
            'title': 'Linked List Insertion and Deletion Quiz',
            'questions': [
                {
                    'text': 'To delete a node by value in a singly linked list, what do you need?',
                    'options': [
                        ('Only a pointer to the node to delete', False),
                        ('A pointer to the node before the one to delete', True),
                        ('Pointers to both the node before and the node after', False),
                        ('A complete copy of the list', False),
                    ],
                },
                {
                    'text': 'What must you do first when deleting the head node of a singly linked list?',
                    'options': [
                        ('Set the head\'s data to 0', False),
                        ('Update head to point to the second node (head = head.next)', True),
                        ('Free head before updating the pointer', False),
                        ('Copy all remaining nodes', False),
                    ],
                },
                {
                    'text': 'In Python, when you do cur.next = cur.next.next to delete a node, what happens to the skipped node?',
                    'options': [
                        ('It remains in memory indefinitely', False),
                        ('It causes a memory leak', False),
                        ('The garbage collector reclaims it when no references exist', True),
                        ('It is immediately freed', False),
                    ],
                },
            ],
        },
        'Doubly Linked Lists': {
            'title': 'Doubly Linked Lists Quiz',
            'questions': [
                {
                    'text': 'What additional pointer does each node in a doubly linked list have compared to a singly linked list?',
                    'options': [
                        ('A pointer to the head of the list', False),
                        ('A prev pointer to the previous node', True),
                        ('A counter of remaining nodes', False),
                        ('A pointer to the middle node', False),
                    ],
                },
                {
                    'text': 'Which Python built-in provides a doubly linked list with O(1) operations at both ends?',
                    'options': [
                        ('list', False),
                        ('tuple', False),
                        ('collections.deque', True),
                        ('heapq', False),
                    ],
                },
                {
                    'text': 'What is the main advantage of a doubly linked list over a singly linked list for deletion?',
                    'options': [
                        ('Deletion is O(1) when you have a direct reference to the node, without needing to find the previous node', True),
                        ('Deletion is O(log n) using binary search', False),
                        ('Memory usage is halved', False),
                        ('Values are deleted from both ends simultaneously', False),
                    ],
                },
            ],
        },
    },

    # ── Module 12: Stacks & Queues ───────────────────────────────────────────
    'Stacks & Queues': {
        'Stack Concept (LIFO)': {
            'title': 'Stack Concepts Quiz',
            'questions': [
                {
                    'text': 'What does LIFO stand for?',
                    'options': [
                        ('Last Item Found Output', False),
                        ('Last In, First Out', True),
                        ('Linear Index For Operations', False),
                        ('Low Input First Output', False),
                    ],
                },
                {
                    'text': 'Which real-world scenario best models a stack?',
                    'options': [
                        ('A queue of people waiting for a bus (first-come, first-served)', False),
                        ('A pile of plates where you always add and remove from the top', True),
                        ('A sorted list of items accessed by index', False),
                        ('A circular conveyor belt', False),
                    ],
                },
                {
                    'text': 'Which algorithm naturally uses a stack for its operation?',
                    'options': [
                        ('Breadth-First Search (BFS)', False),
                        ('Binary search', False),
                        ('Depth-First Search (DFS)', True),
                        ('Merge sort', False),
                    ],
                },
            ],
        },
        'Implementing a Stack': {
            'title': 'Stack Implementation Quiz',
            'questions': [
                {
                    'text': 'In a C array-based stack, what does top = -1 indicate?',
                    'options': [
                        ('The stack has one element', False),
                        ('The stack is full', False),
                        ('The stack is empty', True),
                        ('The stack pointer has underflowed', False),
                    ],
                },
                {
                    'text': 'Which Java class is preferred for implementing a stack?',
                    'options': [
                        ('java.util.Stack (legacy)', False),
                        ('java.util.ArrayList', False),
                        ('java.util.ArrayDeque', True),
                        ('java.util.TreeSet', False),
                    ],
                },
                {
                    'text': 'What is the advantage of a linked-list-based stack over an array-based stack?',
                    'options': [
                        ('It is more cache-friendly', False),
                        ('It has no fixed maximum capacity', True),
                        ('Push and pop are O(log n)', False),
                        ('It uses less memory per element', False),
                    ],
                },
            ],
        },
        'Queue Concept (FIFO)': {
            'title': 'Queue Concepts Quiz',
            'questions': [
                {
                    'text': 'What does FIFO stand for?',
                    'options': [
                        ('First In, First Out', True),
                        ('Fast Index For Output', False),
                        ('First Item Free Operation', False),
                        ('Forward In, Forward Out', False),
                    ],
                },
                {
                    'text': 'Which algorithm uses a queue as its core data structure?',
                    'options': [
                        ('Depth-First Search (DFS)', False),
                        ('Breadth-First Search (BFS)', True),
                        ('Quicksort', False),
                        ('Binary search', False),
                    ],
                },
                {
                    'text': 'Why should you avoid using list.pop(0) in Python as a queue dequeue operation?',
                    'options': [
                        ('pop(0) is not a valid operation on Python lists', False),
                        ('pop(0) is O(n) because all remaining elements must shift', True),
                        ('It removes from the wrong end', False),
                        ('It only works on sorted lists', False),
                    ],
                },
            ],
        },
        'Implementing a Queue': {
            'title': 'Queue Implementation Quiz',
            'questions': [
                {
                    'text': 'What problem does a circular buffer solve for array-based queues?',
                    'options': [
                        ('It prevents collisions between elements', False),
                        ('It wastes space as the front index advances — the circular buffer reuses freed slots', True),
                        ('It sorts elements automatically', False),
                        ('It doubles the capacity of the array', False),
                    ],
                },
                {
                    'text': 'In a circular array queue, how is the rear index advanced after enqueue?',
                    'options': [
                        ('rear = rear + 1', False),
                        ('rear = (rear + 1) % MAX', True),
                        ('rear = rear * 2', False),
                        ('rear = front + 1', False),
                    ],
                },
                {
                    'text': 'Which Python class provides O(1) enqueue and dequeue for a queue?',
                    'options': [
                        ('list', False),
                        ('set', False),
                        ('collections.deque', True),
                        ('queue.PriorityQueue', False),
                    ],
                },
            ],
        },
        'Applications: Bracket Matching, BFS, Undo/Redo': {
            'title': 'Stack and Queue Applications Quiz',
            'questions': [
                {
                    'text': 'How does a stack solve the bracket matching problem?',
                    'options': [
                        ('By sorting the brackets first and then comparing', False),
                        ('By pushing opening brackets and popping/matching when a closing bracket is seen', True),
                        ('By using two queues simultaneously', False),
                        ('By counting open and close brackets and comparing totals', False),
                    ],
                },
                {
                    'text': 'In an undo/redo system using two stacks, what happens when you press Undo?',
                    'options': [
                        ('The undo stack is cleared', False),
                        ('The top action is popped from the undo stack and pushed onto the redo stack', True),
                        ('Both stacks are merged', False),
                        ('The redo stack is cleared', False),
                    ],
                },
                {
                    'text': 'In BFS, why is a queue used instead of a stack?',
                    'options': [
                        ('Because queues are faster than stacks', False),
                        ('A queue ensures nodes are visited in the order they were discovered (level by level)', True),
                        ('Because stacks cannot store graph nodes', False),
                        ('Because BFS requires sorting nodes before visiting', False),
                    ],
                },
            ],
        },
    },

    # ── Module 13: Hash Tables & Dictionaries ────────────────────────────────
    'Hash Tables & Dictionaries': {
        'Hash Concepts and Hash Functions': {
            'title': 'Hash Table Concepts Quiz',
            'questions': [
                {
                    'text': 'What is the purpose of a hash function in a hash table?',
                    'options': [
                        ('To sort the keys alphabetically', False),
                        ('To convert a key into an array index', True),
                        ('To encrypt the stored values', False),
                        ('To compress the data into fewer bytes', False),
                    ],
                },
                {
                    'text': 'What is a collision in a hash table?',
                    'options': [
                        ('Two different values being equal', False),
                        ('Two different keys producing the same hash index', True),
                        ('The table running out of memory', False),
                        ('A key being deleted while another thread reads it', False),
                    ],
                },
                {
                    'text': 'What is the average time complexity for insertion and lookup in a well-designed hash table?',
                    'options': [
                        ('O(n)', False),
                        ('O(log n)', False),
                        ('O(1)', True),
                        ('O(n²)', False),
                    ],
                },
            ],
        },
        'Dictionaries in Python': {
            'title': 'Python Dictionaries Quiz',
            'questions': [
                {
                    'text': 'What does d.get("key", "default") return when "key" is not in d?',
                    'options': [
                        ('It raises a KeyError', False),
                        ('"default"', True),
                        ('None', False),
                        ('An empty dict', False),
                    ],
                },
                {
                    'text': 'Which Python collection automatically initialises missing keys with a default value?',
                    'options': [
                        ('dict', False),
                        ('Counter', False),
                        ('defaultdict', True),
                        ('OrderedDict', False),
                    ],
                },
                {
                    'text': 'Which method iterates over key-value pairs of a Python dict?',
                    'options': [
                        ('d.keys()', False),
                        ('d.values()', False),
                        ('d.items()', True),
                        ('d.pairs()', False),
                    ],
                },
            ],
        },
        'HashMaps in Java': {
            'title': 'Java HashMap Quiz',
            'questions': [
                {
                    'text': 'Which Java Map preserves the insertion order of key-value pairs?',
                    'options': [
                        ('HashMap', False),
                        ('TreeMap', False),
                        ('LinkedHashMap', True),
                        ('WeakHashMap', False),
                    ],
                },
                {
                    'text': 'What does getOrDefault(key, defaultVal) return when the key is absent?',
                    'options': [
                        ('It throws a NullPointerException', False),
                        ('null', False),
                        ('defaultVal', True),
                        ('An empty string', False),
                    ],
                },
                {
                    'text': 'Is Java\'s HashMap thread-safe?',
                    'options': [
                        ('Yes, all HashMap operations are synchronised', False),
                        ('No — use ConcurrentHashMap in multi-threaded code', True),
                        ('Only the get() method is thread-safe', False),
                        ('Yes, because Java objects are immutable by default', False),
                    ],
                },
            ],
        },
        'Manual Hash Table in C': {
            'title': 'Manual Hash Table in C Quiz',
            'questions': [
                {
                    'text': 'In separate chaining, what does each array bucket contain?',
                    'options': [
                        ('A single key-value pair', False),
                        ('A sorted array of values', False),
                        ('A linked list of all entries that hashed to that index', True),
                        ('A binary tree of key-value pairs', False),
                    ],
                },
                {
                    'text': 'Why is a prime number often chosen as the table size for a hash table?',
                    'options': [
                        ('To make the hash function faster to compute', False),
                        ('To reduce clustering by distributing keys more evenly with modulo hashing', True),
                        ('Prime sizes allow the table to grow indefinitely', False),
                        ('Required by the C standard', False),
                    ],
                },
                {
                    'text': 'When should you rehash a hash table?',
                    'options': [
                        ('After every insertion', False),
                        ('Only when a collision occurs', False),
                        ('When the load factor exceeds a threshold (typically 0.75)', True),
                        ('When the table has been used for more than 1000 operations', False),
                    ],
                },
            ],
        },
        'Collision Handling': {
            'title': 'Collision Handling Quiz',
            'questions': [
                {
                    'text': 'In linear probing, what happens when a collision occurs at index i?',
                    'options': [
                        ('The entry is discarded', False),
                        ('The entry is stored at the next available index (i+1, i+2, ...) cyclically', True),
                        ('A new bucket is allocated inline', False),
                        ('The key is hashed again with a different function', False),
                    ],
                },
                {
                    'text': 'What is the worst-case time complexity for lookup in a hash table with many collisions?',
                    'options': [
                        ('O(1)', False),
                        ('O(log n)', False),
                        ('O(n) — all keys in one bucket requires a full list scan', True),
                        ('O(n²)', False),
                    ],
                },
                {
                    'text': 'In Java 8+, what does HashMap use when a single bucket\'s chain exceeds 8 entries?',
                    'options': [
                        ('A sorted array', False),
                        ('A red-black tree, giving O(log n) worst-case performance', True),
                        ('A secondary hash table', False),
                        ('A skip list', False),
                    ],
                },
            ],
        },
    },
}


class Command(BaseCommand):
    help = 'Seed quizzes for the 4 new learning modules (Pointers, Linked Lists, Stacks/Queues, Hash Tables)'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        missing = 0

        for module_title, lessons in QUIZ_DATA.items():
            try:
                module = LearningModule.objects.get(title=module_title)
            except LearningModule.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Module "{module_title}" not found — run seed_new_modules first.'
                    )
                )
                missing += len(lessons)
                continue

            for lesson_title, quiz_def in lessons.items():
                try:
                    lesson = Lesson.objects.get(module=module, title=lesson_title)
                except Lesson.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  Lesson "{lesson_title}" not found in "{module_title}", skipping.')
                    )
                    missing += 1
                    continue

                if hasattr(lesson, 'quiz'):
                    self.stdout.write(
                        f'  Quiz for "{lesson_title}" already exists, skipping.'
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
                        f'  Created quiz "{quiz_def["title"]}" for lesson "{lesson_title}"'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created: {created}, Skipped: {skipped}, Not found: {missing}'
            )
        )
