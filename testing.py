import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def main():
    filename = "EEGMouse_alan_1_1_69.npy"
    channel_index = 1

    if not filename:
        return

    try:
        # Construct the full file path for the original data
        full_filepath = os.path.join("./static/uploads/", filename)
        print(f"Full file path: {full_filepath}")

        # Load the original EEG data from the file
        eeg_data = np.load(full_filepath)

        if channel_index < 0 or channel_index >= eeg_data.shape[0]:
            return

        eeg_channel_data = eeg_data[channel_index][1:]

        # Skip filtering. TODO: Restructure later
        filtered_data = eeg_channel_data[::]
        frame_len = len(filtered_data)

        # Generate the new plot for the filtered data
        fig, ax = plt.subplots(figsize=(6, 2))  # Smaller size for the plot
        line, = ax.plot([],[], label=f'Filtered Channel {channel_index + 1}')
        ax.set_title(f"EEG Data - Channel {channel_index + 1}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Amplitude")
        ax.legend(loc="upper right")
        ax.set_xlim(0, frame_len)
        ax.set_ylim(np.min(filtered_data), np.max(filtered_data))

        plot_filename = f'channel_{channel_index + 1}_animation_plot.gif'
        plot_filepath = os.path.join("./static/uploads/", plot_filename)
        

        def animate(i):
            x = np.arange(0, i + 1)
            y = filtered_data[:i + 1]
            line.set_data(x,y)
            return line

            

        ani = animation.FuncAnimation(fig, animate, frames=range(0, frame_len))
        ani.save(plot_filepath, writer=animation.PillowWriter(150))
        plt.close(fig)

        return
    

    except Exception as e:
        print(e)
        return
    
if __name__ == "__main__":
    main()