PY ?= python3

.PHONY: setup figures check clean

setup:
	$(PY) -m venv .venv
	.venv/bin/pip install -q -r requirements.txt
	@echo "activate with: source .venv/bin/activate"

figures:
	cd scripts && $(PY) fig1_label.py && $(PY) fig2.py && $(PY) fig3.py && $(PY) fig4.py \
	  && $(PY) fig5.py && $(PY) fig6.py

check:
	cd scripts && $(PY) verify_all.py

clean:
	rm -f figures/Figure*.pdf figures/Figure*.png figures/*.ticks.json
	rm -f data/sensitivity.json
	find . -name __pycache__ -type d -exec rm -rf {} +
