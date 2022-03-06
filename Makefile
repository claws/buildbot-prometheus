# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to an appropriate Python.

# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: buildbot_prometheus Makefile help
# help:

# help: help                    - display this makefile's help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'


# help: format                  - perform code style format
.PHONY: format
format:
	@black src/buildbot_prometheus tests setup.py

# help: check-format            - check code format compliance
.PHONY: check-format
check-format:
	@black --check src/buildbot_prometheus tests setup.py

# help: style                   - perform code style format
.PHONY: style
style: sort-imports format


# help: sort-imports            - apply import sort ordering
.PHONY: sort-imports
sort-imports:
	@isort . --profile black

# help: check-sort-imports      - check imports are sorted
.PHONY: check-sort-imports
check-sort-imports:
	@isort . --check-only --profile black

# help: dist                    - create a distribution package
.PHONY: dist
dist:
	@python setup.py bdist_wheel

# help: test-dist               - test a distribution package
.PHONY: test-dist
test-dist: dist
	@cd tests && ./test.bash ../dist/buildbot_prometheus-*-py3-none-any.whl

# help: upload-dist             - upload a distribution package
.PHONY: upload-dist
upload-dist:
	@twine upload ./dist/buildbot_prometheus-*-py3-none-any.whl

# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
