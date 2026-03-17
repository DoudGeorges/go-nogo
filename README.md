# Go/No-Go Experiment

A PsychoPy experiment developed as part of a neuroscience course. The goal is to investigate whether different types of background music affect cognitive performance (specifically impulsivity and concentration) during a Go/No-Go task.

Participants complete the task under three auditory conditions (silence, music with lyrics, and music without lyrics) in a randomized order. We record both behavioral data (reaction time, accuracy) and brain activity (EEG via the Muse headband) to compare performance across conditions.

Each participant reads the consent form, answers a short questionnaire, completes a practice block with feedback, and then completes three experimental blocks (one per condition, in randomized order).

Each block consists of 240 trials (75% Go, 25% No-Go) displaying the letters **M** (Go) and **W** (No-Go). Participants press **SPACE** for Go stimuli and withhold their response for No-Go stimuli.

## Requirements

- Python 3.10+
- [PsychoPy](https://www.psychopy.org/)

## Setup

```bash
conda create -n neuroscience python=3.10 -y
conda activate neuroscience
uv pip install psychopy
```

## Usage

Place your audio files (`lyrics.wav`, `no_lyrics.wav`) in the project root, then run:

```bash
python go_nogo.py
```

## Data Output

Each session generates two CSV files named using the session timestamp (e.g., `20260315_0034.csv`):

- `data/participants/` — demographics, questionnaire responses, and block order
- `data/trials/` — per-trial data including condition, reaction time, accuracy, and timestamps

## License

[MIT](LICENSE)
