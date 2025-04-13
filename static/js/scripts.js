document.addEventListener('DOMContentLoaded', function () {
    // Get the form element and prevent the default form submission
    const filterForm = document.getElementById('filterForm');
    const filterTypeInput = document.getElementById('filterType');
    const lowcutInput = document.getElementById('lowcut');
    const highcutInput = document.getElementById('highcut');
    const channelInput = document.getElementById('channel');
    const animationChannelInput = document.getElementById('animationChannel');
    const filepath = new URLSearchParams(window.location.search).get('filepath');  // Get filename from query params

    const animationForm = document.getElementById('animationForm');

    // Check if filepath is available
    if (!filepath) {
        alert('Error: No filepath provided.');
        return;
    }

    filterForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent page reload

        const data = {
            filepath: filepath,  // Send the filename
            filter_type: filterTypeInput.value,
            lowcut: parseFloat(lowcutInput.value),
            highcut: parseFloat(highcutInput.value),
            channel: parseInt(channelInput.value)
        };

        console.log("Sending data:", data);  // Log data for debugging

        // Send the request to the Flask backend
        fetch('/apply_filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(responseData => {
            if (responseData.new_plot_url) {
                // If the response contains a new plot URL, update the page with the new plot
                const newPlotDiv = document.getElementById('newPlot');
                const newPlotImage = document.createElement('img');
                newPlotImage.src = responseData.new_plot_url;
                newPlotImage.style.maxWidth = '500px';  // Set the same max width as other plots
                newPlotImage.style.maxHeight = '300px';  // Set the same max height as other plots

                // Remove previous plot if present
                newPlotDiv.innerHTML = '';  
                newPlotDiv.appendChild(newPlotImage);

                // Update the original plot with the new filtered plot
                const plotsDiv = document.getElementById('plots');
                const originalPlot = plotsDiv.querySelectorAll('img')[data.channel];
                if (originalPlot) {
                    originalPlot.src = responseData.new_plot_url;  // Update the original plot with the new one
                }
            } else if (responseData.error) {
                alert(`Error: ${responseData.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while applying the filter.');
        });
    });

    animationForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent page reload

        const data = {
            filepath: filepath,  // Send the filename
            channel: parseInt(animationChannelInput.value)
        };

        console.log("Sending data:", data);  // Log data for debugging

        // Send the request to the Flask backend
        fetch('/apply_animation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(responseData => {
            if (responseData.new_plot_url) {
                // If the response contains a new plot URL, update the page with the new plot
                const newPlotDiv = document.getElementById('newPlot');
                const newPlotImage = document.createElement('img');
                newPlotImage.src = responseData.new_plot_url;
                newPlotImage.style.maxWidth = '500px';  // Set the same max width as other plots
                newPlotImage.style.maxHeight = '300px';  // Set the same max height as other plots

                // Remove previous plot if present
                newPlotDiv.innerHTML = '';  
                newPlotDiv.appendChild(newPlotImage);

                // Update the original plot with the new filtered plot
                const plotsDiv = document.getElementById('plots');
                const originalPlot = plotsDiv.querySelectorAll('img')[data.channel];
                if (originalPlot) {
                    originalPlot.src = responseData.new_plot_url;  // Update the original plot with the new one
                }
            } else if (responseData.error) {
                alert(`Error: ${responseData.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while applying the animation.');
        });
    });
});