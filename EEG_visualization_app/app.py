from flask import Flask, request, jsonify, render_template, redirect, url_for
import numpy as np
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename

# Use Agg backend to avoid GUI issues on macOS
plt.switch_backend('Agg')

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Dummy function placeholders for preprocessing techniques
def bandpass_filter(data, low_freq, high_freq):
    return data  

def fft_transform(data):
    return data 

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
        eeg_data = eeg_data[:, 1:]  # Slicing to remove the first element

        # Generate individual plots for each channel
        plot_paths = []
        for i in range(eeg_data.shape[0]):
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(eeg_data[i], label=f'Channel {i+1}')
            ax.set_title(f"EEG Data - Channel {i+1}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Amplitude")
            ax.legend(loc="upper right")
            
            # Save plot to static uploads folder
            plot_filename = f'channel_{i+1}_plot.png'
            plot_filepath = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
            fig.savefig(plot_filepath)
            plt.close(fig)  # Close the figure to avoid memory issues
            plot_paths.append(url_for('static', filename=f'uploads/{plot_filename}'))
        
        # Render plot on visualize.html template with dropdown options
        return render_template('visualize.html', plot_paths=plot_paths)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
