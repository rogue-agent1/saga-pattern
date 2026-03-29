#!/usr/bin/env python3
"""Saga pattern for distributed transaction management."""
import sys

class SagaStep:
    def __init__(self, name, action, compensate):
        self.name = name
        self.action = action
        self.compensate = compensate

class Saga:
    def __init__(self, name):
        self.name = name
        self.steps = []
        self.completed = []
        self.log = []
    def add_step(self, name, action, compensate):
        self.steps.append(SagaStep(name, action, compensate))
    def execute(self, context):
        for step in self.steps:
            try:
                self.log.append(f"executing: {step.name}")
                step.action(context)
                self.completed.append(step)
                self.log.append(f"completed: {step.name}")
            except Exception as e:
                self.log.append(f"failed: {step.name} ({e})")
                self._compensate(context)
                return False, str(e)
        return True, None
    def _compensate(self, context):
        for step in reversed(self.completed):
            try:
                self.log.append(f"compensating: {step.name}")
                step.compensate(context)
            except Exception as e:
                self.log.append(f"compensate failed: {step.name} ({e})")

def test():
    ctx = {"balance": 100, "inventory": 5, "order": None}
    saga = Saga("order")
    saga.add_step("debit",
        lambda c: c.__setitem__("balance", c["balance"] - 50),
        lambda c: c.__setitem__("balance", c["balance"] + 50))
    saga.add_step("reserve",
        lambda c: c.__setitem__("inventory", c["inventory"] - 1),
        lambda c: c.__setitem__("inventory", c["inventory"] + 1))
    saga.add_step("confirm",
        lambda c: c.__setitem__("order", "confirmed"),
        lambda c: c.__setitem__("order", None))
    ok, err = saga.execute(ctx)
    assert ok and err is None
    assert ctx["balance"] == 50 and ctx["inventory"] == 4 and ctx["order"] == "confirmed"
    # Test compensation on failure
    ctx2 = {"balance": 100, "inventory": 5, "order": None}
    saga2 = Saga("fail_order")
    saga2.add_step("debit",
        lambda c: c.__setitem__("balance", c["balance"] - 50),
        lambda c: c.__setitem__("balance", c["balance"] + 50))
    def fail_reserve(c): raise RuntimeError("out of stock")
    saga2.add_step("reserve", fail_reserve,
        lambda c: c.__setitem__("inventory", c["inventory"] + 1))
    ok2, err2 = saga2.execute(ctx2)
    assert not ok2
    assert ctx2["balance"] == 100  # compensated
    print("  saga_pattern: ALL TESTS PASSED")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Saga pattern for distributed transactions")
