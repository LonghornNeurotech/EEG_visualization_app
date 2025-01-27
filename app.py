from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import base64
import io
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from scipy.signal import butter, filtfilt

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    channel = int(request.form['channel']) - 1 # To convert number to index for ease of use
    filter_type = request.form['filter']
    window_size = int(request.form['window_size'])

    arr = np.load(file_path)

    if filter_type == 'bandpass':
        low_cut = float(request.form['low_cut'])
        high_cut = float(request.form['high_cut'])
        b, a = butter(4, [low_cut, high_cut], btype='band', fs=1000)
        arr[channel] = filtfilt(b, a, arr[channel])

    elif filter_type == 'zscore': # Written by Sarah
        channel_data = arr[channel]
        mean = np.mean(channel_data)
        std = np.std(channel_data)
        if std == 0:
            std = 1  
        channel_data = (channel_data - mean) / std
        arr[channel] = channel_data
    
    elif filter_type == 'minmax': # Written by Sarah
        channel_data = arr[channel]
        max = np.max(channel_data)
        min = np.min(channel_data) 
        channel_data = (channel_data - min) / (max - min)
        arr[channel] = channel_data

    elif filter_type == 'average': # Written by Marco
        # Convolution kernel (moving average filter)
        kernel = np.ones(window_size) / window_size
        pad_width = window_size // 2 # Define padding size

        # Apply padding
        padded_data = np.pad(arr[channel][1:], (pad_width, pad_width), mode='reflect')

        # Convolve
        filtered_data = np.convolve(padded_data, kernel, mode='valid')

        arr[channel] = filtered_data

    np.save(file_path, arr)

    return redirect(url_for('visualize', file_paths=[file_path]))

if __name__ == '__main__':
    app.run(debug=True)
