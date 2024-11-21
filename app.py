from flask import Flask, request, jsonify, render_template, redirect, url_for
import numpy as np
import os
import matplotlib.pyplot as plt
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
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Both files are required'}), 400

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return jsonify({'error': 'One or both files not selected'}), 400

    if file1 and file1.filename.endswith('.npy') and file2 and file2.filename.endswith('.npy'):
        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
        file1.save(filepath1)
        file2.save(filepath2)
        print("FILEPATH1:", filepath1)
        print("FILEPATH2:", filepath2)

        # Redirect to visualize page after successful upload
        return redirect(url_for('visualize', filepath1=filename1, filepath2=filename2))
    else:
        return jsonify({'error': 'Invalid file format. Only .npy files allowed.'}), 400

@app.route('/visualize')
def visualize():
    print("REQUEST:\n", request)
    filename1 = request.args.get('filepath1')
    filename2 = request.args.get('filepath2')

    if not filename1 or not filename2:
        return jsonify({'error': 'Filepaths not provided'}), 400

    try:
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
        eeg_data1 = np.load(filepath1)
        eeg_data2 = np.load(filepath2)

        # Truncate the first value in each channel's data
        eeg_data1 = eeg_data1[:, 1:]
        eeg_data2 = eeg_data2[:, 1:]

        # Save original data for resetting
        np.save(os.path.join(app.config['UPLOAD_FOLDER'], f'original_{filename1}'), eeg_data1)
        np.save(os.path.join(app.config['UPLOAD_FOLDER'], f'original_{filename2}'), eeg_data2)

        # Generate plots for each channel per file
        plot_paths1 = []  # For file 1

        plot_paths2 = []  # For file 2
        num_channels1 = eeg_data1.shape[0]
        num_channels2 = eeg_data2.shape[0]
        colors = ['blue', 'orange']  # Different colors for the two files

        # Plot channels for the first file
        for i in range(num_channels1):
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(eeg_data1[i], label=f'File 1 - Channel {i + 1}', color=colors[0])
            ax.set_title(f"EEG Data - File 1 - Channel {i + 1}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Amplitude")
            ax.legend(loc="upper right")

            plot_filename = f'file1_channel_{i + 1}_plot.png'
            plot_filepath = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            fig.savefig(plot_filepath)
            plt.close(fig)
            plot_paths1.append(url_for('static', filename=f'uploads/{plot_filename}'))

        # Plot channels for the second file
        for i in range(num_channels2):
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(eeg_data2[i], label=f'File 2 - Channel {i + 1}', color=colors[1])
            ax.set_title(f"EEG Data - File 2 - Channel {i + 1}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Amplitude")
            ax.legend(loc="upper right")

            plot_filename = f'file2_channel_{i + 1}_plot.png'
            plot_filepath = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            fig.savefig(plot_filepath)
            plt.close(fig)
            plot_paths2.append(url_for('static', filename=f'uploads/{plot_filename}'))

        return render_template('visualize.html', plot_paths1=plot_paths1, plot_paths2=plot_paths2)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def bandpass_filter(sig, order, lowcut, highcut, sampling_freq):
    b, a = scipy.signal.butter(order, [lowcut, highcut], btype='band', fs=sampling_freq)
    processed_signal = scipy.signal.filtfilt(b, a, sig)
    return processed_signal

def notch_filter(data, notch_freq, fs, quality_factor=30):
    nyquist = 0.5 * fs
    low = notch_freq / nyquist
    b, a = scipy.signal.iirnotch(low, quality_factor)
    filtered_signal = scipy.signal.filtfilt(b, a, data)
    return filtered_signal

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    data = request.json
    filename1 = data.get('filepath1')
    filename2 = data.get('filepath2')
    filter_type = data.get('filter_type')
    lowcut = data.get('lowcut')
    highcut = data.get('highcut')
    channel = int(data.get('channel'))
    sampling_freq = 125  # Example sampling frequency

    if not filename1 or not filename2:
        return jsonify({'error': 'File paths not provided'}), 400

    try:
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)

        eeg_data1 = np.load(filepath1)
        eeg_data2 = np.load(filepath2)

        # Original signals
        original_signal1 = eeg_data1[channel, 1:]
        original_signal2 = eeg_data2[channel, 1:]

        # Apply the selected filter
        if filter_type == 'bandpass':
            filtered_signal1 = bandpass_filter(original_signal1, 4, lowcut, highcut, sampling_freq)
            filtered_signal2 = bandpass_filter(original_signal2, 4, lowcut, highcut, sampling_freq)
        elif filter_type == 'fft':
            filtered_signal1 = np.fft.ifft(np.fft.fft(original_signal1)).real
            filtered_signal2 = np.fft.ifft(np.fft.fft(original_signal2)).real
        elif filter_type == 'average':
            filtered_signal1 = np.convolve(original_signal1, np.ones(10) / 10, mode='same')
            filtered_signal2 = np.convolve(original_signal2, np.ones(10) / 10, mode='same')
        else:
            return jsonify({'error': 'Invalid filter type'}), 400

        # Save original and filtered plots for file 1
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        # ax1.plot(original_signal1, label='Original', color='blue', alpha=0.6)
        ax1.plot(filtered_signal1, label='Filtered', color='red')
        ax1.set_title(f"File 1 - Channel {channel + 1}")
        ax1.legend(loc="upper right")
        new_plot_filename1 = f'filtered_file1_channel_{channel + 1}.png'
        fig1.savefig(os.path.join(app.config['UPLOAD_FOLDER'], new_plot_filename1))
        plt.close(fig1)

        # Save original and filtered plots for file 2
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        # ax2.plot(original_signal2, label='Original', color='orange', alpha=0.6)
        ax2.plot(filtered_signal2, label='Filtered', color='green')
        ax2.set_title(f"File 2 - Channel {channel + 1}")
        ax2.legend(loc="upper right")
        new_plot_filename2 = f'filtered_file2_channel_{channel + 1}.png'
        fig2.savefig(os.path.join(app.config['UPLOAD_FOLDER'], new_plot_filename2))
        plt.close(fig2)

        # Return the new plot URLs
        return jsonify({
            'new_plot_url1': url_for('static', filename=f'uploads/{new_plot_filename1}'),
            'new_plot_url2': url_for('static', filename=f'uploads/{new_plot_filename2}')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
