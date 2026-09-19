"""Clean control code: zero vulnerabilities and zero code smells."""

from typing import List


def calculate_average(values: List[float]) -> float:
    """Calculates arithmetic mean of non-empty sequence."""
    if not values:
        return 0.0
    return sum(values) / len(values)


class Greeter:
    def __init__(self, greeting: str = "Hello") -> None:
        self.greeting = greeting

    def greet(self, name: str) -> str:
        return f"{self.greeting}, {name}!"
