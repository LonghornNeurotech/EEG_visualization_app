document.addEventListener('DOMContentLoaded', function () {
    // Get the form element and prevent the default form submission
    const filterForm = document.getElementById('filterForm');
    const filterTypeInput = document.getElementById('filterType');
    const lowcutInput = document.getElementById('lowcut');
    const highcutInput = document.getElementById('highcut');
    const channelInput = document.getElementById('channel');
    const filepath1 = new URLSearchParams(window.location.search).get('filepath1'); // Get the first filepath from query params
    const filepath2 = new URLSearchParams(window.location.search).get('filepath2'); // Get the second filepath from query params

    // Check if filepaths are available
    if (!filepath1 || !filepath2) {
        alert('Error: File paths are not provided.');
        return;
    }

    filterForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent page reload

        const data = {
            filepath1: filepath1,  // Send the first filename
            filepath2: filepath2,  // Send the second filename
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
            if (responseData.new_plot_url1 && responseData.new_plot_url2) {
                // If the response contains new plot URLs, update the page with the new plots
                const newPlotDiv1 = document.getElementById('newPlot1');
                const newPlotImage1 = document.createElement('img');
                newPlotImage1.src = responseData.new_plot_url1;
                newPlotImage1.style.maxWidth = '500px';  // Set the same max width as other plots
                newPlotImage1.style.maxHeight = '300px';  // Set the same max height as other plots

                // Remove previous plot if present
                newPlotDiv1.innerHTML = '';  
                newPlotDiv1.appendChild(newPlotImage1);

                const newPlotDiv2 = document.getElementById('newPlot2');
                const newPlotImage2 = document.createElement('img');
                newPlotImage2.src = responseData.new_plot_url2;
                newPlotImage2.style.maxWidth = '500px';
                newPlotImage2.style.maxHeight = '300px';

                // Remove previous plot if present
                newPlotDiv2.innerHTML = '';  
                newPlotDiv2.appendChild(newPlotImage2);

                // Update the original plots with the new filtered plots
                const plotsDiv1 = document.getElementById('plots1');
                const originalPlot1 = plotsDiv1.querySelectorAll('img')[data.channel];
                if (originalPlot1) {
                    originalPlot1.src = responseData.new_plot_url1;
                }

                const plotsDiv2 = document.getElementById('plots2');
                const originalPlot2 = plotsDiv2.querySelectorAll('img')[data.channel];
                if (originalPlot2) {
                    originalPlot2.src = responseData.new_plot_url2;
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
});
