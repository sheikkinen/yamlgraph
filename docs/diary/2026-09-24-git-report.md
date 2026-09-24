## 2026-09-24: Git Report

Based on my analysis of the git repository, here's a comprehensive **feature-level summary of development over the last 3 days** (approximately September 18-20, 2026):

---

## 📊 **Development Summary: Last 3 Days**

### **Release Cycle & Version Management**
- **v0.5.25 Release**: Changelog freeze completed on September 18, consolidating 34 feature fragments into a major release
- **Active Development**: Continued post-release with one critical bugfix (FR-1054)

---

### **Major Features Delivered**

#### **1. Schema System Enhancement (FR-1054) - CRITICAL FIX**
- **Status**: Completed & Deployed
- **Impact**: Fixed nested object schema handling in LLM provider calls
- **Problem Solved**: 
  - Nested object properties were being discarded, causing 55 declared keys to be lost across 14 sites
  - Schemas were collapsing to unconstrained `{}` objects
  - Affected 11 shipped prompts across the codebase
- **Solution**: Recursive schema builder that preserves nested properties
- **Testing**: Comprehensive inventory witness validating all 14 affected sites now work correctly

#### **2. OpenCode Judge Variant (FR-1049) - NEW BACKEND**
- **Status**: Approved & Implemented
- **What It Is**: Third backend option for the judge adapter (alongside existing copilot & claude variants)
- **Key Capabilities**:
  - Uses `deepseek/deepseek-v4-pro` model
  - Operates as headless write-capable backend
  - No permission flags required
  - Enables judge to auto-approve drafts
- **Evidence**: Dual-run witness comparing opencode vs copilot judge outputs
- **Testing**: 397-line comprehensive test suite with routing validation

---

### **Quality & Infrastructure Improvements**

#### **3. Pre-commit Gate Hygiene (FR-1044)**
- Unified ruff version management across all hooks
- Self-repairing suppression ledger for noqa annotations
- Improved developer experience with consistent tooling

#### **4. Artifact Hash Defaults (FR-1051)**
- Fixed artifact hashing to honor `defaults.prompts_relative` c
