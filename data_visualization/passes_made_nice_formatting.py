from mplsoccer import Pitch, FontManager
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.patheffects as path_effects
import glob
import os

# Read csv data into dataframe
header = ["x", "y", "rate"]
path = r'C:\Users\juanm\OneDrive\Documents\robo-foosball-table\camera\data'
all_files = glob.glob(os.path.join(path, "*.csv"))
title_buff = [os.path.basename(filepath).replace(".csv", "").replace("game_", "").replace("_", " - ") for filepath in all_files][1:]
title_buff.append("9 - 10")

all_dfs = []
for ii, filepath in enumerate(all_files):
    data = pd.read_csv(filepath, names=header, index_col=False)
    data.drop(columns="rate", inplace=True)
    all_dfs.append(data)

data = pd.concat(all_dfs, ignore_index=True)
new = data.diff(axis=0)
new.dropna(inplace=True, axis=0)
# pitch.lines(data["x"], data["y"], data["x"] + new["x"], data["y"] + new["y"], ax=ax, color="white", lw=1, zorder=2)
# plt.title("Passes made", color="black", fontsize=20)
# plt.show()

slope = new["x"] / new["y"]
slope2 = new["y"] / new["x"]
# Replace inf with 0
slope = slope.replace([np.inf, -np.inf], 0)
slope2 = slope2.replace([np.inf, -np.inf], 0)
# convert to np array
slope = slope.tolist()
slope2 = slope2.tolist()

THRESHOLD = 1
lines = []
start_slope = None
start_slope2 = None
start_slope_index = None
for ii, elem in enumerate(slope):
    if start_slope is None:
        start_slope = elem
        start_slope2 = slope2[ii]
        start_slope_index = ii

    if start_slope < 0 < slope[ii + 1] or start_slope > 0 > slope[ii + 1]:
        lines.append((start_slope_index, ii + 1))
        start_slope = None
        start_slope2 = None
    elif abs(slope[ii + 1] - start_slope) > THRESHOLD and abs(slope2[ii + 1] - start_slope2) > THRESHOLD:
        lines.append((start_slope_index, ii + 1))
        start_slope = None
        start_slope2 = None
    if ii == len(slope) - 2:
        lines.append((start_slope_index, ii + 1))
        break

# THIS CODE WAS TAKEN FROM THE MPLSOCCER DOCUMENTATION PAGE FOR FORMATTING https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_plots/plot_cyberpunk.html
LINEWIDTH = 1  # starting linewidth
DIFF_LINEWIDTH = 1.2  # amount the glow linewidth increases each loop
NUM_GLOW_LINES = 10  # the amount of loops, if you increase the glow will be wider

# in each loop, for the glow, we plot the alpha divided by the num_glow_lines
# I have a lower alpha_pass_line value as there is a slight overlap in
# the pass comet lines when using capstyle='round'
ALPHA_PITCH_LINE = 0.3
ALPHA_PASS_LINE = 0.15

# The colors are borrowed from mplcyberpunk. Try some of the following alternatives
# '#08F7FE' (teal/cyan), '#FE53BB' (pink), '#F5D300' (yellow),
# '#00ff41' (matrix green), 'r' (red), '#9467bd' (viloet)
BACKGROUND_COLOR = '#212946'
PASS_COLOR = '#FE53BB'
LINE_COLOR = '#08F7FE'

# plot as initial pitch and the lines with alpha=1
# I have used grid to get a title and endnote axis automatically, but you could you pitch.draw()
pitch = Pitch(pitch_type="custom", line_color=LINE_COLOR, pitch_color=BACKGROUND_COLOR, linewidth=LINEWIDTH,
              line_alpha=1, goal_alpha=1, goal_type='box', pitch_length=743, pitch_width=397)
fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                     endnote_height=0.04, title_space=0, endnote_space=0)
fig.set_facecolor(BACKGROUND_COLOR)
for line in lines:
    pitch.lines(data["x"][line[0]], data["y"][line[0]], data["x"][line[1]], data["y"][line[1]],
                capstyle='butt',  # cut-off the line at the end-location.
                linewidth=LINEWIDTH, color=PASS_COLOR, comet=True, ax=ax['pitch'])

# plotting the titles and endnote
text_effects = [path_effects.Stroke(linewidth=3, foreground='black'),
                path_effects.Normal()]
ax['title'].text(0.5, 0.3, f'Passes Made',
                 path_effects=text_effects,
                 va='center', ha='center', color=LINE_COLOR, fontsize=30)

# plotting the glow effect. it is essentially a loop that plots the line with
# a low alpha (transparency) value and gradually increases the linewidth.
# This way the center will have more color than the outer area.
# you could break this up into two loops if you wanted the pitch lines to have wider glow
for i in range(1, NUM_GLOW_LINES + 1):
    pitch = Pitch(pitch_type="custom", line_color=LINE_COLOR, pitch_color=BACKGROUND_COLOR,
                  linewidth=LINEWIDTH + (DIFF_LINEWIDTH * i),
                  line_alpha=ALPHA_PITCH_LINE / NUM_GLOW_LINES,
                  goal_alpha=ALPHA_PITCH_LINE / NUM_GLOW_LINES,
                  goal_type='box', pitch_length=743, pitch_width=397)
    pitch.draw(ax=ax['pitch'])  # we plot on-top of our previous axis from pitch.grid
    for line in lines:
        pitch.lines(data["x"][line[0]], data["y"][line[0]], data["x"][line[1]], data["y"][line[1]],
                    linewidth=LINEWIDTH + (DIFF_LINEWIDTH * i),
                    capstyle='round',  # capstyle round so the glow extends past the line
                    alpha=ALPHA_PASS_LINE / NUM_GLOW_LINES,
                    color=PASS_COLOR, comet=True, ax=ax['pitch'])

plt.show()
