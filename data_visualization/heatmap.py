from mplsoccer import Pitch
import matplotlib.pyplot as plt
import matplotlib
import glob
import pandas as pd
import os
# 743, 397
pitch = Pitch(pitch_type='custom', pitch_color='black', line_color="white", line_zorder=2, pitch_length=743, pitch_width=397)
fig, axes = pitch.draw(figsize=(16, 8), nrows=4, ncols=5)

fig.set_facecolor((146/255, 214/255, 200/255))

customcmap = matplotlib.colors.LinearSegmentedColormap.from_list("custom cmap", [(49/255, 21/255, 31/255),"red", "yellow"])
# Read csv data into dataframe
header = ["x", "y", "rate"]
path = r'C:\Users\juanm\OneDrive\Documents\robo-foosball-table\camera\data'
all_files = glob.glob(os.path.join(path, "*.csv"))
title_buff = [os.path.basename(filepath).replace(".csv", "").replace("game_", "").replace("_", " - ") for filepath in all_files][1:]
title_buff.append("9 - 10")

col_count = 0
row_count = 0
test_run = 0
for ii, filepath in enumerate(all_files):
    test_run += 1
    if test_run == 3:
        pass
    data = pd.read_csv(filepath, names=header, index_col=False)
    data.drop(columns="rate", inplace=True)
    axes[row_count][col_count].set_title(title_buff[ii], color="black")
    pitch.kdeplot(data["x"], data["y"], ax=axes[row_count][col_count], cmap=customcmap, shade=True, n_levels=100, zorder=1)
    col_count += 1
    if col_count == 5:
        row_count += 1
        col_count = 0

# Add a colorbar and position to the right of the plot
#fig.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(vmin=0, vmax=1), cmap=customcmap), ax=axes, pad=0, location="top", anchor=(0,0), shrink=0.5, panchor=(0,0))


# Set title
fig.suptitle("Heatmap of ball positions", color="black", fontsize=20)
plt.show()

