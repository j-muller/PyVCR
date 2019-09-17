# Project configuration
PROJECT_NAME := pyvcr
PACKAGE_NAME := pyvcr
VERSION_FILE := $(PACKAGE_NAME)/__init__.py

TESTS_DIRECTORY := tests

# Call these functions before/after each target to maintain a coherent display
START_TARGET = @printf "[$(shell date +"%H:%M:%S")] %-40s" "$(1)"
END_TARGET := @printf "\033[32;1mOK\033[0m\n"

# Parameter expansion
PYTEST_OPTS ?=
SCL_COLLECTIONS := rh-python35

ENV_RUN := PYTHONUSERBASE=/dev/null
SCL := scl enable $(SCL_COLLECTIONS) --

TMP_DIR := ${CURDIR}/tmp_env
CI_DIR := ${CURDIR}/ci_env

BASE_DEPS := ${CURDIR}/base.lock
ADDITIONAL_DEPS := ${CURDIR}/additional.lock

.PHONY: help check_code_style check_doc_style check_pylint check_xenon \
        check_lint check_test check distclean clean doc dist \
        ci_check ci_doc \
        update_requirement update_base_requirement update_additional_requirement

# generate command list based on the "##" comment marked with the targets
help: ## Display list of targets and their documentation
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk \
		'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

doc: ## Build documentation
	$(call START_TARGET,Generating documentation)
	@sphinx-apidoc --force --output-dir=doc/source/api --module-first $(PACKAGE_NAME)
	@$(ENV_RUN) make -C doc html
	$(call END_TARGET)

check_code_style: ## Check code style
	$(call START_TARGET,Checking code style)
	@$(ENV_RUN) pycodestyle $(PACKAGE_NAME) $(TESTS_DIRECTORY)
	$(call END_TARGET)

check_doc_style: ## Check documentation style
	$(call START_TARGET,Checking doc style)
	@$(ENV_RUN) pydocstyle $(PACKAGE_NAME) $(TESTS_DIRECTORY)
	$(call END_TARGET)

check_pylint: ## Run pylint
	$(call START_TARGET,Checking pylint)
	@$(ENV_RUN) pylint --reports=no $(PACKAGE_NAME) $(TESTS_DIRECTORY)
	$(call END_TARGET)

check_xenon: ## Run xenon (code complexity)
	$(call START_TARGET,Checking xenon)
	@$(ENV_RUN) xenon $(PACKAGE_NAME) --no-assert
	$(call END_TARGET)

check_lint: check_code_style check_doc_style check_pylint check_xenon ## Check code style, documentation style, pylint and xenon

check_test: ## Run pytest
	$(call START_TARGET,Checking $(TESTS_DIRECTORY))
	@$(ENV_RUN) pytest --cov=$(PACKAGE_NAME) --cov-fail-under=0 --durations=10 \
		$(PYTEST_OPTS) $(PACKAGE_NAME) $(TESTS_DIRECTORY) doc/source/
	$(call END_TARGET)

check: check_lint check_test ## Run all checks (lint and tests)

distclean: clean ## Remove *.egg-info and apply clean
	$(call START_TARGET,Distribution cleaning)
	@rm -rf *.egg-info
	$(call END_TARGET)

clean: ## Remove temporary and build files
	$(call START_TARGET,Cleaning)
	@find . -type f -name '*.pyc' -delete
	@rm -rf dist/* .cache .eggs
	@rm -rf htmlcov .coverage
	@rm -rf doc/source/api
	@rm -rf $(TMP_DIR) $(CI_DIR)
	@$(ENV_RUN) make -C doc clean
	$(call END_TARGET)

dist: ## Create a source distribution
	$(call START_TARGET,Creating distribution)
	@$(ENV_RUN) $(SCL) python setup.py --quiet sdist --dist-dir _tmp_dist
	@mkdir -p dist
	@mv _tmp_dist/*.tar.gz dist/$(PACKAGE_NAME)-$$(git describe --always).tar.gz
	@rm -r _tmp_dist
	$(call END_TARGET)

update_base_requirement: ## Update project requirements based on setup.py
	$(call START_TARGET,Updating production requirements file)
	@rm -rf $(TMP_DIR)
	$(ENV_RUN) $(SCL) virtualenv-3.5 --system-site-packages $(TMP_DIR)
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip install -U pip setuptools wheel
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip install -e ${CURDIR}
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip freeze --all --exclude-editable > $(BASE_DEPS)
	@rm -r $(TMP_DIR)
	$(call END_TARGET)

# 1. Install additional packages with base requirements as constraint
# 2. Remove packages already present in base.lock
#    Exact match on version is not problematic because of -c above on base.lock
#    There is another check to ensure there is no overlap when installing ci_env
update_additional_requirement: $(BASE_DEPS)  ## Update additional requirements for test and doc
	$(call START_TARGET,Updating development requirements file)
	@rm -rf $(TMP_DIR)
	$(ENV_RUN) $(SCL) virtualenv-3.5 --system-site-packages $(TMP_DIR)
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip install -c $(BASE_DEPS) -U pip setuptools wheel
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip install -c $(BASE_DEPS) -e ${CURDIR}[test,doc]
	$(ENV_RUN) $(SCL) $(TMP_DIR)/bin/pip freeze --all --exclude-editable > $(ADDITIONAL_DEPS)
	@grep -v -f $(BASE_DEPS) $(ADDITIONAL_DEPS) > $(ADDITIONAL_DEPS).tmp
	@mv $(ADDITIONAL_DEPS).tmp $(ADDITIONAL_DEPS)
	@rm -r $(TMP_DIR)
	$(call END_TARGET)

update_requirement: update_base_requirement update_additional_requirement  ## Update requirement lock files

$(BASE_DEPS):
	$(MAKE) update_base_requirement

$(ADDITIONAL_DEPS):
	$(MAKE) update_additional_requirement

# Fails if base and additional files overlap
ci_env: $(BASE_DEPS) $(ADDITIONAL_DEPS) ## Build a CI environment
	$(ENV_RUN) $(SCL) virtualenv-3.5 --system-site-packages $(CI_DIR)
	$(ENV_RUN) $(SCL) $(CI_DIR)/bin/pip install --no-deps -c $(BASE_DEPS) pip setuptools wheel
	$(ENV_RUN) $(SCL) $(CI_DIR)/bin/pip install --no-deps -r $(BASE_DEPS) -r $(ADDITIONAL_DEPS)
	$(ENV_RUN) $(SCL) $(CI_DIR)/bin/pip install --no-deps -e ${CURDIR}
	$(ENV_RUN) $(SCL) $(CI_DIR)/bin/pip list
	$(ENV_RUN) $(SCL) $(CI_DIR)/bin/pip check

ci_check: ci_env ## Run all checks in the CI environment
	$(ENV_RUN) $(SCL) bash -c "source $(CI_DIR)/bin/activate && \
		$(MAKE) check \
		PYTEST_OPTS='-vv --junit-xml=junit.xml --cov $(PACKAGE_NAME) --cov-report xml:cov.xml'"
	$(ENV_RUN) $(SCL) bash -c "source $(CI_DIR)/bin/activate && \
			cobertura-clover-transform ${CURDIR}/cov.xml -o ${CURDIR}/clover.xml"

ci_doc: ci_env ## Build the documentation in the CI environment
	$(ENV_RUN) $(SCL) bash -c "source $(CI_DIR)/bin/activate && $(MAKE) doc"
