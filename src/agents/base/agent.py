from abc import ABC, abstractmethod
from typing import Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(ABC, Generic[InputT, OutputT]):

    @abstractmethod
    def run(self, input_data: InputT) -> OutputT:
        pass