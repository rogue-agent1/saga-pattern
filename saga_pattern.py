#!/usr/bin/env python3
"""Saga pattern (distributed transactions with compensation) — zero-dep."""

class SagaStep:
    def __init__(self, name, action, compensate):
        self.name=name; self.action=action; self.compensate=compensate

class Saga:
    def __init__(self, name):
        self.name=name; self.steps=[]; self.completed=[]; self.log=[]
    def add_step(self, name, action, compensate):
        self.steps.append(SagaStep(name,action,compensate))
    def execute(self, context):
        for step in self.steps:
            try:
                self.log.append(f"→ {step.name}")
                step.action(context)
                self.completed.append(step)
            except Exception as e:
                self.log.append(f"✗ {step.name} failed: {e}")
                self._compensate(context); return False
        self.log.append("✓ Saga completed"); return True
    def _compensate(self, context):
        self.log.append("⟲ Compensating...")
        for step in reversed(self.completed):
            try:
                step.compensate(context)
                self.log.append(f"  ↩ {step.name} compensated")
            except Exception as e:
                self.log.append(f"  ✗ {step.name} compensation failed: {e}")

if __name__=="__main__":
    ctx={"order":None,"payment":None,"inventory":None,"shipping":None}
    saga=Saga("OrderSaga")
    saga.add_step("CreateOrder",lambda c:c.update({"order":"created"}),lambda c:c.update({"order":"cancelled"}))
    saga.add_step("ChargePayment",lambda c:c.update({"payment":"charged"}),lambda c:c.update({"payment":"refunded"}))
    saga.add_step("ReserveInventory",lambda c:(_ for _ in ()).throw(RuntimeError("Out of stock")),lambda c:c.update({"inventory":"released"}))
    saga.add_step("ShipOrder",lambda c:c.update({"shipping":"shipped"}),lambda c:c.update({"shipping":"cancelled"}))
    result=saga.execute(ctx)
    print(f"Saga result: {'success' if result else 'failed + compensated'}")
    print(f"Context: {ctx}")
    for l in saga.log: print(f"  {l}")
