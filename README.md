# FORMautomator
## Google Form Automation Script

### Overview

This script automates the process of filling out a Google Form with multiple sections. It is designed to handle forms that include:

- Participant Information & Consent
- Body Shape Questionnaire (BSQ-8A)
- Weight Control Behaviours Checklist

The script supports automatic scrolling to manage longer forms and can perform multiple submissions concurrently.

### Features

- **Automated Form Filling**: Automatically fills out Google Forms based on predefined sections.
- **Randomized Data Generation**: Generates random user data for each submission to simulate real responses.
- **Concurrent Submissions**: Utilizes multithreading to perform multiple submissions simultaneously, improving efficiency.
- **Headless Browser Mode**: Option to run the browser in headless mode for better performance.
- **Error Handling**: Logs errors and attempts to recover from common issues during form submission.
- **Progress Tracking**: Displays a progress bar to track submission status and completion.

### Requirements

- Python 3.x
- Selenium WebDriver
- Google Chrome and ChromeDriver
- tqdm (for progress tracking)

### Installation

1. **Install Python**: Ensure Python 3.x is installed on your system.
2. **Install Selenium**: Use pip to install Selenium:
   ```
   pip install selenium
   ```
3. **Install tqdm**: Use pip to install tqdm for progress tracking:
   ```
   pip install tqdm
   ```
4. **Download ChromeDriver**: Ensure ChromeDriver is installed and matches your Chrome version. Add it to your system's PATH.

### Usage

1. **Command Line Arguments**:
   - `--url`: URL of the Google Form to be filled.
   - `--count`: Number of form submissions to generate (default: 125).
   - `--workers`: Number of concurrent browser instances (default: 4).

2. **Run the Script**:
   Execute the script with the desired parameters:
   ```
   python formfiller.py --url <form_url> --count 125 --workers 4
   ```

3. **Monitor Progress**:
   The script will display a progress bar indicating the number of submissions completed and remaining.

### Customization

- **Random Data Generation**: Modify the `generate_random_user_data`, `generate_random_bsq_answers`, and `generate_random_wcb_answers` functions to customize the data being submitted.
- **Logging**: Adjust logging settings in the script to change the level of detail or log file location.

### Troubleshooting

- **WebDriver Errors**: Ensure ChromeDriver is correctly installed and matches your Chrome version.
- **Form Navigation Issues**: Verify the form structure and update XPath or CSS selectors if the form layout changes.
- **Rate Limiting**: If Google starts rate-limiting, consider adding random delays between submissions or using proxy rotation.

### License

This script is provided "as-is" without warranty of any kind. Use at your own risk.
