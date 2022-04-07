pip install twine
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q src\robobosim.egg-info
python setup.py sdist bdist_wheel
python -m twine upload --repository testpypi dist/*