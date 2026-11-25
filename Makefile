film:
	python pipeline/run_all.py

validate:
	python pipeline/s0_validate.py

radio:
	python pipeline/radio_cut.py

costs:
	python pipeline/cost_summary.py