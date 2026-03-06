import json
from django.core.management.base import BaseCommand
from learning.models import LearningModule, Lesson

MODULES = [
    # ── Module 7: Advanced Sorting (intermediate) ────────────────────────
    {
        'meta': {
            'title': 'Advanced Sorting Algorithms',
            'description': 'Go beyond bubble sort. Learn insertion sort, merge sort, and quicksort — the workhorses of real-world software.',
            'difficulty': 'intermediate',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'Insertion Sort',
                'content': (
                    'Insertion sort builds a sorted array one element at a time. '
                    'It picks the next unsorted element and inserts it into its correct position in the already-sorted portion.\n\n'
                    'Think of sorting a hand of playing cards: you pick a card and slide it into the right spot among the cards already in your hand.\n\n'
                    'Time complexity: O(n²) worst/average, O(n) best case (already sorted). '
                    'It is efficient for small arrays and nearly-sorted data, and is stable (equal elements keep their original order).'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'void insertionSort(int arr[], int n) {\n'
                        '    for (int i = 1; i < n; i++) {\n'
                        '        int key = arr[i];\n'
                        '        int j = i - 1;\n'
                        '        while (j >= 0 && arr[j] > key) {\n'
                        '            arr[j + 1] = arr[j];\n'
                        '            j--;\n'
                        '        }\n'
                        '        arr[j + 1] = key;\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int arr[] = {12, 11, 13, 5, 6};\n'
                        '    insertionSort(arr, 5);\n'
                        '    for (int i = 0; i < 5; i++) printf("%d ", arr[i]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def insertion_sort(arr):\n'
                        '    for i in range(1, len(arr)):\n'
                        '        key = arr[i]\n'
                        '        j = i - 1\n'
                        '        while j >= 0 and arr[j] > key:\n'
                        '            arr[j + 1] = arr[j]\n'
                        '            j -= 1\n'
                        '        arr[j + 1] = key\n'
                        '    return arr\n\n'
                        'arr = [12, 11, 13, 5, 6]\n'
                        'print(insertion_sort(arr))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static void insertionSort(int[] arr) {\n'
                        '        for (int i = 1; i < arr.length; i++) {\n'
                        '            int key = arr[i];\n'
                        '            int j = i - 1;\n'
                        '            while (j >= 0 && arr[j] > key) {\n'
                        '                arr[j + 1] = arr[j];\n'
                        '                j--;\n'
                        '            }\n'
                        '            arr[j + 1] = key;\n'
                        '        }\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] arr = {12, 11, 13, 5, 6};\n'
                        '        insertionSort(arr);\n'
                        '        for (int n : arr) System.out.print(n + " ");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 1,
            },
            {
                'title': 'Merge Sort',
                'content': (
                    'Merge sort is a divide-and-conquer algorithm. It splits the array in half, '
                    'recursively sorts each half, then merges the two sorted halves back together.\n\n'
                    'The merge step is the key: compare the front of each half and pick the smaller element repeatedly '
                    'until both halves are exhausted.\n\n'
                    'Time complexity: O(n log n) — guaranteed in all cases. '
                    'Space complexity: O(n) — needs extra memory for the merge step. '
                    'Merge sort is stable and the same algorithm works identically in all three languages.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'void merge(int arr[], int l, int m, int r) {\n'
                        '    int n1 = m - l + 1, n2 = r - m;\n'
                        '    int L[n1], R[n2];\n'
                        '    for (int i = 0; i < n1; i++) L[i] = arr[l + i];\n'
                        '    for (int j = 0; j < n2; j++) R[j] = arr[m + 1 + j];\n'
                        '    int i = 0, j = 0, k = l;\n'
                        '    while (i < n1 && j < n2)\n'
                        '        arr[k++] = (L[i] <= R[j]) ? L[i++] : R[j++];\n'
                        '    while (i < n1) arr[k++] = L[i++];\n'
                        '    while (j < n2) arr[k++] = R[j++];\n'
                        '}\n\n'
                        'void mergeSort(int arr[], int l, int r) {\n'
                        '    if (l < r) {\n'
                        '        int m = (l + r) / 2;\n'
                        '        mergeSort(arr, l, m);\n'
                        '        mergeSort(arr, m + 1, r);\n'
                        '        merge(arr, l, m, r);\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int arr[] = {12, 11, 13, 5, 6, 7};\n'
                        '    mergeSort(arr, 0, 5);\n'
                        '    for (int i = 0; i < 6; i++) printf("%d ", arr[i]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def merge_sort(arr):\n'
                        '    if len(arr) <= 1:\n'
                        '        return arr\n'
                        '    mid = len(arr) // 2\n'
                        '    left = merge_sort(arr[:mid])\n'
                        '    right = merge_sort(arr[mid:])\n'
                        '    return merge(left, right)\n\n'
                        'def merge(left, right):\n'
                        '    result, i, j = [], 0, 0\n'
                        '    while i < len(left) and j < len(right):\n'
                        '        if left[i] <= right[j]:\n'
                        '            result.append(left[i]); i += 1\n'
                        '        else:\n'
                        '            result.append(right[j]); j += 1\n'
                        '    return result + left[i:] + right[j:]\n\n'
                        'arr = [12, 11, 13, 5, 6, 7]\n'
                        'print(merge_sort(arr))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static void merge(int[] arr, int l, int m, int r) {\n'
                        '        int n1 = m - l + 1, n2 = r - m;\n'
                        '        int[] L = new int[n1], R = new int[n2];\n'
                        '        for (int i = 0; i < n1; i++) L[i] = arr[l + i];\n'
                        '        for (int j = 0; j < n2; j++) R[j] = arr[m + 1 + j];\n'
                        '        int i = 0, j = 0, k = l;\n'
                        '        while (i < n1 && j < n2)\n'
                        '            arr[k++] = (L[i] <= R[j]) ? L[i++] : R[j++];\n'
                        '        while (i < n1) arr[k++] = L[i++];\n'
                        '        while (j < n2) arr[k++] = R[j++];\n'
                        '    }\n\n'
                        '    static void mergeSort(int[] arr, int l, int r) {\n'
                        '        if (l < r) {\n'
                        '            int m = (l + r) / 2;\n'
                        '            mergeSort(arr, l, m);\n'
                        '            mergeSort(arr, m + 1, r);\n'
                        '            merge(arr, l, m, r);\n'
                        '        }\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] arr = {12, 11, 13, 5, 6, 7};\n'
                        '        mergeSort(arr, 0, arr.length - 1);\n'
                        '        for (int n : arr) System.out.print(n + " ");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Quick Sort',
                'content': (
                    'Quick sort picks a pivot element and partitions the array so that all elements less than the pivot '
                    'come before it, and all greater elements come after. It then recursively sorts both halves.\n\n'
                    'Time complexity: O(n log n) average, O(n²) worst case (bad pivot choice). '
                    'Space complexity: O(log n) — sorts in-place with only the call stack.\n\n'
                    'QuickSort is typically the fastest sorting algorithm in practice because of excellent cache performance. '
                    'Python and Java both use a variant of QuickSort internally in their built-in sort functions.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int partition(int arr[], int low, int high) {\n'
                        '    int pivot = arr[high], i = low - 1;\n'
                        '    for (int j = low; j < high; j++) {\n'
                        '        if (arr[j] <= pivot) {\n'
                        '            i++;\n'
                        '            int t = arr[i]; arr[i] = arr[j]; arr[j] = t;\n'
                        '        }\n'
                        '    }\n'
                        '    int t = arr[i+1]; arr[i+1] = arr[high]; arr[high] = t;\n'
                        '    return i + 1;\n'
                        '}\n\n'
                        'void quickSort(int arr[], int low, int high) {\n'
                        '    if (low < high) {\n'
                        '        int pi = partition(arr, low, high);\n'
                        '        quickSort(arr, low, pi - 1);\n'
                        '        quickSort(arr, pi + 1, high);\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int arr[] = {10, 7, 8, 9, 1, 5};\n'
                        '    quickSort(arr, 0, 5);\n'
                        '    for (int i = 0; i < 6; i++) printf("%d ", arr[i]);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        '# Python quicksort using list comprehensions\n'
                        'def quick_sort(arr):\n'
                        '    if len(arr) <= 1:\n'
                        '        return arr\n'
                        '    pivot = arr[len(arr) // 2]\n'
                        '    left   = [x for x in arr if x < pivot]\n'
                        '    middle = [x for x in arr if x == pivot]\n'
                        '    right  = [x for x in arr if x > pivot]\n'
                        '    return quick_sort(left) + middle + quick_sort(right)\n\n'
                        'arr = [10, 7, 8, 9, 1, 5]\n'
                        'print(quick_sort(arr))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int partition(int[] arr, int low, int high) {\n'
                        '        int pivot = arr[high], i = low - 1;\n'
                        '        for (int j = low; j < high; j++) {\n'
                        '            if (arr[j] <= pivot) {\n'
                        '                i++;\n'
                        '                int t = arr[i]; arr[i] = arr[j]; arr[j] = t;\n'
                        '            }\n'
                        '        }\n'
                        '        int t = arr[i+1]; arr[i+1] = arr[high]; arr[high] = t;\n'
                        '        return i + 1;\n'
                        '    }\n\n'
                        '    static void quickSort(int[] arr, int low, int high) {\n'
                        '        if (low < high) {\n'
                        '            int pi = partition(arr, low, high);\n'
                        '            quickSort(arr, low, pi - 1);\n'
                        '            quickSort(arr, pi + 1, high);\n'
                        '        }\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] arr = {10, 7, 8, 9, 1, 5};\n'
                        '        quickSort(arr, 0, arr.length - 1);\n'
                        '        for (int n : arr) System.out.print(n + " ");\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Comparing Sorting Algorithms',
                'content': (
                    'Now that you know the main sorting algorithms, here is how they compare:\n\n'
                    '| Algorithm | Best | Average | Worst | Space | Stable |\n'
                    '| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |\n'
                    '| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |\n'
                    '| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |\n'
                    '| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |\n'
                    '| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |\n\n'
                    'Practical advice:\n\n'
                    '- For small arrays (< 20 elements): insertion sort wins due to low overhead\n'
                    '- For guaranteed O(n log n): use merge sort\n'
                    '- For best average performance: use quicksort (most standard libraries use it)\n'
                    '- Python sorted() and Java Arrays.sort() use TimSort — a hybrid of merge sort and insertion sort'
                ),
                'example_code': '',
                'order': 4,
            },
        ],
    },

    # ── Module 8: Dynamic Programming (advanced) ─────────────────────────
    {
        'meta': {
            'title': 'Dynamic Programming',
            'description': 'Solve complex problems by breaking them into overlapping subproblems. Covers memoization, tabulation, coin change, LCS, and the knapsack problem.',
            'difficulty': 'advanced',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'What is Dynamic Programming?',
                'content': (
                    'Dynamic programming (DP) solves a complex problem by breaking it into simpler overlapping subproblems, '
                    'solving each subproblem once, and storing the results to avoid redundant computation.\n\n'
                    'DP applies when a problem has two properties:\n\n'
                    '1. Optimal substructure — the optimal solution can be built from optimal solutions to subproblems\n'
                    '2. Overlapping subproblems — the same subproblems recur many times\n\n'
                    'There are two approaches:\n\n'
                    '- Memoization (top-down): write the natural recursive solution, then cache results in a lookup table\n'
                    '- Tabulation (bottom-up): fill a table iteratively starting from the smallest subproblems\n\n'
                    'Both approaches give the same answer. Tabulation is usually faster (no recursion overhead). '
                    'Memoization is often easier to write from a recursive intuition.'
                ),
                'example_code': '',
                'order': 1,
            },
            {
                'title': 'Memoization — Fibonacci Revisited',
                'content': (
                    'The naive recursive Fibonacci recalculates the same values exponentially many times. '
                    'Memoization fixes this by caching every result the first time it is computed.\n\n'
                    'With memoization, fibonacci(40) that would require billions of calls with naive recursion '
                    'now takes exactly 40 unique calls. Time complexity drops from O(2^n) to O(n).\n\n'
                    'C uses an array for the cache. Python has @lru_cache which does it automatically. '
                    'Java uses a HashMap.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int memo[100];\n\n'
                        'int fibonacci(int n) {\n'
                        '    if (n <= 1) return n;\n'
                        '    if (memo[n] != -1) return memo[n];\n'
                        '    memo[n] = fibonacci(n - 1) + fibonacci(n - 2);\n'
                        '    return memo[n];\n'
                        '}\n\n'
                        'int main() {\n'
                        '    memset(memo, -1, sizeof(memo));\n'
                        '    for (int i = 0; i < 10; i++) printf("%d ", fibonacci(i));\n'
                        '    printf("\\nfib(40) = %d\\n", fibonacci(40));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'from functools import lru_cache\n\n'
                        '@lru_cache(maxsize=None)\n'
                        'def fibonacci(n):\n'
                        '    if n <= 1:\n'
                        '        return n\n'
                        '    return fibonacci(n - 1) + fibonacci(n - 2)\n\n'
                        'for i in range(10):\n'
                        '    print(fibonacci(i), end=" ")\n'
                        'print()\n'
                        'print("fib(40) =", fibonacci(40))'
                    ),
                    'java': (
                        'import java.util.HashMap;\n\n'
                        'public class Main {\n'
                        '    static HashMap<Integer, Integer> memo = new HashMap<>();\n\n'
                        '    static int fibonacci(int n) {\n'
                        '        if (n <= 1) return n;\n'
                        '        if (memo.containsKey(n)) return memo.get(n);\n'
                        '        int result = fibonacci(n - 1) + fibonacci(n - 2);\n'
                        '        memo.put(n, result);\n'
                        '        return result;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        for (int i = 0; i < 10; i++) System.out.print(fibonacci(i) + " ");\n'
                        '        System.out.println("\\nfib(40) = " + fibonacci(40));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Coin Change — Minimum Coins',
                'content': (
                    'Given a set of coin denominations and a target amount, find the minimum number of coins needed.\n\n'
                    'DP approach: build a table dp where dp[i] = minimum coins needed for amount i. '
                    'For each amount i, try every coin: if the coin fits (coin <= i), '
                    'then dp[i] = min(dp[i], dp[i - coin] + 1).\n\n'
                    'The key insight: dp[i - coin] gives the minimum coins needed for the remaining amount, '
                    'and adding 1 accounts for the current coin. We want the choice that minimises the total.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <limits.h>\n\n'
                        'int coinChange(int coins[], int n, int amount) {\n'
                        '    int dp[amount + 1];\n'
                        '    dp[0] = 0;\n'
                        '    for (int i = 1; i <= amount; i++) dp[i] = INT_MAX;\n'
                        '    for (int i = 1; i <= amount; i++) {\n'
                        '        for (int j = 0; j < n; j++) {\n'
                        '            if (coins[j] <= i && dp[i - coins[j]] != INT_MAX)\n'
                        '                if (dp[i - coins[j]] + 1 < dp[i])\n'
                        '                    dp[i] = dp[i - coins[j]] + 1;\n'
                        '        }\n'
                        '    }\n'
                        '    return dp[amount] == INT_MAX ? -1 : dp[amount];\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int coins[] = {1, 5, 10, 25};\n'
                        '    printf("Min coins for 30: %d\\n", coinChange(coins, 4, 30));\n'
                        '    printf("Min coins for 11: %d\\n", coinChange(coins, 4, 11));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def coin_change(coins, amount):\n'
                        '    dp = [float("inf")] * (amount + 1)\n'
                        '    dp[0] = 0\n'
                        '    for i in range(1, amount + 1):\n'
                        '        for coin in coins:\n'
                        '            if coin <= i and dp[i - coin] + 1 < dp[i]:\n'
                        '                dp[i] = dp[i - coin] + 1\n'
                        '    return dp[amount] if dp[amount] != float("inf") else -1\n\n'
                        'coins = [1, 5, 10, 25]\n'
                        'print("Min coins for 30:", coin_change(coins, 30))\n'
                        'print("Min coins for 11:", coin_change(coins, 11))'
                    ),
                    'java': (
                        'import java.util.Arrays;\n\n'
                        'public class Main {\n'
                        '    static int coinChange(int[] coins, int amount) {\n'
                        '        int[] dp = new int[amount + 1];\n'
                        '        Arrays.fill(dp, Integer.MAX_VALUE);\n'
                        '        dp[0] = 0;\n'
                        '        for (int i = 1; i <= amount; i++)\n'
                        '            for (int coin : coins)\n'
                        '                if (coin <= i && dp[i - coin] != Integer.MAX_VALUE)\n'
                        '                    dp[i] = Math.min(dp[i], dp[i - coin] + 1);\n'
                        '        return dp[amount] == Integer.MAX_VALUE ? -1 : dp[amount];\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] coins = {1, 5, 10, 25};\n'
                        '        System.out.println("Min coins for 30: " + coinChange(coins, 30));\n'
                        '        System.out.println("Min coins for 11: " + coinChange(coins, 11));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Longest Common Subsequence',
                'content': (
                    'Given two strings, find the length of their longest common subsequence (LCS). '
                    'A subsequence does not need to be contiguous — characters just need to appear in the same order.\n\n'
                    'Example: LCS of "ABCBDAB" and "BDCABA" is "BCBA" (length 4).\n\n'
                    'DP approach: build a 2D table dp[i][j] = LCS length of the first i characters of s1 and first j of s2. '
                    'If s1[i] == s2[j], extend the previous diagonal: dp[i][j] = dp[i-1][j-1] + 1. '
                    'Otherwise take the max of left and above: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        'int lcs(char *s1, char *s2) {\n'
                        '    int m = strlen(s1), n = strlen(s2);\n'
                        '    int dp[m + 1][n + 1];\n'
                        '    for (int i = 0; i <= m; i++) {\n'
                        '        for (int j = 0; j <= n; j++) {\n'
                        '            if (i == 0 || j == 0) dp[i][j] = 0;\n'
                        '            else if (s1[i-1] == s2[j-1]) dp[i][j] = dp[i-1][j-1] + 1;\n'
                        '            else dp[i][j] = dp[i-1][j] > dp[i][j-1] ? dp[i-1][j] : dp[i][j-1];\n'
                        '        }\n'
                        '    }\n'
                        '    return dp[m][n];\n'
                        '}\n\n'
                        'int main() {\n'
                        '    printf("LCS of ABCBDAB and BDCABA: %d\\n", lcs("ABCBDAB", "BDCABA"));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def lcs(s1, s2):\n'
                        '    m, n = len(s1), len(s2)\n'
                        '    dp = [[0] * (n + 1) for _ in range(m + 1)]\n'
                        '    for i in range(1, m + 1):\n'
                        '        for j in range(1, n + 1):\n'
                        '            if s1[i-1] == s2[j-1]:\n'
                        '                dp[i][j] = dp[i-1][j-1] + 1\n'
                        '            else:\n'
                        '                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n'
                        '    return dp[m][n]\n\n'
                        'print("LCS of ABCBDAB and BDCABA:", lcs("ABCBDAB", "BDCABA"))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int lcs(String s1, String s2) {\n'
                        '        int m = s1.length(), n = s2.length();\n'
                        '        int[][] dp = new int[m + 1][n + 1];\n'
                        '        for (int i = 1; i <= m; i++)\n'
                        '            for (int j = 1; j <= n; j++)\n'
                        '                if (s1.charAt(i-1) == s2.charAt(j-1))\n'
                        '                    dp[i][j] = dp[i-1][j-1] + 1;\n'
                        '                else\n'
                        '                    dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);\n'
                        '        return dp[m][n];\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        System.out.println("LCS of ABCBDAB and BDCABA: " + lcs("ABCBDAB", "BDCABA"));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': '0/1 Knapsack',
                'content': (
                    'You have a knapsack that can carry at most W weight. '
                    'You have n items, each with a weight and a value. '
                    'You can either take an item (1) or leave it (0) — you cannot take a fraction. '
                    'Maximise the total value without exceeding W.\n\n'
                    'DP approach: dp[i][w] = maximum value using the first i items with capacity w. '
                    'For each item i at each capacity w:\n\n'
                    '- If item i is too heavy: dp[i][w] = dp[i-1][w] (skip it)\n'
                    '- Otherwise: dp[i][w] = max(skip it, take it) = max(dp[i-1][w], value[i] + dp[i-1][w - weight[i]])'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        'int max(int a, int b) { return a > b ? a : b; }\n\n'
                        'int knapsack(int W, int wt[], int val[], int n) {\n'
                        '    int dp[n + 1][W + 1];\n'
                        '    for (int i = 0; i <= n; i++) {\n'
                        '        for (int w = 0; w <= W; w++) {\n'
                        '            if (i == 0 || w == 0) dp[i][w] = 0;\n'
                        '            else if (wt[i-1] <= w)\n'
                        '                dp[i][w] = max(val[i-1] + dp[i-1][w - wt[i-1]], dp[i-1][w]);\n'
                        '            else\n'
                        '                dp[i][w] = dp[i-1][w];\n'
                        '        }\n'
                        '    }\n'
                        '    return dp[n][W];\n'
                        '}\n\n'
                        'int main() {\n'
                        '    int weights[] = {2, 3, 4, 5};\n'
                        '    int values[]  = {3, 4, 5, 6};\n'
                        '    printf("Max value (W=8): %d\\n", knapsack(8, weights, values, 4));\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def knapsack(W, weights, values):\n'
                        '    n = len(weights)\n'
                        '    dp = [[0] * (W + 1) for _ in range(n + 1)]\n'
                        '    for i in range(1, n + 1):\n'
                        '        for w in range(W + 1):\n'
                        '            if weights[i-1] <= w:\n'
                        '                dp[i][w] = max(values[i-1] + dp[i-1][w - weights[i-1]],\n'
                        '                               dp[i-1][w])\n'
                        '            else:\n'
                        '                dp[i][w] = dp[i-1][w]\n'
                        '    return dp[n][W]\n\n'
                        'weights = [2, 3, 4, 5]\n'
                        'values  = [3, 4, 5, 6]\n'
                        'print("Max value (W=8):", knapsack(8, weights, values))'
                    ),
                    'java': (
                        'public class Main {\n'
                        '    static int knapsack(int W, int[] wt, int[] val, int n) {\n'
                        '        int[][] dp = new int[n + 1][W + 1];\n'
                        '        for (int i = 1; i <= n; i++)\n'
                        '            for (int w = 0; w <= W; w++)\n'
                        '                if (wt[i-1] <= w)\n'
                        '                    dp[i][w] = Math.max(val[i-1] + dp[i-1][w - wt[i-1]], dp[i-1][w]);\n'
                        '                else\n'
                        '                    dp[i][w] = dp[i-1][w];\n'
                        '        return dp[n][W];\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        int[] weights = {2, 3, 4, 5};\n'
                        '        int[] values  = {3, 4, 5, 6};\n'
                        '        System.out.println("Max value (W=8): " + knapsack(8, weights, values, 4));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
        ],
    },

    # ── Module 9: Graph Algorithms (advanced) ────────────────────────────
    {
        'meta': {
            'title': 'Graph Algorithms',
            'description': 'Understand graphs, BFS, DFS, and Dijkstra\'s shortest path. Essential knowledge for networks, maps, social graphs, and more.',
            'difficulty': 'advanced',
            'language': 'general',
        },
        'lessons': [
            {
                'title': 'What are Graphs?',
                'content': (
                    'A graph is a set of nodes (vertices) connected by edges. Graphs model networks of all kinds:\n\n'
                    '- Road maps (cities = nodes, roads = edges)\n'
                    '- Social networks (people = nodes, friendships = edges)\n'
                    '- Web pages (pages = nodes, hyperlinks = edges)\n'
                    '- Computer networks (computers = nodes, connections = edges)\n\n'
                    'Key terms:\n\n'
                    '- Directed graph: edges have a direction (A → B does not imply B → A)\n'
                    '- Undirected graph: edges go both ways (A — B means A → B and B → A)\n'
                    '- Weighted graph: edges have a cost or distance value\n'
                    '- Path: a sequence of nodes connected by edges\n'
                    '- Cycle: a path that starts and ends at the same node'
                ),
                'example_code': '',
                'order': 1,
            },
            {
                'title': 'Representing Graphs',
                'content': (
                    'There are two common ways to represent a graph in code:\n\n'
                    '- Adjacency matrix: a 2D grid where cell [i][j] = 1 if there is an edge from i to j. '
                    'Fast edge lookup O(1) but uses O(n²) memory even for sparse graphs.\n\n'
                    '- Adjacency list: each node stores a list of its neighbours. '
                    'Memory-efficient for sparse graphs O(n + e) and faster for traversal.\n\n'
                    'Most algorithm problems use adjacency lists. The example below builds the same graph both ways.'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n\n'
                        '// Adjacency matrix for a 5-node undirected graph\n'
                        '#define N 5\n'
                        'int matrix[N][N] = {\n'
                        '    {0,1,1,0,0},\n'
                        '    {1,0,0,1,1},\n'
                        '    {1,0,0,0,0},\n'
                        '    {0,1,0,0,1},\n'
                        '    {0,1,0,1,0}\n'
                        '};\n\n'
                        'int main() {\n'
                        '    printf("Neighbours of node 1: ");\n'
                        '    for (int i = 0; i < N; i++)\n'
                        '        if (matrix[1][i]) printf("%d ", i);\n'
                        '    printf("\\n");\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        '# Adjacency list using a dictionary\n'
                        'graph = {\n'
                        '    0: [1, 2],\n'
                        '    1: [0, 3, 4],\n'
                        '    2: [0],\n'
                        '    3: [1, 4],\n'
                        '    4: [1, 3]\n'
                        '}\n\n'
                        'print("Neighbours of node 1:", graph[1])\n'
                        'print("Number of edges:", sum(len(v) for v in graph.values()) // 2)'
                    ),
                    'java': (
                        'import java.util.*;\n\n'
                        'public class Main {\n'
                        '    public static void main(String[] args) {\n'
                        '        // Adjacency list\n'
                        '        Map<Integer, List<Integer>> graph = new HashMap<>();\n'
                        '        graph.put(0, Arrays.asList(1, 2));\n'
                        '        graph.put(1, Arrays.asList(0, 3, 4));\n'
                        '        graph.put(2, Arrays.asList(0));\n'
                        '        graph.put(3, Arrays.asList(1, 4));\n'
                        '        graph.put(4, Arrays.asList(1, 3));\n\n'
                        '        System.out.println("Neighbours of node 1: " + graph.get(1));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 2,
            },
            {
                'title': 'Breadth-First Search (BFS)',
                'content': (
                    'BFS explores a graph level by level — first all nodes at distance 1 from the start, '
                    'then all nodes at distance 2, and so on. It uses a queue.\n\n'
                    'BFS guarantees the shortest path in an unweighted graph. '
                    'Time complexity: O(V + E) where V = vertices and E = edges.\n\n'
                    'Algorithm:\n\n'
                    '1. Enqueue the start node and mark it visited\n'
                    '2. While the queue is not empty: dequeue a node, process it, enqueue all unvisited neighbours'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        '#define N 6\n'
                        'int graph[N][N] = {\n'
                        '    {0,1,1,0,0,0},\n'
                        '    {1,0,0,1,1,0},\n'
                        '    {1,0,0,0,0,1},\n'
                        '    {0,1,0,0,0,0},\n'
                        '    {0,1,0,0,0,0},\n'
                        '    {0,0,1,0,0,0}\n'
                        '};\n\n'
                        'void bfs(int start) {\n'
                        '    int visited[N] = {0};\n'
                        '    int queue[N], front = 0, rear = 0;\n'
                        '    visited[start] = 1;\n'
                        '    queue[rear++] = start;\n'
                        '    while (front < rear) {\n'
                        '        int node = queue[front++];\n'
                        '        printf("%d ", node);\n'
                        '        for (int i = 0; i < N; i++)\n'
                        '            if (graph[node][i] && !visited[i]) {\n'
                        '                visited[i] = 1;\n'
                        '                queue[rear++] = i;\n'
                        '            }\n'
                        '    }\n'
                        '}\n\n'
                        'int main() {\n'
                        '    printf("BFS from 0: ");\n'
                        '    bfs(0);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'from collections import deque\n\n'
                        'def bfs(graph, start):\n'
                        '    visited = {start}\n'
                        '    queue = deque([start])\n'
                        '    order = []\n'
                        '    while queue:\n'
                        '        node = queue.popleft()\n'
                        '        order.append(node)\n'
                        '        for neighbour in graph[node]:\n'
                        '            if neighbour not in visited:\n'
                        '                visited.add(neighbour)\n'
                        '                queue.append(neighbour)\n'
                        '    return order\n\n'
                        'graph = {0:[1,2], 1:[0,3,4], 2:[0,5], 3:[1], 4:[1], 5:[2]}\n'
                        'print("BFS from 0:", bfs(graph, 0))'
                    ),
                    'java': (
                        'import java.util.*;\n\n'
                        'public class Main {\n'
                        '    static List<Integer> bfs(Map<Integer, List<Integer>> graph, int start) {\n'
                        '        Set<Integer> visited = new HashSet<>();\n'
                        '        Queue<Integer> queue = new LinkedList<>();\n'
                        '        List<Integer> order = new ArrayList<>();\n'
                        '        queue.add(start); visited.add(start);\n'
                        '        while (!queue.isEmpty()) {\n'
                        '            int node = queue.poll();\n'
                        '            order.add(node);\n'
                        '            for (int nb : graph.get(node))\n'
                        '                if (!visited.contains(nb)) { visited.add(nb); queue.add(nb); }\n'
                        '        }\n'
                        '        return order;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        Map<Integer, List<Integer>> graph = new HashMap<>();\n'
                        '        graph.put(0, Arrays.asList(1,2)); graph.put(1, Arrays.asList(0,3,4));\n'
                        '        graph.put(2, Arrays.asList(0,5)); graph.put(3, Arrays.asList(1));\n'
                        '        graph.put(4, Arrays.asList(1));   graph.put(5, Arrays.asList(2));\n'
                        '        System.out.println("BFS from 0: " + bfs(graph, 0));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 3,
            },
            {
                'title': 'Depth-First Search (DFS)',
                'content': (
                    'DFS explores as far as possible down one path before backtracking. '
                    'It uses a stack — either explicitly, or implicitly through recursion.\n\n'
                    'DFS is useful for: detecting cycles, topological sorting, finding connected components, '
                    'and solving maze/puzzle problems.\n\n'
                    'Time complexity: O(V + E). Unlike BFS, DFS does not guarantee the shortest path.\n\n'
                    'Algorithm (recursive):\n\n'
                    '1. Mark the current node visited and process it\n'
                    '2. For each unvisited neighbour, recursively call DFS'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <string.h>\n\n'
                        '#define N 6\n'
                        'int graph[N][N] = {\n'
                        '    {0,1,1,0,0,0},\n'
                        '    {1,0,0,1,1,0},\n'
                        '    {1,0,0,0,0,1},\n'
                        '    {0,1,0,0,0,0},\n'
                        '    {0,1,0,0,0,0},\n'
                        '    {0,0,1,0,0,0}\n'
                        '};\n'
                        'int visited[N];\n\n'
                        'void dfs(int node) {\n'
                        '    visited[node] = 1;\n'
                        '    printf("%d ", node);\n'
                        '    for (int i = 0; i < N; i++)\n'
                        '        if (graph[node][i] && !visited[i])\n'
                        '            dfs(i);\n'
                        '}\n\n'
                        'int main() {\n'
                        '    memset(visited, 0, sizeof(visited));\n'
                        '    printf("DFS from 0: ");\n'
                        '    dfs(0);\n'
                        '    return 0;\n'
                        '}'
                    ),
                    'python': (
                        'def dfs(graph, node, visited=None, order=None):\n'
                        '    if visited is None:\n'
                        '        visited, order = set(), []\n'
                        '    visited.add(node)\n'
                        '    order.append(node)\n'
                        '    for neighbour in graph[node]:\n'
                        '        if neighbour not in visited:\n'
                        '            dfs(graph, neighbour, visited, order)\n'
                        '    return order\n\n'
                        'graph = {0:[1,2], 1:[0,3,4], 2:[0,5], 3:[1], 4:[1], 5:[2]}\n'
                        'print("DFS from 0:", dfs(graph, 0))'
                    ),
                    'java': (
                        'import java.util.*;\n\n'
                        'public class Main {\n'
                        '    static void dfsHelper(Map<Integer,List<Integer>> g, int node,\n'
                        '                          Set<Integer> visited, List<Integer> order) {\n'
                        '        visited.add(node);\n'
                        '        order.add(node);\n'
                        '        for (int nb : g.get(node))\n'
                        '            if (!visited.contains(nb))\n'
                        '                dfsHelper(g, nb, visited, order);\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        Map<Integer, List<Integer>> graph = new HashMap<>();\n'
                        '        graph.put(0, Arrays.asList(1,2)); graph.put(1, Arrays.asList(0,3,4));\n'
                        '        graph.put(2, Arrays.asList(0,5)); graph.put(3, Arrays.asList(1));\n'
                        '        graph.put(4, Arrays.asList(1));   graph.put(5, Arrays.asList(2));\n'
                        '        Set<Integer> visited = new HashSet<>();\n'
                        '        List<Integer> order = new ArrayList<>();\n'
                        '        dfsHelper(graph, 0, visited, order);\n'
                        '        System.out.println("DFS from 0: " + order);\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 4,
            },
            {
                'title': "Dijkstra's Shortest Path",
                'content': (
                    "Dijkstra's algorithm finds the shortest path from a source node to all other nodes "
                    'in a weighted graph (with non-negative weights).\n\n'
                    'It uses a priority queue (min-heap) to always process the closest unvisited node next:\n\n'
                    '1. Set all distances to infinity except the source (distance 0)\n'
                    '2. Add source to the priority queue\n'
                    '3. While the queue is not empty: extract the minimum-distance node, '
                    'update distances to its neighbours if a shorter path is found\n\n'
                    'Time complexity: O((V + E) log V) with a binary heap. '
                    'This algorithm is used in GPS navigation, network routing, and game pathfinding (A* is an extension).'
                ),
                'example_code': json.dumps({
                    'c': (
                        '#include <stdio.h>\n'
                        '#include <limits.h>\n\n'
                        '#define N 5\n'
                        '// Weighted adjacency matrix (0 = no edge)\n'
                        'int graph[N][N] = {\n'
                        '    {0, 4, 1, 0, 0},\n'
                        '    {4, 0, 0, 1, 0},\n'
                        '    {1, 0, 0, 5, 0},\n'
                        '    {0, 1, 5, 0, 3},\n'
                        '    {0, 0, 0, 3, 0}\n'
                        '};\n\n'
                        'void dijkstra(int src) {\n'
                        '    int dist[N], visited[N] = {0};\n'
                        '    for (int i = 0; i < N; i++) dist[i] = INT_MAX;\n'
                        '    dist[src] = 0;\n'
                        '    for (int count = 0; count < N - 1; count++) {\n'
                        '        // pick minimum distance unvisited node\n'
                        '        int u = -1;\n'
                        '        for (int v = 0; v < N; v++)\n'
                        '            if (!visited[v] && (u == -1 || dist[v] < dist[u])) u = v;\n'
                        '        visited[u] = 1;\n'
                        '        for (int v = 0; v < N; v++)\n'
                        '            if (graph[u][v] && !visited[v] && dist[u] + graph[u][v] < dist[v])\n'
                        '                dist[v] = dist[u] + graph[u][v];\n'
                        '    }\n'
                        '    printf("Distances from node %d:\\n", src);\n'
                        '    for (int i = 0; i < N; i++) printf("  -> %d: %d\\n", i, dist[i]);\n'
                        '}\n\n'
                        'int main() { dijkstra(0); return 0; }'
                    ),
                    'python': (
                        'import heapq\n\n'
                        'def dijkstra(graph, start):\n'
                        '    dist = {node: float("inf") for node in graph}\n'
                        '    dist[start] = 0\n'
                        '    heap = [(0, start)]\n'
                        '    while heap:\n'
                        '        d, node = heapq.heappop(heap)\n'
                        '        if d > dist[node]:\n'
                        '            continue\n'
                        '        for neighbour, weight in graph[node]:\n'
                        '            new_dist = dist[node] + weight\n'
                        '            if new_dist < dist[neighbour]:\n'
                        '                dist[neighbour] = new_dist\n'
                        '                heapq.heappush(heap, (new_dist, neighbour))\n'
                        '    return dist\n\n'
                        '# (neighbour, weight) adjacency list\n'
                        'graph = {\n'
                        '    0: [(1, 4), (2, 1)],\n'
                        '    1: [(0, 4), (3, 1)],\n'
                        '    2: [(0, 1), (3, 5)],\n'
                        '    3: [(1, 1), (2, 5), (4, 3)],\n'
                        '    4: [(3, 3)]\n'
                        '}\n'
                        'print("Distances from 0:", dijkstra(graph, 0))'
                    ),
                    'java': (
                        'import java.util.*;\n\n'
                        'public class Main {\n'
                        '    static Map<Integer, Integer> dijkstra(\n'
                        '            Map<Integer, List<int[]>> graph, int start) {\n'
                        '        Map<Integer, Integer> dist = new HashMap<>();\n'
                        '        for (int node : graph.keySet()) dist.put(node, Integer.MAX_VALUE);\n'
                        '        dist.put(start, 0);\n'
                        '        // PriorityQueue: [distance, node]\n'
                        '        PriorityQueue<int[]> heap = new PriorityQueue<>(Comparator.comparingInt(a -> a[0]));\n'
                        '        heap.offer(new int[]{0, start});\n'
                        '        while (!heap.isEmpty()) {\n'
                        '            int[] top = heap.poll();\n'
                        '            int d = top[0], node = top[1];\n'
                        '            if (d > dist.get(node)) continue;\n'
                        '            for (int[] edge : graph.get(node)) {\n'
                        '                int nb = edge[0], w = edge[1];\n'
                        '                int newDist = dist.get(node) + w;\n'
                        '                if (newDist < dist.get(nb)) {\n'
                        '                    dist.put(nb, newDist);\n'
                        '                    heap.offer(new int[]{newDist, nb});\n'
                        '                }\n'
                        '            }\n'
                        '        }\n'
                        '        return dist;\n'
                        '    }\n\n'
                        '    public static void main(String[] args) {\n'
                        '        Map<Integer, List<int[]>> graph = new HashMap<>();\n'
                        '        graph.put(0, Arrays.asList(new int[]{1,4}, new int[]{2,1}));\n'
                        '        graph.put(1, Arrays.asList(new int[]{0,4}, new int[]{3,1}));\n'
                        '        graph.put(2, Arrays.asList(new int[]{0,1}, new int[]{3,5}));\n'
                        '        graph.put(3, Arrays.asList(new int[]{1,1}, new int[]{2,5}, new int[]{4,3}));\n'
                        '        graph.put(4, Arrays.asList(new int[]{3,3}));\n'
                        '        System.out.println("Distances from 0: " + dijkstra(graph, 0));\n'
                        '    }\n'
                        '}'
                    ),
                }),
                'order': 5,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed advanced algorithm modules: Advanced Sorting, Dynamic Programming, Graph Algorithms'

    def handle(self, *args, **options):
        titles = [m['meta']['title'] for m in MODULES]
        LearningModule.objects.filter(title__in=titles).delete()

        for module_data in MODULES:
            module = LearningModule.objects.create(**module_data['meta'])
            for lesson_data in module_data['lessons']:
                Lesson.objects.create(module=module, **lesson_data)
            self.stdout.write(
                f'  Created "{module.title}" '
                f'({len(module_data["lessons"])} lessons, {module.difficulty})'
            )

        total_lessons = sum(len(m['lessons']) for m in MODULES)
        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(MODULES)} modules created with {total_lessons} total lessons.'
        ))
