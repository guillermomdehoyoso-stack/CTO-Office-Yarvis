# EOS Glossary

## Status

PROPOSED

NOT RATIFIED

## Scope

This glossary is normative vocabulary for EOS governance communication.
It clarifies existing constitutional and documentary terms only.
It introduces no new authority, no new implementation scope, and no new phase.

## Terms

### 1. EOS
NORMATIVE DEFINITION: EOS is the domain-independent engineering operating system that governs how authority, evidence, review, and delivery controls are applied across long-lived software work.
BOUNDARY OR EXCLUSION: EOS is not product runtime architecture, not domain business logic, and not implementation code.
OPTIONAL RELATIONSHIP TO OTHER TERMS: EOS is constrained by Constitution, Governance, and Authority Hierarchy.

### 2. Constitution
NORMATIVE DEFINITION: The Constitution is the highest normative governance authority for EOS principles.
BOUNDARY OR EXCLUSION: It does not directly ratify implementation details or product architecture by itself.
OPTIONAL RELATIONSHIP TO OTHER TERMS: It defines Authority Hierarchy and boundaries for Agent and Human Authority.

### 3. Governance
NORMATIVE DEFINITION: Governance is the set of ratified rules that creates, constrains, and interprets engineering authority.
BOUNDARY OR EXCLUSION: Governance is not implementation execution.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Governance is subordinate to Constitution and superior to lower documentary layers.

### 4. Authority
NORMATIVE DEFINITION: Authority is the recognized right to define binding engineering direction under the hierarchy.
BOUNDARY OR EXCLUSION: Authority is not created by conversation, memory, or tool output alone.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Authority depends on Evidence and Ratification state.

### 5. Authority Hierarchy
NORMATIVE DEFINITION: Authority Hierarchy is the ordered precedence of documentary authority used to resolve conflicts.
BOUNDARY OR EXCLUSION: Lower layers cannot silently override higher layers.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Defined by Constitution Article I.

### 6. Evidence
NORMATIVE DEFINITION: Evidence is verifiable information that supports an engineering claim or decision.
BOUNDARY OR EXCLUSION: Assertion without verifiable documentary basis is not sufficient evidence.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Evidence supports Review, Finding, Validation, and Ratification.

### 7. Repository Evidence
NORMATIVE DEFINITION: Repository Evidence is engineering evidence present in versioned repository artifacts.
BOUNDARY OR EXCLUSION: Chat-only statements and hidden session context are excluded.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Repository Evidence is the required basis for Independent Review.

### 8. Durable Authority
NORMATIVE DEFINITION: Durable Authority is authority that persists through Git-tracked, reviewable documentation under the hierarchy.
BOUNDARY OR EXCLUSION: Ephemeral conversational context is excluded.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Durable Authority depends on Repository Evidence and ratified status.

### 9. Proposal
NORMATIVE DEFINITION: A Proposal is a candidate artifact or change submitted for review that is not yet binding.
BOUNDARY OR EXCLUSION: Proposal status is not ratified authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Proposal precedes Review and possible Ratification.

### 10. Review
NORMATIVE DEFINITION: Review is the evaluation of a proposal against governing authority and evidence.
BOUNDARY OR EXCLUSION: Review itself is not ratification.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Review produces Findings and a disposition.

### 11. Independent Review
NORMATIVE DEFINITION: Independent Review is a review performed from repository bootstrap and repository evidence in an independent session without hidden conversational state.
BOUNDARY OR EXCLUSION: Self-approval by the proposing process is excluded.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Independent Review is mandatory before Ratification.

### 12. Finding
NORMATIVE DEFINITION: A Finding is a documented review outcome identifying conformance, risk, defect, or required correction.
BOUNDARY OR EXCLUSION: A finding is not implementation authority by itself.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Findings guide amendment corrections and ratification decisions.

### 13. Ratification
NORMATIVE DEFINITION: Ratification is formal acceptance that grants binding authority under the hierarchy.
BOUNDARY OR EXCLUSION: No proposal may ratify itself.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Ratification follows Review and evidence-based disposition.

### 14. Human Authority
NORMATIVE DEFINITION: Human Authority is the identified human accountability that holds final engineering responsibility.
BOUNDARY OR EXCLUSION: Agents cannot replace Human Authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Human Authority confirms ratification and governance responsibility.

### 15. Agent
NORMATIVE DEFINITION: An Agent is a tool-assisted actor that can analyze, review, propose, generate, and summarize within declared boundaries.
BOUNDARY OR EXCLUSION: Agents cannot ratify, self-approve, or change authority unilaterally.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Agent work is constrained by Constitution and Governance.

### 16. Session
NORMATIVE DEFINITION: A Session is one bounded working interaction with its own immediate context.
BOUNDARY OR EXCLUSION: Session context is not durable authority unless recorded as repository evidence.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Independent Review requires independent session conditions.

### 17. Bootstrap
NORMATIVE DEFINITION: Bootstrap is the required startup reading and state reconstruction process from repository authority sources.
BOUNDARY OR EXCLUSION: Bootstrap cannot rely on hidden memory as authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Bootstrap precedes gate decisions and implementation actions.

### 18. State
NORMATIVE DEFINITION: State is the documented snapshot of current engineering position, constraints, and next actions.
BOUNDARY OR EXCLUSION: State does not supersede higher authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Current State is a specific state artifact.

### 19. Current State
NORMATIVE DEFINITION: Current State is the active engineering-state record used for operational orientation.
BOUNDARY OR EXCLUSION: Current State cannot independently create, supersede, or ratify authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Current State is below ratified layers in Authority Hierarchy.

### 20. Gate
NORMATIVE DEFINITION: A Gate is a required control point that must be satisfied before proceeding to specified work.
BOUNDARY OR EXCLUSION: Passing a gate does not rewrite higher authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Gates depend on Review, Findings, and Validation evidence.

### 21. Active Gate
NORMATIVE DEFINITION: Active Gate is the currently controlling gate for allowed next engineering action.
BOUNDARY OR EXCLUSION: Work outside the Active Gate is unauthorized unless explicitly allowed.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Active Gate is recorded in Current State and Current Sprint.

### 22. Work Package
NORMATIVE DEFINITION: A Work Package is a bounded, named set of tasks with defined objective, scope, and exit criteria.
BOUNDARY OR EXCLUSION: A work package does not expand authority beyond governing artifacts.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Work Package execution is constrained by Active Gate.

### 23. Validation
NORMATIVE DEFINITION: Validation is the verification that artifacts or outcomes conform to stated requirements and governing authority.
BOUNDARY OR EXCLUSION: Validation is not approval or ratification.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Validation provides evidence consumed by Review.

### 24. Implementation
NORMATIVE DEFINITION: Implementation is the execution of approved engineering changes in code, runtime, or operations artifacts.
BOUNDARY OR EXCLUSION: Implementation is not authorized by proposal status alone.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Implementation follows ratified authority and gate clearance.

### 25. Amendment
NORMATIVE DEFINITION: An Amendment is an append-only corrective or clarifying document that updates planning interpretation within stated scope.
BOUNDARY OR EXCLUSION: Amendment is not silent overwrite and is not automatic ratification.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Amendments preserve historical lineage and require review.

### 26. Supersession
NORMATIVE DEFINITION: Supersession is explicit replacement of prior lower-level statements by later authorized artifacts within defined scope.
BOUNDARY OR EXCLUSION: Implicit or silent supersession is invalid.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Supersession must respect Authority Hierarchy.

### 27. Append-Only History
NORMATIVE DEFINITION: Append-Only History means prior engineering records remain preserved while corrections are added as new artifacts.
BOUNDARY OR EXCLUSION: History rewriting is prohibited.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Append-Only History governs Amendment and review lineage.

### 28. Decision
NORMATIVE DEFINITION: A Decision is a documented engineering choice with traceable rationale and scope.
BOUNDARY OR EXCLUSION: Undocumented or non-evidenced choice is not a durable decision.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Decisions may be tracked in decision registers or ADRs based on scope.

### 29. Architecture Decision Record
NORMATIVE DEFINITION: An Architecture Decision Record is a structured record of an architecture-level decision and its consequences.
BOUNDARY OR EXCLUSION: It is not a substitute for constitutional authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Ratified ADRs are a defined layer in Authority Hierarchy.

### 30. Policy
NORMATIVE DEFINITION: A Policy is a rule-level statement of required behavior within a defined governance scope.
BOUNDARY OR EXCLUSION: Policy cannot exceed higher-authority constraints.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Policy may be implemented through standards and procedures.

### 31. Standard
NORMATIVE DEFINITION: A Standard is a normative specification of required format, quality, or consistency criteria.
BOUNDARY OR EXCLUSION: A standard does not by itself ratify new authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Standards support Validation and deterministic reconstruction.

### 32. Procedure
NORMATIVE DEFINITION: A Procedure is an ordered method for executing work under existing authority.
BOUNDARY OR EXCLUSION: Procedures do not create new governance power.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Procedures operationalize policies and standards.

### 33. Capability
NORMATIVE DEFINITION: A Capability is a reusable ability to perform a defined engineering or operational function.
BOUNDARY OR EXCLUSION: Capability is not automatically a product feature.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Capabilities may be Shared Capability, Product Capability, or Development Infrastructure.

### 34. Open Standard
NORMATIVE DEFINITION: An Open Standard is a publicly defined, interoperable specification not controlled by a single vendor implementation.
BOUNDARY OR EXCLUSION: Vendor-exclusive behavior is excluded from this term.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Open Standard has first priority in Reuse Before Build when equivalent.

### 35. Mature Capability
NORMATIVE DEFINITION: A Mature Capability is an established, widely used solution with demonstrated reliability and maintainability.
BOUNDARY OR EXCLUSION: Maturity alone does not override constitutional or authority constraints.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Mature Capability is second priority after Open Standard in Reuse Before Build.

### 36. Thin Integration
NORMATIVE DEFINITION: Thin Integration is minimal coupling that uses existing capabilities through narrow adapters and explicit boundaries.
BOUNDARY OR EXCLUSION: Thin Integration excludes deep rewrites or broad framework capture.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Thin Integration is preferred before Extension and Custom Core.

### 37. Extension
NORMATIVE DEFINITION: Extension is bounded additional behavior built on top of existing capabilities without replacing their core.
BOUNDARY OR EXCLUSION: Extension must not become unbounded custom platform creation.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Extension precedes Custom Core in Reuse Before Build.

### 38. Custom Core
NORMATIVE DEFINITION: Custom Core is bespoke foundational implementation created and owned directly by the engineering organization.
BOUNDARY OR EXCLUSION: Custom Core requires explicit differentiation justification and cannot be default-first.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Custom Core is the last option in Reuse Before Build.

### 39. Reuse Before Build
NORMATIVE DEFINITION: Reuse Before Build is the engineering selection order: Open Standard, Mature Capability, Thin Integration, Extension, then Custom Core.
BOUNDARY OR EXCLUSION: Vendor-specific selection is not default when equivalent open standards satisfy requirements.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Reuse Before Build is constrained by Constitution Article VII and DOS-003 proposed status.

### 40. Domain
NORMATIVE DEFINITION: A Domain is a bounded operational problem space with its own business semantics and ownership boundaries.
BOUNDARY OR EXCLUSION: Domain boundaries cannot be merged implicitly through technical reuse.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Domain knowledge is represented through Domain Packs under EOS governance.

### 41. Domain Pack
NORMATIVE DEFINITION: A Domain Pack is a domain-specific knowledge and governance package that applies EOS principles to one domain context.
BOUNDARY OR EXCLUSION: A Domain Pack is not EOS itself and does not redefine constitutional authority.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Domain Pack may consume Shared Capability without transferring business ownership.

### 42. Domain Operating System
NORMATIVE DEFINITION: A Domain Operating System is the domain-level operating framework for one domain, governed under EOS and domain constraints.
BOUNDARY OR EXCLUSION: It is not a replacement for EOS constitutional governance.
OPTIONAL RELATIONSHIP TO OTHER TERMS: A Domain Operating System can be realized through one or more Domain Packs.

### 43. Yarvis
NORMATIVE DEFINITION: Yarvis is the first domain-composable operational system governed and developed under EOS.
BOUNDARY OR EXCLUSION: Yarvis is not EOS governance infrastructure.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Immediate implementation priority is Netpay operations, Energia Fotonica operations, and shared operational capabilities required by both.

### 44. Shared Capability
NORMATIVE DEFINITION: Shared Capability is a reusable technical or operational capability consumed by multiple domains under explicit boundaries.
BOUNDARY OR EXCLUSION: Shared Capability does not transfer canonical domain ownership.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Shared Capability may support multiple Domain Packs and Yarvis domains.

### 45. Product Capability
NORMATIVE DEFINITION: Product Capability is user-facing or operational-system behavior that delivers product value.
BOUNDARY OR EXCLUSION: Product Capability is distinct from Development Infrastructure governance tooling.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Yarvis delivery prioritizes Product Capability for Netpay and Energia Fotonica.

### 46. Development Infrastructure
NORMATIVE DEFINITION: Development Infrastructure is engineering support capability used to govern, coordinate, or accelerate delivery work.
BOUNDARY OR EXCLUSION: Development Infrastructure is not direct product-domain behavior.
OPTIONAL RELATIONSHIP TO OTHER TERMS: EOS and Development Kernel proposal artifacts are development infrastructure.

### 47. Runtime Dependency
NORMATIVE DEFINITION: Runtime Dependency is a required component for execution of an application or runtime path.
BOUNDARY OR EXCLUSION: Documentary governance artifacts are not runtime dependencies by default.
OPTIONAL RELATIONSHIP TO OTHER TERMS: EOS documentary artifacts do not create new Yarvis runtime dependency authority.

### 48. Ambiguity
NORMATIVE DEFINITION: Ambiguity is a material uncertainty where authority, scope, or interpretation cannot be determined from repository evidence.
BOUNDARY OR EXCLUSION: Ambiguity is not resolved by speculation.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Ambiguity triggers Stop-and-Report under constitutional constraints.

### 49. Stop-and-Report
NORMATIVE DEFINITION: Stop-and-Report is mandatory behavior to halt progression, state the ambiguity or conflict, and request governing review.
BOUNDARY OR EXCLUSION: Stop-and-Report is not silent continuation.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Required by Deterministic Reconstruction and Epistemic Humility.

### 50. Epistemic Humility
NORMATIVE DEFINITION: Epistemic Humility is the obligation to avoid fabricated certainty and to escalate conflicting evidence.
BOUNDARY OR EXCLUSION: Confident assertion without evidence is prohibited.
OPTIONAL RELATIONSHIP TO OTHER TERMS: Epistemic Humility operationalizes Stop-and-Report.

## Scope Guardrail

- EOS exists to accelerate and govern delivery of operational systems.
- Yarvis is the first operational system governed under EOS.
- EOS work must be justified by immediate reduction of engineering risk, ambiguity, or implementation time.
- EOS is not currently authorized as a standalone commercial product.
- EOS must not delay the Yarvis Netpay and Energia Fotonica delivery path.
- Additional EOS layers require explicit roadmap authority.
- After glossary review and minimum documentary baseline, default priority returns to Yarvis implementation.
