document.getElementById('filter').addEventListener('change', function () {
    const filterParameters = document.getElementById('filter-parameters');
    filterParameters.innerHTML = '';
    
    switch (this.value) {
        case 'bandpass':
            filterParameters.innerHTML = `
                <label for="low_cut">Low Cut Frequency:</label>
                <input type="range" id="low_cut" name="low_cut" min="0" max="100">

                <label for="high_cut">High Cut Frequency:</label>
                <input type="range" id="high_cut" name="high_cut" min="0" max="100">
            `;
            break;
        case 'normalization':
            filterParameters.innerHTML = `<label for="norm_param">Normalization Parameter:</label>
                <input type="range" id="norm_param" name="norm_param" min="0" max="1" step="0.01">`;
            break;
        case 'averaging':
            filterParameters.innerHTML = `<label for="average_param">Averaging Parameter:</label>
                <input type="range" id="average_param" name="average_param" min="1" max="10">`;
            break;
    }
});

function applyFilter() {
    const filter = document.getElementById('filter').value;
    const file = document.getElementById('file').value;
    const channel = document.getElementById('channel').value;
    
    let data = {
        filter,
        file,
        channel
    };

    if (filter === 'bandpass') {
        data.low_cut = document.getElementById('low_cut').value;
        data.high_cut = document.getElementById('high_cut').value;
    }

    fetch('/apply_filter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
}

// Update slider values dynamically
document.addEventListener('DOMContentLoaded', function () {
    const lowCutSlider = document.getElementById('low_cut');
    const lowCutValue = document.getElementById('low_cut_value');

    const highCutSlider = document.getElementById('high_cut');
    const highCutValue = document.getElementById('high_cut_value');

    // Set initial values
    lowCutValue.textContent = lowCutSlider.value;
    highCutValue.textContent = highCutSlider.value;

    lowCutSlider.addEventListener('input', function () {
        console.log(`Low cut slider changed to: ${lowCutSlider.value}`);
        lowCutValue.textContent = lowCutSlider.value;
    });
    
    highCutSlider.addEventListener('input', function () {
        console.log(`High cut slider changed to: ${highCutSlider.value}`);
        highCutValue.textContent = highCutSlider.value;
    });
    
});
