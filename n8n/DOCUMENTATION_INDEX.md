# n8n AI Guard Integration - Documentation Index

This directory contains comprehensive documentation for developing and testing the Zscaler AI Guard custom node for n8n.

---

## 📚 Documentation Files

### 1. [README.md](./README.md)
**Main documentation** - Overview of the integration, features, and basic usage.

**Contents:**
- What the integration does
- Installation options (npm and local)
- Quick start guide
- Node operations (Prompt Scan, Response Scan, Dual Scan)
- Example workflows
- Security features
- Resources and support

**Use when:** You want a high-level overview or are publishing/sharing the package.

---

### 2. [SETUP_GUIDE.md](./SETUP_GUIDE.md) ⭐ **MOST COMPREHENSIVE**
**Complete step-by-step setup guide** with detailed troubleshooting.

**Contents:**
- Prerequisites checklist
- Initial setup (clone, install, build)
- Docker configuration explanation
- Building and running with Docker
- Creating test workflows step-by-step
- Two testing methods (test mode and production mode)
- **7 common issues with detailed solutions:**
  1. Custom node not appearing
  2. Webhook 404 errors
  3. "undefined" error in AI Guard node
  4. API authentication failures
  5. Docker container issues
  6. Changes not reflected after code edits
  7. Workflow executions not showing results
- Verification steps
- Quick reference commands

**Use when:** Setting up for the first time, troubleshooting issues, or need detailed explanations.

**Total Length:** ~900 lines of comprehensive documentation

---

### 3. [DOCKER_DEV.md](./DOCKER_DEV.md)
**Docker-specific development workflow** guide.

**Contents:**
- Quick start commands
- Making changes workflow
- Testing the custom node in n8n
- Setting up credentials
- Testing a simple scan
- Docker commands reference
- File structure
- Troubleshooting Docker issues
- Development workflow
- Production deployment notes

**Use when:** Working with Docker containers specifically or need Docker-related commands.

---

### 4. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) ⚡ **FASTEST LOOKUP**
**One-page cheat sheet** for common tasks and issues.

**Contents:**
- 3-step quick start
- Common commands (development, testing)
- Common issues table with quick fixes
- Workflow configuration checklist
- Debugging commands
- Expected results (what success looks like)
- Test cases with curl commands

**Use when:** You know what you're doing but need a quick command or reminder.

**Total Length:** ~150 lines - designed for quick scanning

---

## 🗺️ Which Document to Use?

```
┌─────────────────────────────────────┐
│ What do you need?                   │
└─────────────────────────────────────┘
         │
         ├─ First time setup?
         │  └─> SETUP_GUIDE.md
         │
         ├─ Quick command lookup?
         │  └─> QUICK_REFERENCE.md
         │
         ├─ Docker-specific help?
         │  └─> DOCKER_DEV.md
         │
         ├─ General overview?
         │  └─> README.md
         │
         └─ Troubleshooting?
            └─> SETUP_GUIDE.md (Section: Common Issues)
```

---

## 🔍 Finding Specific Information

### "Custom node not showing in n8n"
- **SETUP_GUIDE.md** → Issue 1
- **QUICK_REFERENCE.md** → Common Issues table

### "Webhook returns 404"
- **SETUP_GUIDE.md** → Issue 2
- **QUICK_REFERENCE.md** → Common Issues table

### "Getting 'undefined' error"
- **SETUP_GUIDE.md** → Issue 3
- **QUICK_REFERENCE.md** → Common Issues table

### "How to test the integration?"
- **SETUP_GUIDE.md** → Testing the Integration
- **QUICK_REFERENCE.md** → Test Cases

### "What commands to run?"
- **QUICK_REFERENCE.md** → Common Commands
- **SETUP_GUIDE.md** → Quick Reference Commands

### "Docker container won't start"
- **SETUP_GUIDE.md** → Issue 5
- **DOCKER_DEV.md** → Troubleshooting

### "Changes not showing after edit"
- **SETUP_GUIDE.md** → Issue 6
- **QUICK_REFERENCE.md** → Development Cycle

---

## 📁 Related Files

### Configuration Files
- `docker-compose.yml` - Docker Compose configuration
- `docker-init.sh` - Container initialization script
- `package.json` - Node package configuration
- `tsconfig.json` - TypeScript configuration

### Source Code
- `nodes/AIGuard/AIGuard.node.ts` - Main node implementation
- `credentials/AIGuardApi.credentials.ts` - Credentials definition
- `dist/` - Compiled output (generated)

### Workflow Templates
- `workflows/AIGuard_Secure_AI_Chatbot.json` - Example workflow

---

## 🎯 Common Workflows by Role

### Developer (First Time Setup)
1. Read **README.md** (overview)
2. Follow **SETUP_GUIDE.md** (complete setup)
3. Bookmark **QUICK_REFERENCE.md** (daily use)

### Developer (Daily Work)
1. Use **QUICK_REFERENCE.md** for commands
2. Refer to **DOCKER_DEV.md** for Docker tasks
3. Check **SETUP_GUIDE.md** when stuck

### QA/Tester
1. Follow **SETUP_GUIDE.md** → Testing section
2. Use **QUICK_REFERENCE.md** → Test Cases
3. Reference **SETUP_GUIDE.md** for troubleshooting

### Technical Writer/Documentation
1. Start with **README.md**
2. Reference all docs for comprehensive info
3. Use **SETUP_GUIDE.md** for accurate procedures

---

## 🛠️ Maintenance

### When to Update Documentation

**Code Changes:**
- Node operations change → Update README.md, SETUP_GUIDE.md
- New configuration options → Update SETUP_GUIDE.md, QUICK_REFERENCE.md
- New issues discovered → Add to SETUP_GUIDE.md Issue section

**Docker Changes:**
- Docker config changes → Update DOCKER_DEV.md, SETUP_GUIDE.md
- New Docker commands → Update QUICK_REFERENCE.md

**Testing Changes:**
- New test scenarios → Update QUICK_REFERENCE.md Test Cases
- New troubleshooting steps → Update SETUP_GUIDE.md

### Documentation Standards

- Keep QUICK_REFERENCE.md under 200 lines
- Include code examples in all guides
- Use consistent formatting (bash code blocks, json examples)
- Cross-reference between documents
- Update "Last Updated" dates

---

## 📊 Documentation Coverage

| Topic | README | SETUP_GUIDE | DOCKER_DEV | QUICK_REF |
|-------|--------|-------------|------------|-----------|
| Overview | ✅ Full | ⚠️ Brief | ⚠️ Brief | ⚠️ Brief |
| Prerequisites | ⚠️ Brief | ✅ Full | ⚠️ Brief | ❌ None |
| Installation | ✅ Full | ✅ Full | ✅ Full | ✅ Commands |
| Configuration | ⚠️ Brief | ✅ Full | ✅ Full | ✅ Checklist |
| Testing | ⚠️ Examples | ✅ Full | ✅ Full | ✅ Commands |
| Troubleshooting | ⚠️ Brief | ✅ Full | ⚠️ Brief | ✅ Table |
| Commands | ❌ None | ✅ Full | ✅ Full | ✅ Primary |
| Docker | ⚠️ Brief | ✅ Full | ✅ Primary | ✅ Commands |

Legend:
- ✅ Primary/comprehensive coverage
- ⚠️ Brief/secondary coverage
- ❌ Not covered

---

## 🚀 Quick Links

- [Main README](./README.md)
- [Complete Setup Guide](./SETUP_GUIDE.md)
- [Docker Development Guide](./DOCKER_DEV.md)
- [Quick Reference Card](./QUICK_REFERENCE.md)
- [Package Configuration](./package.json)
- [Docker Compose](./docker-compose.yml)

---

**Last Updated:** 2026-02-03  
**Maintainer:** Documentation Team
