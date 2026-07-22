## 2026-07-22: Git Report

Perfect! Now I have enough context. Let me compile a comprehensive analysis.

## Git Repository Analysis: Last 3 Days of Development

Based on my analysis of the repository commits and changes from **July 19-21, 2026**, here's the feature-level summary:

---

### **📊 Overview**
- **Commits analyzed:** Top 50 recent commits
- **Period:** Last 3 days (July 19-21, 2026)
- **Release cycle:** v0.5.15 → v0.5.16 released during this period
- **Development focus:** Architecture boundary enforcement, package organization, and routing infrastructure

---

### **🎯 Major Features Completed**

#### **1. Architecture & Boundary Enforcement (FR-754, FR-755, FR-756)**
- **FR-754:** Relocated `id_registry` out of shipped package into `scripts/` directory
  - Moved from `yamlgraph/utils/` to `scripts/`
  - Fixed `.chaplain` path leak in shipped package
  - Updated import contracts to enforce core boundary
  - **Status:** ✅ Completed with RED tests and enforcement

- **FR-755:** FSM Bridge Architecture Ruling
  - Declared FSM bridge as contrib-tier component
  - Froze import contract at core boundary
  - Updated `.importlinter` configuration
  - Added CAP-141 capability documentation
  - **Status:** ✅ Completed

- **FR-756:** Core-Process Boundary Enforcement (in progress)
  - Part of multi-phase boundary enforcement initiative
  - Documented in diary with implementation plan

#### **2. Route Overlay Infrastructure (FR-752, FR-753)**
- **FR-752:** Route Log Path Targets
  - Support for directory targets with trailing separator intent
  - Auto-create parent directories for `YAMLGRAPH_ROUTE_LOG`
  - Relative path resolution against CWD
  - Warning system for invalid targets
  - Preserved never-raise emission behavior

- **FR-753:** Route Overlay Example CLI
  - New `examples/route_overlay_cli/` package
  - Argparse-based CLI interface
  - Graph and route validation
  - mermaid-cli (mmdc) integration
  - Comprehensive demo script and unit tests (189 lines of test coverage)
  - **Status:*
