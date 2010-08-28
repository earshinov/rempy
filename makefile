.PHONY: all docs user-docs api-docs clean clean-docs clean-user-docs clean-api-docs clean

# Shortcuts

all:

docs: user-docs api-docs

clean: clean-docs

clean-docs: clean-user-docs clean-api-docs

# Main targets

user-docs:
	for file in doc/user-docs/*.txt; do \
		txt2tags --target=html --toc --encoding=utf-8 "$$file"; \
	done

clean-user-docs:
	-rm doc/user-docs/*.html

api-docs:
	cd doc; epydoc --config=epydoc.conf

clean-api-docs:
	-rm -r doc/api/
