import csv
import os
import random
import time
import datetime
import ctypes
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

try:
    from psychopy import visual, core, event, logging
except ModuleNotFoundError:
    print("PsychoPy introuvable.")
    print()
    print("Pour lancer manuellement :")
    print("1. Ouvrir PsychoPy")
    print("2. Aller en mode Coder")
    print("3. Ouvrir go_nogo.py")
    print("4. Cliquer sur le bouton vert")
    print()
    input("Appuyez sur une touche pour continuer . . . ")
    raise SystemExit(1)

logging.console.setLevel(logging.ERROR)

USE_LSL = False

ITI_MIN = 0.800
ITI_MAX = 1.200
STIMULUS_DUR = 0.800
BASELINE_DUR = 2.000

GO_STIMULUS = "M"
NOGO_STIMULUS = "W"
PRACTICE_TRIALS = 4
RESPONSE_KEY = "space"

CONDITIONS_CSV = "conditions.csv"

FONT = "Arial"
COLOR_BG = [-1, -1, -1]
COLOR_TEXT = "white"
COLOR_ACCENT = "dodgerblue"
COLOR_HINT = [0.4, 0.4, 0.4]
COLOR_INPUT_BG = [-0.85, -0.85, -0.85]
SIZE_BODY = 0.040
SIZE_HEADING = 0.050
SIZE_HINT = 0.028
SIZE_STIMULUS = 0.15
WRAP = 1.4

COLUMNS = [
    "block",
    "condition",
    "trial",
    "trial_type",
    "response",
    "rt_ms",
    "accuracy",
    "stimulus_time",
    "response_time",
    "stimulus_iso",
    "stimulus_unix",
    "age",
    "gender",
    "music_frequency",
    "studies_with_music",
    "concentration_effect",
    "block_order",
]

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_lsl_outlet = None


def load_conditions(csv_path: Path) -> list:
    required = {"condition", "label", "n_trials", "go_ratio"}
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not required.issubset(set(reader.fieldnames or [])):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(
                f"conditions.csv is missing required columns: {missing}"
            )
        for row in reader:
            rows.append({
                "condition": row["condition"].strip(),
                "label": row["label"].strip(),
                "audio_file": row.get("audio_file", "").strip() or None,
                "n_trials": int(row["n_trials"]),
                "go_ratio": float(row["go_ratio"]),
            })
    if not rows:
        raise ValueError("conditions.csv contains no rows")
    return rows


def init_lsl():
    global _lsl_outlet
    if not USE_LSL:
        return
    from pylsl import StreamInfo, StreamOutlet
    info = StreamInfo("PsychoPyMarkers", "Markers", 1, 0, "string", "gonogo_erp")
    _lsl_outlet = StreamOutlet(info)


def send_marker(name: str):
    t = core.getTime()
    if USE_LSL and _lsl_outlet is not None:
        _lsl_outlet.push_sample([name])
    logging.data(f"MARKER: {name} @ {t:.6f}")


def _has_consecutive_nogo(trials: list) -> bool:
    for i in range(len(trials) - 1):
        if trials[i]["trial_type"] == "nogo" and trials[i + 1]["trial_type"] == "nogo":
            return True
    return False


def generate_trials(n_go: int, n_nogo: int) -> list:
    trials = (
        [{"stimulus": GO_STIMULUS, "trial_type": "go"} for _ in range(n_go)]
        + [{"stimulus": NOGO_STIMULUS, "trial_type": "nogo"} for _ in range(n_nogo)]
    )
    for _ in range(1000):
        random.shuffle(trials)
        if not _has_consecutive_nogo(trials):
            return trials
    logging.warning("Could not avoid consecutive no-go trials after 1000 attempts")
    return trials


def load_audio(filename: str | None):
    if filename is None:
        return None
    filepath = SCRIPT_DIR / filename
    if not filepath.exists():
        logging.warning(
            f"Audio file '{filepath}' not found - assuming external playback"
        )
        return None
    return str(filepath)


_now = datetime.datetime.now()
participant_id = _now.strftime("%Y%m%d_%H%M")
exp_info = {}

csv_path = DATA_DIR / f"{participant_id}.csv"

csv_file = None
csv_writer = None
_first_trial = True

_user32 = ctypes.windll.user32
_screen_w = _user32.GetSystemMetrics(0)
_screen_h = _user32.GetSystemMetrics(1)

win = visual.Window(
    size=(_screen_w, _screen_h - 1),
    fullscr=False,
    color=COLOR_BG,
    units="height",
    allowGUI=False,
    monitor="testMonitor",
    checkTiming=False,
    useRetina=False,
    pos=(0, 0),
)
win.mouseVisible = False


_hwnd = win.winHandle._hwnd
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_HWND_TOPMOST = -1
_user32.SetWindowPos(_hwnd, _HWND_TOPMOST, 0, 0, 0, 0, _SWP_NOSIZE | _SWP_NOMOVE)

visual.TextStim(
    win, text="Préparation de l'expérience…",
    height=SIZE_BODY, color=COLOR_TEXT, font=FONT,
).draw()
win.flip()
core.wait(0.5)

csv_file = open(csv_path, "w", newline="", encoding="utf-8-sig")
csv_writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
csv_writer.writeheader()

stimulus_stim = visual.TextStim(
    win, text="", height=SIZE_STIMULUS, color=COLOR_TEXT, font=FONT, bold=True,
)
body_stim = visual.TextStim(
    win, text="", height=SIZE_BODY, color=COLOR_TEXT,
    wrapWidth=WRAP, alignText="center", font=FONT,
)
feedback_stim = visual.TextStim(
    win, text="", height=SIZE_HEADING, color=COLOR_TEXT,
    alignText="center", font=FONT,
)
consent_stim = visual.TextStim(
    win, text="", height=SIZE_HINT + 0.002, color=COLOR_TEXT,
    wrapWidth=WRAP, alignText="center", font=FONT,
)

trial_clock = core.Clock()
global_clock = core.Clock()

init_lsl()


def abort_and_cleanup():
    if csv_file and not csv_file.closed:
        csv_file.close()
    if csv_path.exists():
        csv_path.unlink()
    try:
        win.close()
    except Exception:
        pass
    core.quit()


def wait_or_escape(duration):
    timer = core.CountdownTimer(duration)
    while timer.getTime() > 0:
        if event.getKeys(keyList=["escape"]):
            abort_and_cleanup()
        core.wait(min(0.05, max(0.001, timer.getTime())), hogCPUperiod=0.02)


def show_screen(message, keys=None, stim=None):
    if keys is None:
        keys = ["space"]
    event.clearEvents()
    text_stim = stim or body_stim
    text_stim.text = message
    text_stim.draw()
    win.flip()
    key_list = None if keys == "any" else keys + ["escape"]
    resp = event.waitKeys(keyList=key_list)
    if resp and "escape" in resp:
        abort_and_cleanup()
    return resp


CONSENT_TEXT = (
    "Cette étude est menée par des étudiant(e)s du Collège Dawson\u00a0: "
    "Maha Ahmed, Mila Degand et Édouard Chassé. Elle a pour but "
    "d'évaluer l'impact de différents types de musique sur "
    "l'impulsivité et la concentration lors d'une tâche cognitive."
    "\n\n"
    "Nous vous demanderons d'effectuer la tâche Go/No-Go à "
    "trois reprises, dans un ordre aléatoire. Chaque essai "
    "consistera en une période de 3\u00a0minutes\u00a0: (1)\u00a0avec de la musique "
    "comprenant des paroles, (2)\u00a0avec de la musique sans paroles, "
    "ou (3)\u00a0sans musique. Nous enregistrerons également l'activité "
    "électrique de votre cerveau à l'aide du bandeau Muse. Le tout "
    "devrait prendre environ 15\u00a0minutes."
    "\n\n"
    "Les informations recueillies ne serviront qu'à cette "
    "étude. Votre participation est volontaire et vous pouvez "
    "arrêter à tout moment en appuyant sur «\u00a0ESC\u00a0». Vos données "
    "demeureront confidentielles et anonymes."
    "\n\n"
    "Si vous avez des questions à propos de cette étude ou désirez "
    "obtenir des informations sur ses résultats, veuillez contacter "
    "la Dre\u00a0Hélène Nadeau à l'adresse hnadeau@dawsoncollege.qc.ca."
    "\n\n"
    "En appuyant sur «\u00a0ESPACE\u00a0», vous consentez à participer "
    "et confirmez avoir lu cette lettre. "
    "En appuyant sur «\u00a0ESC\u00a0», vous refusez de participer "
    "pour le moment."
)

HINT_SLIDER = "Cliquez sur l'échelle, puis appuyez sur «\u00a0ESPACE\u00a0» pour confirmer."
HINT_TEXT = "Tapez votre réponse, puis appuyez sur «\u00a0ESPACE\u00a0» pour confirmer."

INSTRUCTIONS = (
    "INSTRUCTIONS\n\n"
    "Des lettres vont apparaître brièvement au centre\n"
    "de l'écran. Votre tâche est simple\u00a0:\n\n"
    f"Lettre «\u00a0{GO_STIMULUS}\u00a0» → appuyez sur «\u00a0ESPACE\u00a0»\n"
    "le plus rapidement possible.\n\n"
    f"Lettre «\u00a0{NOGO_STIMULUS}\u00a0» → ne faites rien,\n"
    "n'appuyez pas.\n\n"
    "Chaque lettre apparaît seulement un court instant.\n"
    "Essayez d'être à la fois rapide et précis(e).\n\n"
    "Vous ferez d'abord un court bloc de pratique\n"
    "pour vous familiariser avec la tâche.\n\n\n"
    "Appuyez sur «\u00a0ESPACE\u00a0» pour commencer la pratique."
)


def ask_slider(question: str, labels: list, ticks: list = None) -> float:
    win.mouseVisible = True
    q_text = visual.TextStim(
        win, text=question, height=SIZE_BODY, color=COLOR_TEXT,
        wrapWidth=WRAP, pos=(0, 0.25), alignText="center", font=FONT,
    )
    if ticks is None:
        ticks = list(range(1, len(labels) + 1))
    slider = visual.Slider(
        win, ticks=ticks, labels=labels, pos=(0, -0.05),
        size=(1.2, 0.06), granularity=1.0,
        style="rating", color=COLOR_TEXT, fillColor=COLOR_ACCENT,
        borderColor=COLOR_TEXT, labelHeight=SIZE_HINT, font=FONT,
    )
    hint = visual.TextStim(
        win, text=HINT_SLIDER,
        height=SIZE_HINT, color=COLOR_HINT, pos=(0, -0.35), font=FONT,
    )
    while True:
        q_text.draw()
        slider.draw()
        hint.draw()
        win.flip()
        keys = event.getKeys(keyList=["space", "return", "escape"])
        if "escape" in keys:
            abort_and_cleanup()
        if ("space" in keys or "return" in keys) and slider.getRating() is not None:
            win.mouseVisible = False
            return slider.getRating()


def ask_text_input(question: str, numeric_only: bool = False) -> str:
    q_text = visual.TextStim(
        win, text=question, height=SIZE_BODY, color=COLOR_TEXT,
        wrapWidth=WRAP, pos=(0, 0.15), alignText="center", font=FONT,
    )
    box_y = -0.02
    input_box = visual.Rect(
        win, width=0.6, height=0.07, pos=(0, box_y),
        lineColor=COLOR_ACCENT, lineWidth=2,
        fillColor=COLOR_INPUT_BG,
    )
    input_display = visual.TextStim(
        win, text="", height=SIZE_BODY, color=COLOR_TEXT,
        pos=(0, box_y), font=FONT,
    )
    hint = visual.TextStim(
        win, text=HINT_TEXT,
        height=SIZE_HINT, color=COLOR_HINT, pos=(0, -0.2), font=FONT,
    )
    user_input = ""
    while True:
        input_display.text = user_input
        q_text.draw()
        input_box.draw()
        input_display.draw()
        hint.draw()
        win.flip()
        keys = event.getKeys()
        for key in keys:
            if key == "escape":
                abort_and_cleanup()
            elif key in ("space", "return") and user_input:
                return user_input
            elif key == "backspace":
                user_input = user_input[:-1]
            elif len(key) == 1:
                if numeric_only and not key.isdigit():
                    continue
                user_input += key


def run_trial(trial_info: dict, condition_csv: str, trial_num: int,
              feedback: bool = False) -> dict:
    event.clearEvents()
    stimulus_stim.text = trial_info["stimulus"]
    stimulus_stim.draw()
    win.flip()
    onset_time = global_clock.getTime()
    onset_iso = datetime.datetime.now().isoformat()
    onset_unix = time.time()
    trial_clock.reset()
    send_marker(f"stimulus_onset_{trial_info['trial_type']}")

    response_key = None
    rt = None

    stim_timer = core.CountdownTimer(STIMULUS_DUR)
    while stim_timer.getTime() > 0:
        keys = event.getKeys(keyList=[RESPONSE_KEY, "escape"], timeStamped=trial_clock)
        if keys:
            if keys[0][0] == "escape":
                abort_and_cleanup()
            response_key = keys[0][0]
            rt = keys[0][1]
            break
        core.wait(0.001, hogCPUperiod=0.001)

    win.flip()
    send_marker("stimulus_offset")

    response_time = global_clock.getTime() if response_key else None
    if response_key:
        send_marker("response")

    is_go = trial_info["trial_type"] == "go"
    correct = (is_go and response_key is not None) or (not is_go and response_key is None)

    if feedback:
        if is_go and response_key is None:
            feedback_stim.text = "Trop lent"
            feedback_stim.color = "orange"
        elif correct:
            feedback_stim.text = "Bonne réponse"
            feedback_stim.color = "lime"
        else:
            feedback_stim.text = "Mauvaise réponse"
            feedback_stim.color = "red"
        feedback_stim.draw()
        win.flip()
        wait_or_escape(0.8)

    win.flip()
    wait_or_escape(random.uniform(ITI_MIN, ITI_MAX))

    return {
        "condition": condition_csv,
        "trial": trial_num,
        "trial_type": trial_info["trial_type"],
        "response": RESPONSE_KEY if response_key else "",
        "rt_ms": round(rt * 1000, 1) if rt is not None else "",
        "accuracy": 1 if correct else 0,
        "stimulus_time": round(onset_time, 6),
        "response_time": round(response_time, 6) if response_time else "",
        "stimulus_iso": onset_iso,
        "stimulus_unix": onset_unix,
    }


def write_trial_row(result: dict, block_num: int):
    global _first_trial
    row = {"block": block_num}
    row.update(result)
    if _first_trial:
        row.update(exp_info)
        _first_trial = False
    csv_writer.writerow(row)
    csv_file.flush()


try:
    show_screen(CONSENT_TEXT, keys=["space"], stim=consent_stim)

    age = ask_text_input("Quel est votre âge\u00a0?", numeric_only=True)
    exp_info["age"] = age

    gender = ask_slider(
        "Quel est votre genre\u00a0?",
        labels=["Homme", "Femme", "Non-binaire", "Autre", "Préfère ne\npas répondre"],
        ticks=[1, 2, 3, 4, 5],
    )
    gender_map = {
        1: "male", 2: "female", 3: "non-binary",
        4: "other", 5: "prefer_not_to_say",
    }
    exp_info["gender"] = gender_map.get(int(round(gender)), str(gender))

    exclusion = ask_slider(
        "Avez-vous reçu un diagnostic de TDAH,\n"
        "de troubles neurologiques ou auditifs,\n"
        "ou portez-vous des appareils auditifs\u00a0?",
        labels=["Non", "Oui"],
        ticks=[1, 2],
    )
    if int(round(exclusion)) == 2:
        show_screen(
            "Malheureusement, vous ne pouvez pas\n"
            "participer à cette étude en raison\n"
            "des critères d'exclusion.\n\n"
            "Merci de votre intérêt\u00a0!\n\n"
            "Appuyez sur n'importe quelle touche\n"
            "pour quitter.",
            keys="any",
        )
        abort_and_cleanup()

    music_freq = ask_slider(
        "En moyenne, combien d'heures par jour\nécoutez-vous de la musique\u00a0?",
        labels=["0-1\u00a0h", "1-2\u00a0h", "2-3\u00a0h", "3-4\u00a0h", "4\u00a0h+"],
        ticks=[1, 2, 3, 4, 5],
    )
    music_freq_map = {1: "0-1h", 2: "1-2h", 3: "2-3h", 4: "3-4h", 5: "4h+"}
    exp_info["music_frequency"] = music_freq_map.get(int(round(music_freq)), str(music_freq))

    study_music = ask_slider(
        "Écoutez-vous habituellement de la musique\nlorsque vous étudiez\u00a0?",
        labels=["Non", "Oui"],
        ticks=[1, 2],
    )
    exp_info["studies_with_music"] = "yes" if int(round(study_music)) == 2 else "no"

    concentration_effect = ask_slider(
        "Dans quelle mesure estimez-vous que la musique\n"
        "affecte votre concentration lorsque vous étudiez\u00a0?",
        labels=["Très\nnégativement", "Négativement", "Aucun\neffet",
                "Positivement", "Très\npositivement"],
        ticks=[1, 2, 3, 4, 5],
    )
    conc_map = {
        1: "very_negative", 2: "negative", 3: "neutral",
        4: "positive", 5: "very_positive",
    }
    exp_info["concentration_effect"] = conc_map.get(
        int(round(concentration_effect)), str(concentration_effect),
    )

    show_screen(INSTRUCTIONS, keys=["space"])

    practice_n_go = max(1, int(PRACTICE_TRIALS * 0.80))
    practice_n_nogo = max(1, PRACTICE_TRIALS - practice_n_go)
    practice_trials = generate_trials(practice_n_go, practice_n_nogo)
    correct_count = 0

    win.flip()
    wait_or_escape(random.uniform(ITI_MIN, ITI_MAX))

    for i, trial in enumerate(practice_trials, start=1):
        result = run_trial(trial, "practice", i, feedback=True)
        if result["accuracy"] == 1:
            correct_count += 1

    accuracy_pct = correct_count / len(practice_trials) * 100

    show_screen(
        "Fin du bloc de pratique.\n\n"
        f"Votre précision\u00a0: {accuracy_pct:.0f}\u00a0%\n\n"
        "Les blocs expérimentaux vont\n"
        "maintenant commencer.\n\n"
        "Appuyez sur «\u00a0ESPACE\u00a0» pour continuer.",
        keys=["space"],
    )

    conditions = load_conditions(SCRIPT_DIR / CONDITIONS_CSV)
    block_order = conditions.copy()
    random.shuffle(block_order)
    exp_info["block_order"] = ",".join(
        cond["condition"] for cond in block_order
    )

    for block_idx, cond in enumerate(block_order, start=1):
        label = cond["label"]
        condition_key = cond["condition"]

        show_screen(
            f"Bloc {block_idx} / {len(block_order)} - {label}\n\n"
            "Fixez le centre de l'écran.\n"
            "La tâche commencera automatiquement\n"
            "après quelques secondes.\n\n"
            "Appuyez sur «\u00a0ESPACE\u00a0» pour commencer.",
            keys=["space"],
        )

        audio_path = load_audio(cond["audio_file"])
        audio_playing = False
        if audio_path is not None:
            try:
                import pygame.mixer as _mixer
                if not _mixer.get_init():
                    _mixer.init(frequency=48000, size=-16, channels=2, buffer=2048)
                _mixer.music.load(audio_path)
                _mixer.music.play(loops=-1)
                audio_playing = True
            except Exception:
                logging.warning(f"Could not play audio for condition '{condition_key}'")

        send_marker(f"baseline_start_{condition_key}")
        win.flip()
        wait_or_escape(BASELINE_DUR)
        send_marker(f"baseline_end_{condition_key}")

        send_marker(f"block_start_{condition_key}")
        n_go = max(1, int(cond["n_trials"] * cond["go_ratio"]))
        n_nogo = max(1, cond["n_trials"] - n_go)
        trials = generate_trials(n_go, n_nogo)

        win.flip()
        wait_or_escape(random.uniform(ITI_MIN, ITI_MAX))

        for trial_num, trial_data in enumerate(trials, start=1):
            result = run_trial(trial_data, condition_key, trial_num)
            write_trial_row(result, block_idx)

        send_marker(f"block_end_{condition_key}")

        if audio_playing:
            try:
                import pygame.mixer as _mixer
                _mixer.music.stop()
            except Exception:
                pass

        if block_idx < len(block_order):
            show_screen(
                f"Fin du bloc {block_idx}.\n\n"
                "Prenez une courte pause si nécessaire.\n"
                "Lorsque vous êtes prêt(e),\n"
                "appuyez sur «\u00a0ESPACE\u00a0» pour continuer.",
                keys=["space"],
            )

    show_screen(
        "L'expérience est terminée.\n\n"
        "Merci beaucoup pour votre participation\u00a0!\n\n"
        "Veuillez aviser le ou la chercheur(e)\n"
        "que vous avez terminé.\n\n"
        "Appuyez sur «\u00a0ESPACE\u00a0» pour quitter.",
        keys=["space"],
    )

    csv_file.close()
    win.close()
    core.quit()

finally:
    if csv_file and not csv_file.closed:
        csv_file.close()
    try:
        win.close()
    except Exception:
        pass
