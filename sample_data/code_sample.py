"""
Fibonacci Sequence Generator
A sample Python script for Smart File Organizer demo.
"""


def fibonacci(n: int) -> list[int]:
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]

    sequence = [0, 1]
    for _ in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


if __name__ == "__main__":
    count = 15
    result = fibonacci(count)
    print(f"First {count} Fibonacci numbers:")
    print(result)
