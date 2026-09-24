## 2026-09-23: Git Report

Perfect! Now I have enough context to provide a comprehensive analysis. Let me compile the feature-level summary:

## Git Repository Analysis: Last 3 Days Development Summary

Based on analysis of commits from **September 18-20, 2026**, here's the feature-level development summary:

### **Release Milestone: v0.5.25 Freeze** (Sep 18)
- **Changelog freeze** completed with 34 feature fragments consolidated
- Major release bundling multiple FRs completed in this cycle

---

### **Key Features Implemented (Last 3 Days)**

#### **1. FR-1054: Nested Object Schema Fix** ⭐ (Sep 20 - Most Recent)
- **Problem**: Schema builder was discarding nested object properties, causing providers to return empty objects `{}`
- **Impact**: 55 declared keys lost across 11 shipped prompts at 14 sites
- **Solution**: Recursive schema building now preserves nested properties while maintaining type safety
- **Scope**: 
  - Added comprehensive test suite with inventory witness tracking all 14 affected sites
  - Updated schema loader with recursive property handling
  - Reference documentation updated for schema constraints
- **Status**: ✅ APPROVED - Live witness confirms zero property losses post-fix

#### **2. FR-1050: Loop Limits Bind-or-Fail Compilation** (Sep 18)
- **Problem**: `loop_limits` declarations were parsed but never enforced on 9 of 15 node types—effectively comments
- **Solution**: Compile-time validation that rejects dangling/unsupported loop_limit entries before execution
- **Scope**:
  - Enforced on 6 supportive node types (race, llm, etc.)
  - Validated at load time before macro expansions
  - 18 graphs migrated repo-wide with zero rejections
  - Added strict disjoint classification assertions
- **Status**: ✅ APPROVED - All 18 graphs validate cleanly

#### **3. FR-1051: Artifact Hash Respects defaults.prompts_relative** (Sep 18)
- **Problem**: `compute_artifact_hash` ignored `defaults.prompts_relative` fallback, causing unresolved prompt errors
- **Root Cause**: Hash function
