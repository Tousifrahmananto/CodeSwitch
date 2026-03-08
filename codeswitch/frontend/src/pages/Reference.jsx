import { useState } from 'react';

const LANG_META = {
    python: { label: 'Python', color: '#3572A5' },
    c: { label: 'C', color: '#6c757d' },
    java: { label: 'Java', color: '#b07219' },
    javascript: { label: 'JavaScript', color: '#f1e05a' },
    cpp: { label: 'C++', color: '#f34b7d' },
};

const ALL_LANGS = ['python', 'c', 'java', 'javascript', 'cpp'];

const CONCEPTS = [
    {
        id: 'variables',
        title: 'Variables & Types',
        description: 'Declaring and assigning variables with different data types.',
        examples: {
            python:
                `# Python — dynamic typing, no declaration needed
name = "Alice"
age = 25
score = 98.5
is_active = True`,
            c:
                `// C — must declare type before use
char name[] = "Alice";
int age = 25;
double score = 98.5;
int is_active = 1;  // C89 has no bool`,
            java:
                `// Java — statically typed
String name = "Alice";
int age = 25;
double score = 98.5;
boolean isActive = true;`,
            javascript:
                `// JavaScript — dynamic, use let/const
let name = "Alice";
let age = 25;
let score = 98.5;
let isActive = true;`,
            cpp:
                `// C++ — like C but with bool and std::string
#include <string>
std::string name = "Alice";
int age = 25;
double score = 98.5;
bool isActive = true;`,
        },
    },
    {
        id: 'if-else',
        title: 'If / Else',
        description: 'Conditional branching — checking conditions and taking different paths.',
        examples: {
            python:
                `# Python — no parentheses, colon + indentation
x = 10
if x > 0:
    print("positive")
elif x == 0:
    print("zero")
else:
    print("negative")`,
            c:
                `// C — parentheses required, curly braces for blocks
int x = 10;
if (x > 0) {
    printf("positive\\n");
} else if (x == 0) {
    printf("zero\\n");
} else {
    printf("negative\\n");
}`,
            java:
                `// Java — same as C syntax
int x = 10;
if (x > 0) {
    System.out.println("positive");
} else if (x == 0) {
    System.out.println("zero");
} else {
    System.out.println("negative");
}`,
            javascript:
                `// JavaScript — use === for strict equality
let x = 10;
if (x > 0) {
    console.log("positive");
} else if (x === 0) {
    console.log("zero");
} else {
    console.log("negative");
}`,
            cpp:
                `// C++ — same as C, but with cout
int x = 10;
if (x > 0) {
    std::cout << "positive" << std::endl;
} else if (x == 0) {
    std::cout << "zero" << std::endl;
} else {
    std::cout << "negative" << std::endl;
}`,
        },
    },
    {
        id: 'for-loops',
        title: 'For Loops',
        description: 'Iterating a fixed number of times or over a collection.',
        examples: {
            python:
                `# Python — range() for numeric, direct iteration for lists
for i in range(5):
    print(i)            # 0 1 2 3 4

fruits = ["apple", "banana"]
for fruit in fruits:
    print(fruit)`,
            c:
                `// C — classic three-part for loop
for (int i = 0; i < 5; i++) {
    printf("%d\\n", i);
}

// Array iteration (need size separately)
int arr[] = {1, 2, 3};
int size = 3;
for (int i = 0; i < size; i++) {
    printf("%d\\n", arr[i]);
}`,
            java:
                `// Java — classic for + enhanced for-each
for (int i = 0; i < 5; i++) {
    System.out.println(i);
}

// For-each works on arrays and collections
int[] arr = {1, 2, 3};
for (int num : arr) {
    System.out.println(num);
}`,
            javascript:
                `// JavaScript — classic for + for...of
for (let i = 0; i < 5; i++) {
    console.log(i);
}

// for...of iterates over values
const fruits = ["apple", "banana"];
for (const fruit of fruits) {
    console.log(fruit);
}`,
            cpp:
                `// C++ — classic for + range-based for
for (int i = 0; i < 5; i++) {
    std::cout << i << std::endl;
}

// Range-based for (C++11+)
std::vector<int> nums = {1, 2, 3};
for (int n : nums) {
    std::cout << n << std::endl;
}`,
        },
    },
    {
        id: 'while-loops',
        title: 'While Loops',
        description: 'Repeating a block as long as a condition is true.',
        examples: {
            python:
                `# Python
n = 5
while n > 0:
    print(n)
    n -= 1     # n-- does not exist in Python`,
            c:
                `// C
int n = 5;
while (n > 0) {
    printf("%d\\n", n);
    n--;
}`,
            java:
                `// Java
int n = 5;
while (n > 0) {
    System.out.println(n);
    n--;
}`,
            javascript:
                `// JavaScript
let n = 5;
while (n > 0) {
    console.log(n);
    n--;
}`,
            cpp:
                `// C++
int n = 5;
while (n > 0) {
    std::cout << n << std::endl;
    n--;
}`,
        },
    },
    {
        id: 'functions',
        title: 'Functions',
        description: 'Defining reusable blocks of code that take arguments and return values.',
        examples: {
            python:
                `# Python — def keyword, no return type annotation needed
def add(a, b):
    return a + b

def greet(name="World"):  # default parameter
    print(f"Hello, {name}!")

result = add(3, 4)  # 7
greet("Alice")      # Hello, Alice!`,
            c:
                `// C — return type must be declared
int add(int a, int b) {
    return a + b;
}

void greet(const char* name) {
    printf("Hello, %s!\\n", name);
}

int result = add(3, 4);  // 7
greet("Alice");           // Hello, Alice!`,
            java:
                `// Java — all functions live inside classes
public static int add(int a, int b) {
    return a + b;
}

public static void greet(String name) {
    System.out.println("Hello, " + name + "!");
}

int result = add(3, 4);  // 7
greet("Alice");           // Hello, Alice!`,
            javascript:
                `// JavaScript — function keyword or arrow syntax
function add(a, b) {
    return a + b;
}

const greet = (name = "World") => {
    console.log(\`Hello, \${name}!\`);
};

const result = add(3, 4);  // 7
greet("Alice");             // Hello, Alice!`,
            cpp:
                `// C++ — same as C but can use default parameters
int add(int a, int b) {
    return a + b;
}

void greet(std::string name = "World") {
    std::cout << "Hello, " << name << "!" << std::endl;
}

int result = add(3, 4);  // 7
greet("Alice");           // Hello, Alice!`,
        },
    },
    {
        id: 'arrays-lists',
        title: 'Arrays & Lists',
        description: 'Storing and accessing ordered collections of values.',
        examples: {
            python:
                `# Python — lists are dynamic, mixed types allowed
nums = [1, 2, 3, 4, 5]
nums.append(6)       # add to end
print(nums[0])       # 1  (zero-indexed)
print(nums[-1])      # 6  (last item)
print(len(nums))     # 6
print(nums[1:3])     # [2, 3]  (slicing)`,
            c:
                `// C — fixed-size arrays, no built-in append
int nums[5] = {1, 2, 3, 4, 5};
printf("%d\\n", nums[0]);  // 1
int size = sizeof(nums) / sizeof(nums[0]);  // 5
// Dynamic arrays require malloc/realloc`,
            java:
                `// Java — fixed arrays or ArrayList for dynamic
int[] nums = {1, 2, 3, 4, 5};
System.out.println(nums[0]);   // 1
System.out.println(nums.length); // 5

// Dynamic:
import java.util.ArrayList;
ArrayList<Integer> list = new ArrayList<>();
list.add(6);
System.out.println(list.size()); // 1`,
            javascript:
                `// JavaScript — arrays are dynamic and flexible
const nums = [1, 2, 3, 4, 5];
nums.push(6);              // add to end
nums.unshift(0);           // add to front
console.log(nums[0]);      // 0
console.log(nums.length);  // 7
console.log(nums.slice(1, 3)); // [1, 2]`,
            cpp:
                `// C++ — use std::vector for dynamic arrays
#include <vector>
std::vector<int> nums = {1, 2, 3, 4, 5};
nums.push_back(6);
std::cout << nums[0];      // 1
std::cout << nums.size();  // 6
// Or fixed: int arr[5] = {1,2,3,4,5};`,
        },
    },
    {
        id: 'strings',
        title: 'String Operations',
        description: 'Common string operations: length, case, split, and slicing.',
        examples: {
            python:
                `# Python — strings are immutable objects
s = "Hello, World!"
print(len(s))            # 13
print(s.upper())         # HELLO, WORLD!
print(s.lower())         # hello, world!
print(s.split(", "))     # ['Hello', 'World!']
print(s[0:5])            # Hello
print(s.replace("World", "Python"))  # Hello, Python!`,
            c:
                `// C — strings are char arrays, use string.h
#include <string.h>
#include <stdio.h>
char s[] = "Hello, World!";
printf("%lu\\n", strlen(s));  // 13
// No built-in upper/split — requires loops
// Use strstr() to find substrings
char* pos = strstr(s, "World");
if (pos) printf("Found at index %ld\\n", pos - s);`,
            java:
                `// Java — String is an immutable class
String s = "Hello, World!";
System.out.println(s.length());          // 13
System.out.println(s.toUpperCase());     // HELLO, WORLD!
System.out.println(s.toLowerCase());     // hello, world!
String[] parts = s.split(", ");         // ["Hello", "World!"]
System.out.println(s.substring(0, 5));  // Hello
System.out.println(s.replace("World", "Python"));`,
            javascript:
                `// JavaScript — strings have rich built-in methods
const s = "Hello, World!";
console.log(s.length);              // 13
console.log(s.toUpperCase());       // HELLO, WORLD!
console.log(s.toLowerCase());       // hello, world!
console.log(s.split(", "));         // ['Hello', 'World!']
console.log(s.slice(0, 5));         // Hello
console.log(s.replace("World", "Python"));`,
            cpp:
                `// C++ — std::string with member methods
#include <string>
#include <algorithm>
std::string s = "Hello, World!";
std::cout << s.size();           // 13
std::cout << s.substr(0, 5);     // Hello
// toUpper requires transform:
std::string up = s;
std::transform(up.begin(), up.end(), up.begin(), ::toupper);
std::cout << up;  // HELLO, WORLD!`,
        },
    },
    {
        id: 'io',
        title: 'Input & Output',
        description: 'Reading user input from the console and printing formatted output.',
        examples: {
            python:
                `# Python — input() always returns a string
name = input("Enter your name: ")
age = int(input("Enter your age: "))  # convert to int
print(f"Hello, {name}! You are {age}.")
print(f"Pi is approximately {3.14159:.2f}")`,
            c:
                `// C — printf/scanf with format specifiers
#include <stdio.h>
char name[100];
int age;
printf("Enter your name: ");
scanf("%s", name);
printf("Enter your age: ");
scanf("%d", &age);
printf("Hello, %s! You are %d.\\n", name, age);
printf("Pi is approximately %.2f\\n", 3.14159);`,
            java:
                `// Java — Scanner for input, println for output
import java.util.Scanner;
Scanner sc = new Scanner(System.in);
System.out.print("Enter your name: ");
String name = sc.nextLine();
System.out.print("Enter your age: ");
int age = sc.nextInt();
System.out.println("Hello, " + name + "! You are " + age + ".");
System.out.printf("Pi is approximately %.2f%n", 3.14159);`,
            javascript:
                `// JavaScript (Node.js) — readline for input
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
rl.question('Enter your name: ', (name) => {
    console.log(\`Hello, \${name}!\`);
    console.log(\`Pi is approximately \${(3.14159).toFixed(2)}\`);
    rl.close();
});`,
            cpp:
                `// C++ — cin for input, cout for output
#include <iostream>
#include <string>
#include <iomanip>
std::string name;
int age;
std::cout << "Enter your name: ";
std::cin >> name;
std::cout << "Enter your age: ";
std::cin >> age;
std::cout << "Hello, " << name << "! You are " << age << "." << std::endl;
std::cout << std::fixed << std::setprecision(2) << 3.14159 << std::endl;`,
        },
    },
    {
        id: 'classes',
        title: 'Classes & Objects',
        description: 'Defining blueprints for objects with state (fields) and behaviour (methods).',
        examples: {
            python:
                `# Python — self is the explicit first parameter
class Animal:
    def __init__(self, name, sound):
        self.name = name
        self.sound = sound

    def speak(self):
        return f"{self.name} says {self.sound}"

dog = Animal("Rex", "Woof")
print(dog.speak())  # Rex says Woof`,
            c:
                `// C — no classes; use structs + functions
#include <stdio.h>
#include <string.h>

typedef struct {
    char name[50];
    char sound[50];
} Animal;

void speak(Animal* a) {
    printf("%s says %s\\n", a->name, a->sound);
}

Animal dog;
strcpy(dog.name, "Rex");
strcpy(dog.sound, "Woof");
speak(&dog);  // Rex says Woof`,
            java:
                `// Java — classes are fundamental; constructor = class name
public class Animal {
    private String name;
    private String sound;

    public Animal(String name, String sound) {
        this.name = name;
        this.sound = sound;
    }

    public String speak() {
        return name + " says " + sound;
    }
}

Animal dog = new Animal("Rex", "Woof");
System.out.println(dog.speak());  // Rex says Woof`,
            javascript:
                `// JavaScript — class keyword (ES6+)
class Animal {
    constructor(name, sound) {
        this.name = name;
        this.sound = sound;
    }

    speak() {
        return \`\${this.name} says \${this.sound}\`;
    }
}

const dog = new Animal("Rex", "Woof");
console.log(dog.speak());  // Rex says Woof`,
            cpp:
                `// C++ — classes with public/private access
#include <string>
#include <iostream>

class Animal {
public:
    std::string name, sound;

    Animal(std::string n, std::string s) : name(n), sound(s) {}

    std::string speak() {
        return name + " says " + sound;
    }
};

Animal dog("Rex", "Woof");
std::cout << dog.speak() << std::endl;  // Rex says Woof`,
        },
    },
    {
        id: 'exceptions',
        title: 'Error Handling',
        description: 'Catching and handling runtime errors so your program does not crash.',
        examples: {
            python:
                `# Python — try/except/finally
try:
    numerator = int(input("Enter number: "))
    result = 10 / numerator
    print(f"Result: {result}")
except ValueError:
    print("Error: that's not a number")
except ZeroDivisionError:
    print("Error: cannot divide by zero")
finally:
    print("Calculation done.")   # always runs`,
            c:
                `// C — no exceptions; use return codes or errno
#include <stdio.h>
#include <errno.h>

int divide(int a, int b, int *out) {
    if (b == 0) return -1;  // signal error
    *out = a / b;
    return 0;               // success
}

int result;
if (divide(10, 0, &result) != 0) {
    printf("Error: cannot divide by zero\\n");
} else {
    printf("Result: %d\\n", result);
}`,
            java:
                `// Java — checked and unchecked exceptions
try {
    int result = 10 / 0;
    System.out.println("Result: " + result);
} catch (ArithmeticException e) {
    System.out.println("Error: " + e.getMessage());
} catch (Exception e) {
    System.out.println("Unknown error: " + e.getMessage());
} finally {
    System.out.println("Calculation done.");
}`,
            javascript:
                `// JavaScript — try/catch/finally
try {
    const b = 0;
    if (b === 0) throw new Error("Cannot divide by zero");
    const result = 10 / b;
    console.log("Result:", result);
} catch (e) {
    console.log("Error:", e.message);
} finally {
    console.log("Calculation done.");
}
// Note: 10/0 = Infinity in JS, not an error`,
            cpp:
                `// C++ — try/catch with exception objects
#include <stdexcept>
#include <iostream>

try {
    int b = 0;
    if (b == 0) throw std::runtime_error("Cannot divide by zero");
    int result = 10 / b;
    std::cout << "Result: " << result << std::endl;
} catch (const std::runtime_error& e) {
    std::cout << "Error: " << e.what() << std::endl;
} catch (const std::exception& e) {
    std::cout << "Unknown error: " << e.what() << std::endl;
}`,
        },
    },
];

export default function Reference() {
    const [search, setSearch] = useState('');
    const [activeTab, setActiveTab] = useState({});  // conceptId -> lang
    const [copied, setCopied] = useState({});         // conceptId -> bool

    const filtered = CONCEPTS.filter(c =>
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.description.toLowerCase().includes(search.toLowerCase())
    );

    const getTab = (id) => activeTab[id] || 'python';

    const handleCopy = (id, lang) => {
        const concept = CONCEPTS.find(c => c.id === id);
        if (!concept) return;
        navigator.clipboard.writeText(concept.examples[lang]);
        setCopied(prev => ({ ...prev, [id]: true }));
        setTimeout(() => setCopied(prev => ({ ...prev, [id]: false })), 2000);
    };

    return (
        <div className="reference-page">
            <div className="reference-header">
                <h2>Language Reference</h2>
                <p className="reference-subtitle">
                    Side-by-side syntax for Python, C, Java, JavaScript, and C++ — organised by concept.
                </p>
                <input
                    className="reference-search"
                    type="text"
                    placeholder="Search concepts (loops, functions, classes...)"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
            </div>

            {filtered.length === 0 && (
                <p style={{ color: 'var(--text-muted)', marginTop: 24 }}>
                    No concepts match "{search}".
                </p>
            )}

            <div className="reference-grid">
                {filtered.map(concept => {
                    const tab = getTab(concept.id);
                    return (
                        <div key={concept.id} className="reference-card">
                            <div className="reference-card-header">
                                <div>
                                    <h3 className="reference-card-title">{concept.title}</h3>
                                    <p className="reference-card-desc">{concept.description}</p>
                                </div>
                            </div>

                            {/* Language tabs */}
                            <div className="ref-tab-bar">
                                {ALL_LANGS.map(lang => (
                                    <button
                                        key={lang}
                                        className={`ref-tab-btn${tab === lang ? ' active' : ''}`}
                                        style={tab === lang ? { borderBottomColor: LANG_META[lang].color } : {}}
                                        onClick={() => setActiveTab(prev => ({ ...prev, [concept.id]: lang }))}
                                    >
                                        <span
                                            className="ref-lang-dot"
                                            style={{ background: LANG_META[lang].color }}
                                        />
                                        {LANG_META[lang].label}
                                    </button>
                                ))}
                                <button
                                    className={`code-copy-btn${copied[concept.id] ? ' copied' : ''}`}
                                    onClick={() => handleCopy(concept.id, tab)}
                                >
                                    {copied[concept.id] ? 'Copied!' : 'Copy'}
                                </button>
                            </div>

                            <pre className="reference-code"><code>{concept.examples[tab]}</code></pre>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
