# Zscaler AI Guard integrations — local checks and API tests
# Run from repository root: make help

ROOT       := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON     ?= python3
PIP        ?= pip3

# ANSI (cyan); use printf '%b' so escapes work. No tput — keeps CI/log output clean.
COLOR_ZSCALER := \033[1;36m
COLOR_RESET   := \033[0m

# Cline hook scripts have no .py extension
CLINE_HOOKS := UserPromptSubmit PreToolUse PostToolUse TaskComplete

.PHONY: help deps-gha deps-windsurf deps-cline deps-cursor \
	compile-anthropic compile-cursor compile-cline compile-windsurf \
	compile-github-actions compile-jenkins test-compile \
	run-policy-gha run-policy-jenkins \
	test-policy-gha test-policy-jenkins test-policy-all \
	test-cursor test-cline test-windsurf test-all check

help:
	@printf '%b\n' "$(COLOR_ZSCALER)"
	@printf '%s\n' '  ______              _           '
	@printf '%s\n' ' |___  /             | |          '
	@printf '%s\n' '    / / ___  ___ __ _| | ___ _ __ '
# Embedded single quote in art: close quote, '"'"', reopen — do not use echo "..." (backticks run commands)
	@printf '%s\n' '   / / / __|/ __/ _` | |/ _ \ '"'"'__|'
	@printf '%s\n' '  / /__\__ \ (_| (_| | |  __/ |   '
	@printf '%s\n' ' /_____|___/\___\__,_|_|\___|_|   '
	@printf '%s\n' '                                  '
	@printf '%b\n' "$(COLOR_RESET)"
	@echo 'Zscaler AI Guard - make targets'
	@echo ""
	@echo "  make check / test-compile   All compile-* targets (syntax, no API)"
	@echo "  make compile-anthropic|cursor|cline|windsurf|github-actions|jenkins  Per-vendor syntax"
	@echo "  make deps-gha               pip install github-actions/requirements.txt"
	@echo "  make run-policy-gha         Run scan only (use after deps-gha; CI uses this)"
	@echo "  make run-policy-jenkins     Jenkins/ copy scan only"
	@echo "  make test-policy-gha        deps + run-policy-gha (needs AIGUARD_API_KEY)"
	@echo "  make test-policy-jenkins    deps + run-policy-jenkins"
	@echo "  make test-policy-all        Both policy scans (2x API usage)"
	@echo "  make test-cursor            Run local_dev/Cursor/test_prompts.sh"
	@echo "  make test-cline             Run local_dev/Cline/test_hooks.sh"
	@echo "  make test-windsurf          Run local_dev/Windsurf/test_pre_user_prompt.sh"
	@echo "  make test-all               compile + policy-all + cline + windsurf + cursor"
	@echo ""
	@echo "Export AIGUARD_API_KEY (and optional AIGUARD_CLOUD) for API targets."

check: test-compile

compile-anthropic:
	@echo "==> Syntax — Anthropic (Claude Code hooks)"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q Anthropic/claude-code-aiguard/hooks

compile-cursor:
	@echo "==> Syntax — Cursor hooks"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q Cursor/hooks

compile-cline:
	@echo "==> Syntax — Cline hooks"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q Cline/.clinerules/hooks/aiguard_utils.py
	@for h in $(CLINE_HOOKS); do \
		$(PYTHON) -m py_compile "$(ROOT)/Cline/.clinerules/hooks/$$h"; \
	done

compile-windsurf:
	@echo "==> Syntax — Windsurf hooks"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q Windsurf/.windsurf/hooks

compile-github-actions:
	@echo "==> Syntax — github-actions scripts"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q github-actions/scripts

compile-jenkins:
	@echo "==> Syntax — Jenkins declarative-pipeline scripts"
	cd "$(ROOT)" && $(PYTHON) -m compileall -q Jenkins/declarative-pipeline/scripts

test-compile: compile-anthropic compile-cursor compile-cline compile-windsurf compile-github-actions compile-jenkins
	@echo "==> test-compile OK"

deps-gha:
	$(PIP) install -r "$(ROOT)/github-actions/requirements.txt"

deps-windsurf:
	$(PIP) install -r "$(ROOT)/Windsurf/requirements.txt"

deps-cline:
	$(PIP) install -r "$(ROOT)/Cline/requirements.txt"

deps-cursor:
	$(PIP) install -r "$(ROOT)/Cursor/requirements.txt"

run-policy-gha:
	@echo "==> AI Guard policy scan (github-actions)"
	cd "$(ROOT)/github-actions" && $(PYTHON) scripts/scan_policy.py --config config/test-prompts.yaml

run-policy-jenkins:
	@echo "==> AI Guard policy scan (Jenkins declarative-pipeline)"
	cd "$(ROOT)/Jenkins/declarative-pipeline" && $(PYTHON) scripts/scan_policy.py --config config/test-prompts.yaml

test-policy-gha: deps-gha run-policy-gha

test-policy-jenkins: deps-gha run-policy-jenkins

test-policy-all: deps-gha run-policy-gha run-policy-jenkins

test-cursor:
	@echo "==> Cursor hook stdin samples (local_dev/Cursor/test_prompts.sh)"
	cd "$(ROOT)" && bash local_dev/Cursor/test_prompts.sh

test-cline:
	@echo "==> Cline hook tests"
	cd "$(ROOT)" && bash local_dev/Cline/test_hooks.sh

test-windsurf:
	@echo "==> Windsurf pre_user_prompt samples"
	cd "$(ROOT)" && bash local_dev/Windsurf/test_pre_user_prompt.sh

# Full local integration sweep (requires AIGUARD_API_KEY; hits API many times)
test-all: test-compile test-policy-all test-cline test-windsurf test-cursor
