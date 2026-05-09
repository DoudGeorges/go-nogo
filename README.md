# Go/No-Go Experiment

PsychoPy Go/No-Go task built for a neuroscience class, measuring the effect of background music on impulsivity and concentration.

Three auditory conditions (silence, lyrics, no lyrics) are presented in random order. Behavioral data (RT, accuracy) and EEG (Muse headband) are recorded for each trial.

## Requirements

- Python 3.12+
- [PsychoPy](https://www.psychopy.org/)
- [Pygame](https://www.pygame.org/)

## Usage

Run the experiment:

```bash
python go_nogo.py
```

Analyze the ERP data in Jupyter:

```bash
jupyter notebook erp_analysis.ipynb
```

## Input

`conditions.csv` defines the experimental blocks (one row per condition).

## Output

Each session generates a CSV file in `data/`, named by session timestamp (e.g. `20260325_2149.csv`). Each row is one trial and contains the condition, reaction time, accuracy, and EEG sync timestamps.

Muse EEG recordings are stored in `muse/` with matching filenames. The notebook pairs them automatically.

## License

MIT
