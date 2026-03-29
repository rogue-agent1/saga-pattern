#!/usr/bin/env python3
"""saga_pattern - Saga pattern for distributed transaction management."""
import sys

class SagaStep:
    def __init__(self, name, execute, compensate):
        self.name = name
        self.execute = execute
        self.compensate = compensate

class Saga:
    def __init__(self, steps):
        self.steps = steps
        self.completed = []
        self.log = []
    def run(self, context=None):
        if context is None:
            context = {}
        for step in self.steps:
            try:
                self.log.append({"step": step.name, "action": "execute"})
                step.execute(context)
                self.completed.append(step)
            except Exception as e:
                self.log.append({"step": step.name, "action": "failed", "error": str(e)})
                self._compensate(context)
                return False, str(e)
        return True, None
    def _compensate(self, context):
        for step in reversed(self.completed):
            try:
                self.log.append({"step": step.name, "action": "compensate"})
                step.compensate(context)
            except Exception as e:
                self.log.append({"step": step.name, "action": "compensate_failed", "error": str(e)})

def test():
    log = []
    steps = [
        SagaStep("reserve_inventory",
                 lambda ctx: log.append("reserved"),
                 lambda ctx: log.append("unreserved")),
        SagaStep("charge_payment",
                 lambda ctx: log.append("charged"),
                 lambda ctx: log.append("refunded")),
        SagaStep("ship_order",
                 lambda ctx: log.append("shipped"),
                 lambda ctx: log.append("cancelled")),
    ]
    saga = Saga(steps)
    ok, err = saga.run()
    assert ok and err is None
    assert log == ["reserved", "charged", "shipped"]
    # failing saga
    log2 = []
    fail_steps = [
        SagaStep("step1", lambda ctx: log2.append("do1"), lambda ctx: log2.append("undo1")),
        SagaStep("step2", lambda ctx: (_ for _ in ()).throw(RuntimeError("boom")), lambda ctx: log2.append("undo2")),
        SagaStep("step3", lambda ctx: log2.append("do3"), lambda ctx: log2.append("undo3")),
    ]
    saga2 = Saga(fail_steps)
    ok2, err2 = saga2.run()
    assert not ok2 and "boom" in err2
    assert log2 == ["do1", "undo1"]  # step2 failed, only step1 compensated
    print("OK: saga_pattern")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: saga_pattern.py test")
