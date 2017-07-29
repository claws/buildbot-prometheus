# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to an appropriate Python.

# help: help                           - display this makefile's help information
help:
	@grep "^# help\:" Makefile | grep -v grep | sed 's/\# help\: //' | sed 's/\# help\://'

# help: clean                          - clean all files using .gitignore rules
clean:
	@git clean -X -f -d

# help: clean.scrub                    - clean all files, even untracked files
clean.scrub:
	git clean -x -f -d

# help: dist                           - create a source distribution package
dist: clean
	@python setup.py bdist_wheel

# help: dist.test                      - test a source distribution package
dist.test: dist
	@cd tests && ./test.bash ../dist/buildbot_prometheus-*-none-any.whl

# help: dist.upload                    - upload a source distribution package
dist.upload:
	@twine upload ./dist/buildbot_prometheus-*-none-any.whl

# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
