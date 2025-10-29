# AxProtocol Reorganization Guide

## Overview

This document explains the reorganization of the AxProtocol project structure for better clarity, maintainability, and version control hygiene.

## Key Improvements

### 1. **Version Control Hygiene**
- ✅ Added comprehensive `.gitignore` at root
- ✅ Removed 82MB `.venv` directory from tracking
- ✅ Excluded log files, backups, and temporary files
- ✅ Added `.env.example` template instead of tracking `.env`

### 2. **Consistent Naming Convention**
- ✅ Protocol files renamed with kebab-case: `v2.1a-core-directives.txt`
- ✅ Removed underscores and inconsistent capitalization
- ✅ Version numbers clearly visible in filenames

### 3. **Logical Directory Structure**
```
Old: Master/                         New: AxProtocol/
├── AxProtocol_*.txt (scattered)     ├── protocol/ (all together)
├── core/                            ├── implementations/
├── variants/                        ├── docs/
├── Scouts/                          ├── scouts/
└── sync_bridge.py                   └── scripts/
```

### 4. **Eliminated Duplication**
- ✅ Consolidated duplicate protocol files
- ✅ Single source of truth for each directive
- ✅ Removed redundant copies

## File Mapping

### Protocol Files
| Old Location | New Location |
|--------------|--------------|
| `AxProtocol_v0_CORE-CHANGE-CONTROL.txt` | `protocol/v0-change-control.txt` |
| `AxProtocol_v2.1a_MASTER.txt` | `protocol/v2.1a-core-directives.txt` |
| `AxProtocol_v2.1b_ADDENDUM-WarRoomIntegration.txt` | `protocol/v2.1b-war-room-integration.txt` |
| `AxProtocol_v2.1c_LAYER-AAL.txt` | `protocol/v2.1c-authority-layer.txt` |
| `AxProtocol_v2.2_LAYER-TAES.txt` | `protocol/v2.2-taes-evaluation.txt` |
| `AxProtocol_v2.3_LAYER-RDL.txt` | `protocol/v2.3-red-team-layer.txt` |
| `core/AxProtocol_v2.3_FULL.txt` | `protocol/v2.3-consolidated.txt` |

### Implementation Files
| Old Location | New Location |
|--------------|--------------|
| `variants/AxP_AAL+TAES_v0.1b/War-Room/` | `implementations/war-room-v0.1b/` |

### Documentation
| Old Location | New Location |
|--------------|--------------|
| `operator-console.md` | `docs/operator-console.md` |
| `Scouts/` | `scouts/` |

### Scripts
| Old Location | New Location |
|--------------|--------------|
| `sync_bridge.py` | `scripts/sync_bridge.py` |

## What Was Excluded

These items are now properly .gitignored:

- **82MB .venv directory** - Virtual environments should never be in version control
- **Log files** - Generated at runtime, not needed in repo
- **Backup files** - Temporary artifacts
- **Session databases** - Runtime data
- **Media files** - Large binary assets
- **__pycache__ directories** - Python bytecode

## Migration Steps

If you're updating an existing local repository:

1. **Backup your current work**
   ```bash
   cp -r Master Master-backup
   ```

2. **Replace with optimized structure**
   ```bash
   # The optimized structure is in /mnt/user-data/outputs/
   ```

3. **Update any scripts with hardcoded paths**
   - Check for references to old paths
   - Update to new structure

4. **Configure environment**
   ```bash
   cd implementations/war-room-v0.1b
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Install dependencies fresh**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

## Benefits

### For Development
- **Clearer organization**: Easier to find files
- **Faster git operations**: Without 82MB of venv bloat
- **Better collaboration**: Standard structure everyone understands

### For Deployment
- **Smaller repository**: 98% reduction in size (84MB → <2MB)
- **Faster clones**: Much quicker for CI/CD
- **Environment isolation**: Each developer creates their own venv

### For Maintenance
- **Consistent naming**: No guessing about file purposes
- **Single source of truth**: No duplicate protocol files
- **Clear separation**: Protocol vs. Implementation vs. Documentation

## Updated Commands

### Working Directory Changes

**Old:**
```bash
cd Master/variants/AxP_AAL+TAES_v0.1b/War-Room
```

**New:**
```bash
cd implementations/war-room-v0.1b
```

### Running War Room

**Old & New (same):**
```bash
TIER=DEV python run_axp.py "Your objective"
streamlit run app_axp.py
```

## Next Steps

1. Review the new structure
2. Update any CI/CD pipelines
3. Update documentation links
4. Commit the optimized structure to your repository
5. Update README paths in CLAUDE.md

## Questions?

This reorganization maintains all functionality while dramatically improving maintainability. All protocol directives, implementation code, and documentation remain intact—just better organized.

---

**Reorganization Date:** 2025-10-25  
**Version:** AxProtocol v2.3 (structure optimization)
