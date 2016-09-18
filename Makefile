# This makefile has been created to help developers perform common actions.
# It assumes it is operating in an environment, such as a virtual env,
# where the python command links to Python2.7 executable - because buildbot
# is currently restricted to Python2.7 due to twisted.spread.

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
	@python setup.py sdist


# help: dist.test                      - test a source distribution package
dist.test: dist
	@cd dist && ./test.bash ./buildbot_prometheus-*.tar.gz


# help: dist.upload                    - upload a source distribution package
dist.upload: clean
	@python setup.py sdist upload

# Keep these lines at the end of the file to retain nice help
# output formatting.
# help:
