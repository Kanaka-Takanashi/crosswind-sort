"""Run benchmarks via: python -m crosswind_sort"""

import random
import time
from ._core import crosswind_sort


def _insertion_sort(arr, lo, hi):
    for i in range(lo + 1, hi):
        key = arr[i]
        j = i - 1
        while j >= lo and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


def _quicksort(arr, lo, hi, threshold=32):
    if hi - lo < threshold:
        _insertion_sort(arr, lo, hi)
        return
    pivot = arr[hi - 1]
    i = lo
    for j in range(lo, hi - 1):
        if arr[j] < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi - 1] = arr[hi - 1], arr[i]
    _quicksort(arr, lo, i, threshold)
    _quicksort(arr, i + 1, hi, threshold)


def quicksort(arr):
    copy = arr[:]
    _quicksort(copy, 0, len(copy))
    return copy


def _sift_down(arr, start, end):
    root = start
    while True:
        child = 2 * root + 1
        if child >= end:
            break
        if child + 1 < end and arr[child] < arr[child + 1]:
            child += 1
        if arr[root] >= arr[child]:
            break
        arr[root], arr[child] = arr[child], arr[root]
        root = child


def heapsort(arr):
    copy = arr[:]
    n = len(copy)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(copy, i, n)
    for end in range(n - 1, 0, -1):
        copy[0], copy[end] = copy[end], copy[0]
        _sift_down(copy, 0, end)
    return copy


def benchmark(sizes=(1_000, 10_000, 50_000, 100_000), repeats=5):
    algorithms = [
        ("4 Crosswind", crosswind_sort),
        ("quicksort", quicksort),
        ("heapsort", heapsort),
        ("timsort", lambda a: sorted(a)),
    ]

    header = f"{'Size':>10} | " + " | ".join(f"{name:>14}" for name, _ in algorithms)
    print(header)
    print("-" * len(header))

    for size in sizes:
        base = [random.randint(0, 1_000_000) for _ in range(size)]
        times = {name: 0.0 for name, _ in algorithms}

        for _ in range(repeats):
            for name, func in algorithms:
                t0 = time.perf_counter()
                func(base[:])
                times[name] += time.perf_counter() - t0

        avg = {name: t / repeats for name, t in times.items()}
        baseline = avg["4 Crosswind"]

        row = f"{size:>10,} | "
        for name, _ in algorithms:
            speedup = baseline / avg[name]
            row += f"  {avg[name]:.4f}s {speedup:4.1f}x |"
        print(row)

    print()
    print("  Speedup relative to 4 Crosswind.  >1.0x = faster  |  <1.0x = slower")


if __name__ == "__main__":
    print("4 Crosswind Sort v1.0.0\n")

    # Correctness
    print("=== Correctness ===")
    test = [2, 27, 43, 3, 9, 82, 10, 55, 12, 99, 1, 5]
    print(f"  Input:  {test}")
    print(f"  Result: {crosswind_sort(test)}")

    for size in (0, 1, 2, 3, 4, 5, 15, 16, 100, 101):
        t = list(range(size, 0, -1))
        assert crosswind_sort(t) == sorted(t), f"Failed at size {size}"
    print("  Edge cases passed (sizes 0-101)")

    t = [5, 3, 1, 4, 2]
    crosswind_sort(t, inplace=True)
    assert t == [1, 2, 3, 4, 5], "In-place sort failed"
    print("  In-place mode works")

    big = [random.randint(0, 10_000) for _ in range(2_000)]
    assert crosswind_sort(big) == sorted(big), "Mismatch on 2000 elements"
    print("  Verified on 2,000 random elements")

    # Benchmark
    print("\n=== Benchmark: 4 Crosswind vs Classics ===\n")
    benchmark()
