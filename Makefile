.PHONY: setup test eval demo app sample
setup:  ; pip install -e ".[dev,ui]"
test:   ; python -m pytest -q
sample: ; python scripts/make_sample_paper.py
eval:   ; python -m paperqa eval data/sample_paper.pdf --llm extractive
demo:   ; bash scripts/make_demo.sh
app:    ; streamlit run app.py
