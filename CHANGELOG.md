# Changelog

## v0.5.2-RC2 "TraceForge / 迹铸"

### Added
- Added Coding Authority Policy (`structured-intelligence/CODING_AUTHORITY_POLICY.md`)
- Added Writeback Authority Matrix (`structured-intelligence/WRITEBACK_AUTHORITY_MATRIX.md`)
- Added explicit distinction between centralized coding, distributed coding, and bounded writeback
- Added governance fields to ClaudeCode task template and runtime trace template
- Added structured intelligence README with governance framework overview
- Added Writeback Policy with enforcement rules
- Added Patch Validation Checklist with authority checks
- Added Writeback Log (`structured-intelligence/WRITEBACK_LOG.md`)
- Added `docs/semantic_control_adapter_spec_v0.1.md`
- Added conceptual semantic-to-control mapping examples for two-finger, three-finger, and suction gripper embodiments

### Fixed
- P6/P7/P8 duplicate rendering in Stage-by-Stage trace (was rendering twice due to phases containing P6-P8)
- Success trace P6 alignment: added "not applicable" P6 when no failure_patches to keep P0-P8 aligned
- P8 transition condition: `from_stage` corrected from 'P7' to 'P8'
- Interaction flow card: skip P6/P7/P8 from failure phases (Patch node covers cognitive stages)
- P6 transition logic: P6 → P7 → P8 (was incorrectly P6 → P8)
- force_stability expression: `stable (observed)` instead of `stable (unknown)`
- Version numbers unified to v0.5.2 across all outputs
- Terminology cleanup: "Failure Patch" → "Failure Hypothesis & Patch Suggestion"
- Cross-embodiment source_failure_meaning: no longer defaults to "unknown"
- P6-P8 Stage Interpretation: "repair strategy" → "patch suggestion"
- README image references: copied architecture diagrams into project assets/figures/
- validation_metrics: `grip_force_stability.current` "unknown" → "not_measured_in_current_demo"

### Governance
- Default repo workflow is now defined as Distributed Coding + Bounded Writeback
- ClaudeCode may autonomously implement bounded patches and write runtime traces / audit notes
- Strategic writeback remains human-approval required
- Writeback levels: L0 (none), L1 (trace), L2 (validated), L3 (strategic)

### Boundaries
- No real-robot validation claim.
- No replacement claim over VLA / World Model / Controller.
- `failure_hypothesis` remains hypothesis, not proven root cause.

### Changed
- Stage-by-Stage AS-IR Runtime Trace now covers P0-P8 (was P1-P5)
- Each stage card includes Stage Interpretation / 阶段解释
- HTML report supports bilingual (EN/ZH) stage overview and next action sections

---

## v0.5.1

### Fixed
- CSS typo: `background:##` → `background:#`
- Added P0, P6, P7, P8 to Stage-by-Stage trace
- Added Next Action Recommendation section
- Removed duplicate Raw Trajectory View explanation
- Terminology cleanup throughout HTML

---

## v0.5.0

### Added
- Stage-by-Stage Physical Interaction Runtime Trace (P0-P8)
- `failure_hypothesis` replacing `root_cause` globally
- `patch_suggestion` replacing `repair_decision` globally
- `validation_metrics` for patch effectiveness
- `next_action_recommendation` output
- Phase A-D refactor plan in docs

### Changed
- Terminology upgrade across all source files
- README restructured for v0.5 positioning
- JSON outputs use new field names

---

## v0.4.0

### Added
- PILa (Physical Interaction Language) as primary external name
- AS-IR as underlying IR / technical alias
- Glossary section in HTML report
- Naming card explaining PILa vs AS-IR relationship

### Changed
- HTML title: "PILa Cup-Grasp MVP v0.4.0"
- All user-facing text uses PILa as primary name
- JSON internal fields retain AS-IR naming

---

## v0.3.4

### Fixed
- Patched Lift animation now visibly lifts the cup
- Failure step shows unstable lift and slip-down behavior
- Cup rotation (tilt) added for failure visualization

---

## v0.3.3

### Added
- Bilingual (EN/ZH) language switching in HTML report
- Language persistence via localStorage
- All major sections support dual language

---

## v0.3.2

### Added
- Cup-Grasp Timeline Animation
- AS-IR Meaning Extraction Animation
- Cross-Embodiment Transfer Animation
- Replay buttons for all animations

---

## v0.3.1

### Changed
- Version numbers unified to v0.3
- README updated with v0.3 capabilities
- cross_embodiment_transfer.json enhanced with transfer_claim and meaning_interpretation

---

## v0.3.0

### Added
- Cross-Embodiment Meaning Transfer module
- robot_profiles.json with three robot morphologies
- Robot-specific patch generation from shared AS-IR meaning

---

## v0.2.0

### Added
- run_metadata in trajectories and traces
- Patch structure with patch_id and validation_status
- Learning update with structured experience retention
- Phase status: warning/failure indicators
- Risk policy: YELLOW/ORANGE risk levels
- Interaction flow card
- representation_gain field

---

## v0.1.0

### Added
- Initial MVP: Cup-Grasp failure diagnosis demo
- Raw trajectory simulation (failure + success)
- AS-IR trace extraction
- Failure patch generation
- HTML report with comparison charts
- Cross-embodiment transfer concept
