from abc import ABC, abstractmethod

from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


class ReportGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        pass
