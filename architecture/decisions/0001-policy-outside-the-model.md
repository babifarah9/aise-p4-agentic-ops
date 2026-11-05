# ADR 0001: Safety is enforced by a policy engine outside the planner

**Status:** accepted

**Context.** A planner that reads free text can be persuaded by that text. Prompt-level instructions ("never delete volumes") are not a control.

**Decision.** Every proposed step passes `Policy.decide`, which sees only the tool's declared scope, risk and reversibility, the environment, and the agent's grants.

**Consequences.** Swapping the planner, including for a language model, cannot widen what the agent can do. New tools must be declared with honest risk metadata; that declaration is reviewed like code.
