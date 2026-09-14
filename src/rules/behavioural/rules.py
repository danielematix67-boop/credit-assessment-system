from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus


class BehaviouralRule(Rule):
    """Shared deterministic implementation for scalar behavioural rules."""

    def evaluate(self, position):
        value, error = self._configured_value(position)
        if error is not None:
            return self._not_evaluable(error)
        assert value is not None
        status = RuleStatus.TRIGGERED if self._is_triggered(value) else RuleStatus.NOT_TRIGGERED
        return self._result(value=value, status=status)


@Rule.register("B001")
class HighCreditUtilizationRule(BehaviouralRule):
    pass


@Rule.register("B002")
class ProlongedOverdraftRule(BehaviouralRule):
    pass


@Rule.register("B003")
class PaymentDelayRule(BehaviouralRule):
    pass


@Rule.register("B004")
class ExposureGrowthRule(BehaviouralRule):
    pass
