## 2026-05-20: Git Report

Perfect! Now I have enough information to provide a comprehensive analysis. Let me create a feature-level summary:

## Git Repository Analysis: Last 3 Days Development Summary

Based on the commit history and changed files from the last 3 days, here's the feature-level development activity:

### **Major Features Delivered**

#### 1. **FSM (Finite State Machine) Schema Hardening** (FR-419, FR-420, FR-422)
   - **Focus**: ActionConfig mapping validation and robustness
   - **Key Improvements**:
     - Fixed description field annotation stripping (was causing schema validation failures)
     - Added strict typing for event_map with proper error handling
     - Implemented variables dict coercion for template expressions
     - Added defensive parameter stripping in nested execute() branches
   - **Impact**: Prevents silent misroutes caused by YAML authoring errors

#### 2. **Questionnaire Gap Utilities** (FR-421)
   - **Focus**: Built-in tools for detecting gaps in questionnaire configurations
   - **New Capability**: Added `questionnaire.py` tools module with gap detection functions
   - **Documentation**: Comprehensive feature documentation and probe-recap guidelines
   - **Testing**: Red-green test suite (test_fr421) included

#### 3. **Fallback Confession Gate** (FR-418)
   - **Focus**: Script-level hedging and fallback mechanisms
   - **Implementation**: Enhanced `scripts/hedging_check.py` with confession gate logic
   - **Scope**: 310+ lines of enhanced hedging detection and fallback handling
   - **Documentation**: Added `docs/confessions.md` with detailed confession patterns

#### 4. **Chaplain YAML Graph Async Bridge Migration** (FR-413)
   - **Focus**: Refactoring chaplain actions to use shared bridge pattern
   - **Changes**: 
     - Migrated `yamlgraph_async_action.py` to shared bridge architecture
     - Enhanced FSM action module with shared bridge utilities
     - Added CI hard-fail requirement for statemachine-engine dependency
   - **Testing**: Compreh
