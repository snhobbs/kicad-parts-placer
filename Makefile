install:
	pip install -e .

push: build publish

build_wheel:
	python setup.py sdist bdist_wheel

publish: dist
	twine upload dist/*
