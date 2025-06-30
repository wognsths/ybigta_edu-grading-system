from abc import ABC, abstractmethod
from typing import Any

class BaseGrader(ABC):
    def __init__(self, student_module: Any):
        self.student_module = student_module

    @abstractmethod
    def run_tests(self) -> dict:
        pass