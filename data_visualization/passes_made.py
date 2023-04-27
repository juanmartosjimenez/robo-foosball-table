from mplsoccer import Pitch
import matplotlib.pyplot as plt
import matplotlib
import glob
import pandas as pd
import numpy as np
LINEWIDTH = 1  # starting linewidth
DIFF_LINEWIDTH = 1.2  # amount the glow linewidth increases each loop
NUM_GLOW_LINES = 10  # the amount of loops, if you increase the glow will be wider

# in each loop, for the glow, we plot the alpha divided by the num_glow_lines
# I have a lower alpha_pass_line value as there is a slight overlap in
# the pass comet lines when using capstyle='round'
ALPHA_PITCH_LINE = 0.3
ALPHA_PASS_LINE = 0.15
BACKGROUND_COLOR = '#212946'
PASS_COLOR = '#FE53BB'
LINE_COLOR = '#08F7FE'
# 743, 397
pitch = Pitch(pitch_type='custom', pitch_color='black', line_color="white", line_zorder=2, pitch_length=743, pitch_width=397)
fig, ax = pitch.draw(figsize=(16, 8))

fig.set_facecolor((146/255, 214/255, 200/255))

customcmap = matplotlib.colors.LinearSegmentedColormap.from_list("custom cmap", [(49/255, 21/255, 31/255),"red", "yellow"])
# Read csv data into dataframe
header = ["x", "y", "rate"]
data = pd.read_csv(r"C:\Users\juanm\OneDrive\Documents\robo-foosball-table\camera\data\game_0_0.csv", names=header, index_col=False)
data.drop(columns="rate", inplace=True)
data.drop(data.tail(1).index,inplace=True)
new = data.diff(axis=0)
new.dropna(inplace=True, axis=0)
#pitch.lines(data["x"], data["y"], data["x"] + new["x"], data["y"] + new["y"], ax=ax, color="white", lw=1, zorder=2)
#plt.title("Passes made", color="black", fontsize=20)
#plt.show()

slope = new["y"] / new["x"]
# Replace inf with 0
slope = slope.replace([np.inf, -np.inf], 0)
# convert to np array
slope = slope.tolist()

THRESHOLD = 0.5
lines = []
start_slope = None
start_slope_index = None
for ii, elem in enumerate(slope):
    if start_slope is None:
        start_slope = elem
        start_slope_index = ii

    if abs(slope[ii+1] - start_slope) > THRESHOLD:
        lines.append((start_slope_index, ii+1))
        start_slope = None
    if ii == len(slope) - 2:
        lines.append((start_slope_index, ii+1))
        break


for line in lines:
    pitch.lines(data["x"][line[0]], data["y"][line[0]], data["x"][line[1]], data["y"][line[1]], ax=ax, color="white", lw=1, zorder=2)

plt.title("Passes made", color="black", fontsize=20)
plt.show()


