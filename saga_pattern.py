#!/usr/bin/env python3
"""Saga pattern for distributed transactions with compensations."""
import sys

class SagaStep:
    def __init__(self, name, action, compensation):
        self.name, self.action, self.compensation = name, action, compensation

class SagaOrchestrator:
    def __init__(self, steps): self.steps = steps; self.completed = []; self.log = []
    def execute(self):
        for step in self.steps:
            self.log.append(f"Executing: {step.name}")
            try:
                result = step.action()
                self.completed.append(step)
                self.log.append(f"  Success: {result}")
            except Exception as e:
                self.log.append(f"  Failed: {e}")
                self._compensate(); return False
        return True
    def _compensate(self):
        self.log.append("Starting compensation...")
        for step in reversed(self.completed):
            self.log.append(f"  Compensating: {step.name}")
            try: step.compensation()
            except Exception as e: self.log.append(f"  Compensation failed: {e}")

def main():
    state = {"order":None,"payment":None,"inventory":None}
    steps = [
        SagaStep("CreateOrder", lambda: state.update({"order":"created"}) or "order-123",
                 lambda: state.update({"order":"cancelled"})),
        SagaStep("ProcessPayment", lambda: state.update({"payment":"charged"}) or "$50",
                 lambda: state.update({"payment":"refunded"})),
        SagaStep("ReserveInventory", lambda: (_ for _ in ()).throw(Exception("Out of stock")),
                 lambda: state.update({"inventory":"released"})),
    ]
    saga = SagaOrchestrator(steps)
    success = saga.execute()
    for entry in saga.log: print(f"  {entry}")
    print(f"Final state: {state}")
    print(f"Saga {'succeeded' if success else 'rolled back'}")

if __name__ == "__main__": main()
