### This script is used to generate annotated event_files for the mario dataset from the pkl sidecars.

import argparse
import os
import os.path as op
import retro
import pandas as pd
import pickle
import numpy as np
import json

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--datapath",
    type=str,
    help="Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.",
)

parser.add_argument(
    "-r",
    "--replays_path",
    type=str,
    help="Path to the replays dataset, containing .json files and sidecars with game variables.",
)

parser.add_argument(
    "-c",
    "--clips_path",
    default=None,
    type=str,
    help="Path to the scenes dataset, containing JSON files with info about the start and end positions of each scene clip.",
)

parser.add_argument(
    "-o",
    "--output_path",
    default="outputdata/annotated_events",
    type=str,
    help="Path to save the annotated events files. If not specified, saves in the same folder as the input events.tsv files.",
)


def create_runevents(runvars, run_id, events_dataframe, CLIPS_PATH=None, FS=60):
    """Create a BIDS compatible events dataframe from game variables and start/duration info of repetitions

    Parameters
    ----------
    runvars : list
        A list of repvars dicts, corresponding to the different repetitions of a run. Each repvar must have it's own duration and onset.
    events_dataframe : pandas.DataFrame
        A BIDS-formatted DataFrame specifying the onset and duration of each repetition.
    FS : int
        The sampling rate of the .bk2 file
    get_actions : boolean
        If True, generates actions events based on key presses
    get_healthloss : boolean
        If True, generates health loss events based on changes on the "lives" variable
    get_kills : boolean
        If True, generates events indicating when an enemy has been killed (based on score increase)

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format.
    """
    all_df = [events_dataframe]
    for idx, repvars in enumerate(runvars):
        n_frames_total = len(repvars["START"])
        repvars["rep_onset"] = [events_dataframe["onset"][idx]]
        repvars["rep_duration"] = n_frames_total / FS

        if len(repvars.keys()) > 0:  # Check if repetition logs are available
            # Actions
            ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "START", "SELECT"]
            for act in ACTIONS:
                temp_df = generate_key_events(repvars, act, FS=FS)
                temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
                all_df.append(temp_df)

            # Kills
            temp_df = generate_kill_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            all_df.append(temp_df)

            # Hits taken
            temp_df = generate_hits_taken_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            all_df.append(temp_df)

            # Bricks smashed
            temp_df = generate_bricks_smashed_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            all_df.append(temp_df)

            # Coins collected
            temp_df = generate_coin_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            all_df.append(temp_df)

            # Powerups
            temp_df = generate_powerup_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            all_df.append(temp_df)

            # Scenes
            if CLIPS_PATH is not None:
                temp_df = generate_scene_events(repvars, idx, run_id, CLIPS_PATH, FS=FS)
                temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
                all_df.append(temp_df)

    try:
        events_df = pd.concat(all_df).sort_values(by="onset").reset_index(drop=True)
    except ValueError:
        print("No bk2 files available for this run. Returning empty df.")
        events_df = pd.DataFrame()
    return events_df


def generate_key_events(repvars, key, FS=60):
    """Create a BIDS compatible events dataframe containing key (actions) events

    Parameters
    ----------
    repvars : list
        A dict containing all the variables of a single repetition
    key : string
        Name of the action variable to process
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format containing the
        corresponding action events.
    """

    var = np.multiply(repvars[key], 1)
    # always keep the first and last value as 0 so diff will register the state transition
    var[0] = 0
    var[-1] = 0

    var_bin = [int(val) for val in var]
    diffs = list(np.diff(var_bin, n=1))
    presses = [round(i / FS, 3) for i, x in enumerate(diffs) if x == 1]
    releases = [round(i / FS, 3) for i, x in enumerate(diffs) if x == -1]
    frame_start = [i for i, x in enumerate(diffs) if x == 1]
    frame_stop = [i for i, x in enumerate(diffs) if x == -1]
    onset = presses
    level = [repvars["level"] for x in onset]
    duration = [round(releases[i] - presses[i], 3) for i in range(len(presses))]
    trial_type = ["{}".format(key) for i in range(len(presses))]
    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_kill_events(repvars, FS=60):
    """Create a BIDS compatible events dataframe containing kill events.
    Parameters
    ----------
    repvars : list
        A dict containing all the variables of a single repetition.
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format containing the
        kill events.
    """
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    killvals_dict = {4: "stomp", 34: "impact", 132: "kick"}

    n_frames_total = len(repvars["START"])
    for frame_idx in range(n_frames_total - 1):
        for ii in range(6):
            curr_val = repvars[f"enemy_kill3{ii}"][frame_idx]
            next_val = repvars[f"enemy_kill3{ii}"][frame_idx + 1]
            if curr_val in [4, 34, 132] and curr_val != next_val:
                killstring = f"Kill/{killvals_dict[curr_val]}"
                if ii == 5:
                    if repvars["powerup_yes_no"] == 0:
                        onset.append(frame_idx / FS)
                        duration.append(0)
                        trial_type.append(killstring)
                        level.append(repvars["level"])
                        frame_start.append(frame_idx)
                        frame_stop.append(frame_idx)
                else:
                    onset.append(frame_idx / FS)
                    duration.append(0)
                    trial_type.append(killstring)
                    level.append(repvars["level"])
                    frame_start.append(frame_idx)
                    frame_stop.append(frame_idx)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_hits_taken_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    # Powerup lost
    diff_state = list(np.diff(repvars["powerstate"]))
    for idx_val, val in enumerate(diff_state):
        if val < -10000:
            onset.append(idx_val / FS)
            duration.append(0)
            trial_type.append("Hit/powerup_lost")
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    # Lives lost
    diff_lives = list(np.diff(repvars["lives"]))
    for idx_val, val in enumerate(diff_lives):
        if val < 0:
            onset.append(idx_val / FS)
            duration.append(0)
            trial_type.append("Hit/life_lost")
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_bricks_smashed_events(repvars, FS=60):

    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    score_increments = list(np.diff(repvars["score"]))
    for idx_val, inc in enumerate(score_increments):
        if inc == 5:
            if repvars["jump_airborne"][idx_val] == 1:
                onset.append(idx_val / FS)
                duration.append(0)
                trial_type.append("Brick_smashed")
                level.append(repvars["level"])
                frame_start.append(idx_val)
                frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_coin_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    diff_coins = np.diff(repvars["coins"])
    for idx_val, val in enumerate(diff_coins):
        if val > 0:
            onset.append(idx_val / FS)
            duration.append(0)
            trial_type.append("Coin_collected")
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_powerup_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    """ ### Currently broken
    diff_powerup = np.diff(repvars['powerup_yes_no'])
    # powerup on screen events
    for idx, val in enumerate(repvars['powerup_yes_no'][:-1]):
        if val == 46:
            idx_stop = idx
            while diff_powerup[idx_stop] != -46:
                idx_stop += 1
            onset.append(idx/FS)
            duration.append((idx_stop-idx)/FS)
            trial_type.append('Powerup_on_screen')
            level.append(repvars['level'])
    """
    # powerup collect events
    for idx, val in enumerate(repvars["player_state"][:-1]):
        if val in [9, 12, 13]:
            if repvars["player_state"][idx + 1] != val:
                onset.append(idx / FS)
                duration.append(0)
                trial_type.append("Powerup_collected")
                level.append(repvars["level"])
                frame_start.append(idx)
                frame_stop.append(idx)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_scene_events(repvars, bk2_idx, run, CLIPS_PATH, FS=60):
    """
    Generates an events_df of clips relative to the beginning of the repetition.
    """

    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    fname = repvars["filename"].split("/")[-1]
    sub = fname.split("_")[0]
    ses = fname.split("_")[1]

    # Collect all jsons files corresponding to sub ses run in CLIPS_PATH
    for root, folder, files in sorted(os.walk(CLIPS_PATH)):
        if sub in root and ses in root:
            for file in files:
                file_bk2_idx = file.split("-")[-1][5:7]
                if run in file:
                    if file_bk2_idx == str(bk2_idx).zfill(2):
                        if file.endswith(".json"):
                            # Load json file
                            json_path = op.join(root, file)
                            with open(json_path, "r") as f:
                                clip_metadata = json.load(f)
                            clip_code = str(clip_metadata["ClipCode"])
                            start_frame = clip_metadata["StartFrame"]
                            end_frame = clip_metadata["EndFrame"]
                            scene = clip_metadata["SceneFullName"]

                            onset.append(start_frame / FS)
                            duration.append((end_frame - start_frame) / FS)
                            trial_type.append(f"scene-{scene}_code-{clip_code}")
                            level.append(clip_metadata["LevelFullName"])
                            frame_start.append(start_frame)
                            frame_stop.append(end_frame)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def main(args):
    FS = 60

    # Get datapath
    DATA_PATH = args.datapath
    if DATA_PATH == ".":
        print("No data path specified. Searching files in this folder.")
    print(f"Generating annotations for the mario dataset in : {DATA_PATH}")
    # Import stimuli
    stimuli_path = op.join(DATA_PATH, "stimuli")
    retro.data.Integrations.add_custom_path(stimuli_path)

    CLIPS_PATH = args.clips_path

    REPLAYS_PATH = args.replays_path

    OUTPUT_PATH = args.output_path

    # Walk through all folders looking for .bk2 files
    for root, folder, files in sorted(os.walk(DATA_PATH)):
        if not "sourcedata" in root:
            for file in files:
                if "events.tsv" in file and not "annotated" in file:
                    run_events_file = op.join(root, file)
                    run_id = file.split("_")[3]
                    if OUTPUT_PATH is not None:
                        sub = file.split("_")[0]
                        ses = file.split("_")[1]
                        events_annotated_fname = op.join(
                            OUTPUT_PATH,
                            sub,
                            ses,
                            "func",
                            file.replace("_events.", "_desc-annotated_events."),
                        )
                        os.makedirs(op.dirname(events_annotated_fname), exist_ok=True)
                    else:
                        events_annotated_fname = run_events_file.replace(
                            "_events.", "_desc-annotated_events."
                        )
                    if not op.isfile(events_annotated_fname):
                        print(f"Processing : {file}")
                        events_dataframe = pd.read_table(run_events_file, index_col=0)
                        events_dataframe = events_dataframe[
                            events_dataframe["trial_type"] == "gym-retro_game"
                        ]  # select only repetition events
                        events_dataframe = events_dataframe[
                            ["trial_type", "onset", "level", "stim_file"]
                        ].reset_index()  # select only relevant columns
                        bk2_files = events_dataframe["stim_file"].values.tolist()
                        runvars = []
                        for bk2_idx, bk2_file in enumerate(bk2_files):
                            if bk2_file != "Missing file" and type(bk2_file) != float:
                                print("Adding : " + bk2_file)
                                sub = bk2_file.split("/")[0]
                                ses = bk2_file.split("/")[1]
                                filename = bk2_file.split("/")[-1]
                                variables_sidecar_fname = op.join(
                                    REPLAYS_PATH,
                                    sub,
                                    ses,
                                    "beh",
                                    "variables",
                                    filename.replace(".bk2", ".json"),
                                )
                                if op.exists(variables_sidecar_fname):
                                    with open(variables_sidecar_fname, "rb") as f:
                                        repvars = json.load(f)

                                    # Add info to repetition event
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "level",
                                    ] = repvars[
                                        "level"
                                    ]  # replace level value in the dataframe by the one in the repvars dict
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "frame_start",
                                    ] = int(0)
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "frame_stop",
                                    ] = int(len(repvars["score"]))
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "duration",
                                    ] = (
                                        int(len(repvars["score"])) / FS
                                    )

                                    # rename index column to rep_index
                                    events_dataframe.rename(
                                        columns={"index": "rep_index"}, inplace=True
                                    )

                                    runvars.append(repvars)
                            else:
                                print("Missing file, skipping")
                                runvars.append({})

                        # Add phase (discovery VS practice)
                        if (
                            events_dataframe["level"].values[0]
                            == events_dataframe["level"].values[1]
                        ):
                            phase = "discovery"
                        else:
                            phase = "practice"
                        events_dataframe["phase"] = phase
                        events_df = create_runevents(
                            runvars, run_id, events_dataframe, CLIPS_PATH, FS=FS
                        )

                        events_df.to_csv(events_annotated_fname, sep="\t", index=False)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
