# Heritage Short
What it makes (one paragraph).
## Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add keys (see .env.example)
Requires FFmpeg 4.4+ with libass.
## Run
make film     (or: python pipeline/run_all.py)
Outputs: outputs/final/film_vertical.mp4, film_horizontal.mp4
## Regenerate one shot
Edit its image_prompt or narration in storyboard.json, run make film. Only that shot regenerates.
## Optional GPU steps
Wan clips and ACE-Step music are made on Kaggle (notebooks/). Without them the pipeline uses Ken Burns and requires outputs/music/score.*.
## Costs and limits
See COSTS.md.