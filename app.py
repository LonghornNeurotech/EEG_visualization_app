from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import base64
import io
from scipy import fft, ifft
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from scipy.signal import butter, filtfilt

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def fft_filter(data, fs, lowcut=None, highcut=None):
    """
    Apply an FFT-based filter (low-pass, high-pass, or band-pass).
    
    Parameters:
    - data: The EEG signal (1D array) to be filtered
    - fs: The sampling frequency of the signal
    - lowcut: The lower cutoff frequency for the filter (None for no low-pass filtering)
    - highcut: The upper cutoff frequency for the filter (None for no high-pass filtering)
    
    Returns:
    - filtered_data: The filtered signal after applying the FFT filter
    """
    # Perform FFT on the signal
    N = len(data)
    fft_data = fft(data)
    
    # Frequency axis
    freqs = np.fft.fftfreq(N, 1/fs)
    
    # Apply low-pass filter (zero out frequencies above highcut)
    if highcut:
        fft_data[np.abs(freqs) > highcut] = 0
    
    # Apply high-pass filter (zero out frequencies below lowcut)
    if lowcut:
        fft_data[np.abs(freqs) < lowcut] = 0
    
    # Perform inverse FFT to get the filtered signal in the time domain
    filtered_data = np.real(ifft(fft_data))
    
    return filtered_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('npy_files')
    file_paths = []

    for file in files:
        if file and file.filename.endswith('.npy'):
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            file_paths.append(path)

    if len(file_paths) == 0:
        return "No .npy files uploaded.", 400

    return redirect(url_for('visualize', file_paths=file_paths))

@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    file_paths = request.args.getlist('file_paths')
    data = [np.load(fp) for fp in file_paths]

    plots = []
    for idx, arr in enumerate(data):
        for channel in range(arr.shape[0]):
            fig, ax = plt.subplots(figsize=(3, 2))
            ax.plot(arr[channel][1:], label=f'File {idx + 1} - Channel {channel + 1}', color=['blue', 'orange'][idx % 2])
            ax.legend()
            ax.set_title(f'File {idx + 1} - Channel {channel + 1}')

            # Convert the plot to a base64 string
            canvas = FigureCanvas(fig)
            output = io.BytesIO()
            canvas.print_png(output)
            img_data = output.getvalue()

            # Base64 encode the image
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            plots.append(f"data:image/png;base64,{img_b64}")
            plt.close(fig)

    return render_template('visualize.html', plots=plots, file_paths=file_paths)

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    file_path = request.form['file']
    channel = int(request.form['channel']) - 1  # Convert number to zero-based index
    filter_type = request.form['filter']
    window_size = int(request.form['window_size'])

    arr = np.load(file_path)

    if filter_type == 'bandpass':
        low_cut = float(request.form['low_cut'])
        high_cut = float(request.form['high_cut'])
        b, a = butter(4, [low_cut, high_cut], btype='band', fs=1000)

        # Ensure all channels have the same length
        arr = arr[:, 1:]  # Remove the first column from ALL channels
        # Apply filter to the entire signal
        filtered_signal = filtfilt(b, a, arr[channel])

        # Assign the filtered signal (minus the first value)
        arr[channel] = filtered_signal
    elif filter_type == 'fft':
        low_cut = float(request.form['low_cut'])
        high_cut = float(request.form['high_cut'])
        fs = 1000  # Assuming a fixed sampling frequency of 1000 Hz, adjust as necessary
        arr[channel] = fft_filter(arr[channel], fs, lowcut=low_cut, highcut=high_cut)


    elif filter_type == 'zscore':  # Written by Sarah
        channel_data = arr[channel]
        mean = np.mean(channel_data)
        std = np.std(channel_data)
        if std == 0:
            std = 1  
        channel_data = (channel_data - mean) / std
        arr[channel] = channel_data

    elif filter_type == 'minmax':  # Written by Sarah
        channel_data = arr[channel]
        max_val = np.max(channel_data)
        min_val = np.min(channel_data) 
        channel_data = (channel_data - min_val) / (max_val - min_val)
        arr[channel] = channel_data

    elif filter_type == 'average':  # Written by Marco
        kernel = np.ones(window_size) / window_size
        pad_width = window_size // 2  

        # Apply padding
        padded_data = np.pad(arr[channel][1:], (pad_width, pad_width), mode='reflect')

        # Convolve
        filtered_data = np.convolve(padded_data, kernel, mode='valid')

        arr[channel] = filtered_data[:arr.shape[1]]  # Ensure shape consistency

    np.save(file_path, arr)
    return redirect(url_for('visualize', file_paths=[file_path]))


if __name__ == '__main__':
    app.run(debug=True)
