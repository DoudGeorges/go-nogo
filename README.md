# Go/No-Go Experiment

A PsychoPy experiment investigating how different types of background music affect cognitive performance (impulsivity and concentration) during a Go/No-Go task.

Participants complete the task under three auditory conditions (silence, music with lyrics, and music without lyrics) in a randomized order. We record both behavioral data (reaction time, accuracy) and brain activity (EEG via the Muse headband) to compare performance across conditions.

Each participant reads a consent form, answers a short questionnaire, completes a practice block with feedback, and then completes three experimental blocks in randomized order.

Block parameters (conditions, trial counts, go/nogo ratio) are defined in `conditions.csv`.

## Requirements

- Python 3.10+
- [PsychoPy](https://www.psychopy.org/)

## Usage

Double-click `lancer_experience.bat`, or run manually:

```bash
python go_nogo.py
```

See `LISEZMOI.txt` for detailed instructions.

## Input

`conditions.csv` defines each experimental block:

| Column | Description |
|---|---|
| `condition` | Internal condition key |
| `label` | Display name shown to participants |
| `audio_file` | Audio filename (empty for silence) |
| `n_trials` | Number of trials in the block |
| `go_ratio` | Proportion of Go trials (e.g. 0.75) |

## Output

Each session generates two CSV files in `data/`, named by session timestamp (e.g. `20260315_0034.csv`):

- `data/participants/` — demographics, questionnaire responses, and block order
- `data/trials/` — per-trial data including condition, reaction time, accuracy, and EEG sync timestamps

## License

[MIT](LICENSE)
