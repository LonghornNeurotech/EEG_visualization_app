from flask import Flask, request, jsonify, render_template, redirect, url_for
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from werkzeug.utils import secure_filename
import scipy

# Use Agg backend to avoid GUI issues on macOS
plt.switch_backend('Agg')

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.npy'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Redirect to visualize page after successful upload
        return redirect(url_for('visualize', filepath=filename))
    else:
        return jsonify({'error': 'Invalid file format. Only .npy files allowed.'}), 400

@app.route('/visualize')
def visualize():
    filename = request.args.get('filepath')
    
    if not filename:
        return jsonify({'error': 'Filepath not provided'}), 400
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        eeg_data = np.load(filepath)

        # Truncate the first value in each channel's data
        eeg_data = eeg_data[:, 1:]

        # Save original data for resetting
        np.save(os.path.join(app.config['UPLOAD_FOLDER'], f'original_{filename}'), eeg_data)

        # Generate individual plots for each channel
        plot_paths = []
        for i in range(eeg_data.shape[0]):
            fig, ax = plt.subplots(figsize=(6, 2))  # Smaller size for the plot
            ax.plot(eeg_data[i], label=f'Channel {i+1}')
            ax.set_title(f"EEG Data - Channel {i+1}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Amplitude")
            ax.legend(loc="upper right")

            plot_filename = f'channel_{i+1}_plot.png'
            plot_filepath = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            fig.savefig(plot_filepath)
            plt.close(fig)
            plot_paths.append(url_for('static', filename=f'uploads/{plot_filename}'))

        return render_template('visualize.html', plot_paths=plot_paths)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def bandpass_filter(sig, order, lowcut, highcut, sampling_freq):
    b, a = scipy.signal.butter(order, [lowcut, highcut], btype='band', fs=sampling_freq)
    processed_signal = scipy.signal.filtfilt(b, a, sig)
    return processed_signal

def notch_filter(data, notch_freq, fs, quality_factor=30):
    nyquist = 0.5 * fs 
    low = notch_freq / nyquist # Normalizes the notch frequency by dividing the Nyquist frequency
    b, a = scipy.signal.iirnotch(low, quality_factor) # Designing the notch filter using iirnotch. Creates a filter to remove a specific frequency
    filtered_signal = scipy.signal.filtfilt(b, a, data) # Applies the filter forward and backward to avoid phase shift (zero-phase filtering)
    return filtered_signal

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    data = request.json
    print(f"Received data: {data}")
    filename = data.get('filepath')
    channel_index = data.get('channel')
    filter_type = data.get('filter_type')
    lowcut = data.get('lowcut')
    highcut = data.get('highcut')

    if not filename:
        return jsonify({'error': 'Filename not provided'}), 400

    try:
        # Construct the full file path for the original data
        full_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Full file path: {full_filepath}")

        # Load the original EEG data from the file
        eeg_data = np.load(full_filepath)

        if channel_index < 0 or channel_index >= eeg_data.shape[0]:
            return jsonify({'error': 'Invalid channel index'}), 400

        eeg_channel_data = eeg_data[channel_index][1:]

        # Apply the selected filter type
        if filter_type == 'bandpass':
            filtered_data = bandpass_filter(eeg_channel_data, order=4, lowcut=lowcut, highcut=highcut, sampling_freq=1000)
        else:
            return jsonify({'error': 'Invalid filter type'}), 400

        # Generate the new plot for the filtered data
        fig, ax = plt.subplots(figsize=(6, 2))  # Smaller size for the plot
        ax.plot(filtered_data, label=f'Filtered Channel {channel_index + 1}')
        ax.set_title(f"EEG Data - Channel {channel_index + 1} ({filter_type.capitalize()})")
        ax.set_xlabel("Time")
        ax.set_ylabel("Amplitude")
        ax.legend(loc="upper right")

        plot_filename = f'channel_{channel_index + 1}_{filter_type}_plot.png'
        plot_filepath = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
        fig.savefig(plot_filepath)
        plt.close(fig)

        return jsonify({'new_plot_url': url_for('static', filename=f'uploads/{plot_filename}')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/apply_animation', methods=['POST'])
def apply_animation():
    data = request.json
    print(f"Received data: {data}")
    filename = data.get('filepath')
    channel_index = data.get('channel')

    if not filename:
        return jsonify({'error': 'Filename not provided'}), 400

    try:
        # Construct the full file path for the original data
        full_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Full file path: {full_filepath}")

        # Load the original EEG data from the file
        eeg_data = np.load(full_filepath)

        if channel_index < 0 or channel_index >= eeg_data.shape[0]:
            return jsonify({'error': 'Invalid channel index'}), 400

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

        return jsonify({'new_plot_url': url_for('static', filename=f'uploads/{plot_filename}')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


if __name__ == "__main__":
    app.run(debug=True)