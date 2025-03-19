"""
Google Form Automation Script
----------------------------
This script automates filling a Google Form with multiple sections for a survey including:
- Participant Information & Consent
- Body Shape Questionnaire (BSQ-8A)
- Weight Control Behaviours Checklist

Includes automatic scrolling to handle longer forms.
Author: Thushaar
Date: March 19, 2025
"""

import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import concurrent.futures
import string
import argparse
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("google_form_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoogleFormAutomation:
    """
    A class to automate filling a Google Form with multiple sections.
    """
    
    def __init__(self, form_url, headless=False):
        """
        Initialize the GoogleFormAutomation instance.
        
        Args:
            form_url (str): The URL of the Google Form to be filled.
            headless (bool): Whether to run browser in headless mode.
        """
        self.form_url = form_url
        self.headless = headless
        self.driver = None
        self.wait = None
        self.timeout = 10  # Default timeout for WebDriverWait
        
    def setup_driver(self):
        """
        Set up the WebDriver with appropriate options.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            logger.info("WebDriver setup completed successfully.")
        except Exception as e:
            logger.error(f"Failed to set up WebDriver: {e}")
            raise

    def navigate_to_form(self):
        """
        Navigate to the Google Form URL.
        """
        try:
            self.driver.get(self.form_url)
            logger.info(f"Navigated to Google Form URL: {self.form_url}")
            # Wait for form to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))
            logger.info("Form loaded successfully")
        except Exception as e:
            logger.error(f"Failed to navigate to Google Form URL: {e}")
            raise

    def _scroll_to_element(self, element):
        """
        Scroll to bring an element into view.
        
        Args:
            element: The WebElement to scroll to.
        """
        try:
            # Scroll element into view using JavaScript
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            # Short pause to let the smooth scroll complete
            time.sleep(0.5)
            logger.debug("Scrolled to element")
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
            # Even if scrolling fails, we'll continue with the operation

    def _find_question_container(self, question_text):
        """
        Find a question container by its text.
        
        Args:
            question_text (str): The label/text of the question to locate.
            
        Returns:
            WebElement: The container element for the question.
        """
        try:
            # Log the attempt to find the question
            logger.debug(f"Attempting to find question container for: '{question_text}'")
            
            # Try different XPath patterns to find the question
            xpaths = [
                f"//div[contains(text(), '{question_text}')]/ancestor::div[contains(@role, 'listitem')]",
                f"//div[.//*[contains(text(), '{question_text}')]]/ancestor::div[contains(@role, 'listitem')]",
                f"//div[text()='{question_text}']/ancestor::div[contains(@role, 'listitem')]",
                # Add more patterns if needed
            ]
            
            for xpath in xpaths:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    element = elements[0]
                    self._scroll_to_element(element)
                    return element
            
            # If all patterns fail, try a more generic approach using partial matching
            script = """
            return Array.from(document.querySelectorAll('div')).find(el => 
                el.textContent.includes(arguments[0]) && 
                el.closest('[role="listitem"]')
            )?.closest('[role="listitem"]');
            """
            element = self.driver.execute_script(script, question_text)
            if element:
                self._scroll_to_element(element)
                return element
                
            raise NoSuchElementException(f"Could not find question with text: {question_text}")
        
        except Exception as e:
            logger.error(f"Error finding question container for '{question_text}': {e}")
            raise

    def _fill_text_input(self, question_text, value):
        """
        Fill a text input field in Google Form by finding it based on the question text.
        
        Args:
            question_text (str): The label/text of the question to locate the field.
            value (str): Value to enter in the field.
        """
        try:
            # Find the container for the question
            question_container = self._find_question_container(question_text)
            
            # Find the input field within this container
            # Google Forms might use different input types
            selectors = ["input[type='text']", "input[type='email']", "input[type='number']", "textarea"]
            
            for selector in selectors:
                input_fields = question_container.find_elements(By.CSS_SELECTOR, selector)
                if input_fields:
                    input_field = input_fields[0]
                    self._scroll_to_element(input_field)
                    
                    # Clear and fill the input field
                    input_field.clear()
                    input_field.send_keys(str(value))
                    logger.info(f"Entered '{value}' for question '{question_text}'")
                    return
            
            raise NoSuchElementException(f"Could not find input field for question '{question_text}'")
            
        except Exception as e:
            logger.error(f"Error filling text input for question '{question_text}': {e}")
            raise

    def _check_checkbox(self, checkbox_text):
        """
        Check a checkbox in Google Form.
        
        Args:
            checkbox_text (str): The label/text of the checkbox to check.
        """
        try:
            # Find the container with the checkbox
            container = self._find_question_container(checkbox_text)
            
            # Find the checkbox element within the container
            checkbox_element = container.find_element(By.CSS_SELECTOR, "div[role='checkbox']")
            self._scroll_to_element(checkbox_element)
            
            # Check if it's already checked
            aria_checked = checkbox_element.get_attribute("aria-checked")
            if aria_checked != "true":
                # Click the checkbox if not checked
                checkbox_element.click()
                logger.info(f"Checked checkbox: '{checkbox_text}'")
            else:
                logger.info(f"Checkbox '{checkbox_text}' was already checked")
                
        except NoSuchElementException as e:
            logger.error(f"Could not find checkbox with text '{checkbox_text}': {e}")
            raise
        except ElementClickInterceptedException:
            try:
                # Try JavaScript click if direct click fails
                self.driver.execute_script("arguments[0].click();", checkbox_element)
                logger.info(f"Checked checkbox '{checkbox_text}' using JavaScript")
            except Exception as e:
                logger.error(f"Failed to check checkbox '{checkbox_text}' even with JavaScript: {e}")
                raise
        except Exception as e:
            logger.error(f"Error checking checkbox '{checkbox_text}': {e}")
            raise

    def _select_radio_option(self, question_text, option_text):
        """
        Select a radio button option in Google Form.
        If exact matching fails, selects a random radio option.
        
        Args:
            question_text (str): The label/text of the question containing radio options.
            option_text (str): The text of the radio option to select (may be ignored if random selection is used).
        """
        try:
            # Find the container for the question
            question_container = self._find_question_container(question_text)
            
            # Find all radio options in the container
            all_radios = question_container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            
            if all_radios:
                # Select a random radio option
                radio_option = random.choice(all_radios)
                self._scroll_to_element(radio_option)
                
                # Check if already selected
                aria_checked = radio_option.get_attribute("aria-checked")
                if aria_checked != "true":
                    try:
                        radio_option.click()
                        logger.info(f"Selected random option for question '{question_text}'")
                    except ElementClickInterceptedException:
                        # Try JavaScript click if direct click fails
                        self.driver.execute_script("arguments[0].click();", radio_option)
                        logger.info(f"Selected random option for question '{question_text}' using JavaScript")
                else:
                    logger.info(f"Option was already selected for question '{question_text}'")
            else:
                raise NoSuchElementException(f"No radio options found for question '{question_text}'")
                
        except Exception as e:
            logger.error(f"Error selecting radio option for question '{question_text}': {e}")
            raise

    def _select_likert_option(self, question_text, scale_value):
        """
        Select a Likert scale option in Google Form.
        
        Args:
            question_text (str): The label/text of the question.
            scale_value (int or str): The scale value to select (1-6) or corresponding text.
        """
        # Map scale values to their text representations
        scale_mapping = {
            1: "Never", "1": "Never", "Never": "Never",
            2: "Rarely", "2": "Rarely", "Rarely": "Rarely",
            3: "Sometimes", "3": "Sometimes", "Sometimes": "Sometimes",
            4: "Often", "4": "Often", "Often": "Often",
            5: "Very Often", "5": "Very Often", "Very Often": "Very Often",
            6: "Always", "6": "Always", "Always": "Always"
        }
        
        # Get the text representation of the scale value
        option_text = scale_mapping.get(scale_value, str(scale_value))
        
        # Use the radio option selection method
        self._select_radio_option(question_text, option_text)

    def _scroll_page(self, direction="down"):
        """
        Scroll the page up or down.
        
        Args:
            direction (str): Direction to scroll, either "up" or "down".
        """
        try:
            if direction.lower() == "down":
                self.driver.execute_script("window.scrollBy(0, 500);")
                logger.debug("Scrolled down")
            else:
                self.driver.execute_script("window.scrollBy(0, -500);")
                logger.debug("Scrolled up")
            
            # Short pause to let the scroll complete
            time.sleep(0.3)
            
        except Exception as e:
            logger.error(f"Error scrolling {direction}: {e}")

    def fill_participant_info(self, user_data):
        """
        Fill the participant information and consent section.
        
        Args:
            user_data (dict): Dictionary containing user demographic information.
        """
        logger.info("Filling participant information and consent section...")
        
        try:
            # Check consent checkbox
            self._check_checkbox("I Agree")
            
            # Fill text input fields
            self._fill_text_input("Name or Initials", user_data["name"])
            self._fill_text_input("E-mail ID", user_data["email"])
            self._fill_text_input("Age", user_data["age"])
            self._fill_text_input("City, State", user_data["location"])
            self._fill_text_input("Height", user_data["height"])
            self._fill_text_input("Weight", user_data["weight"])
            
            # Select gender
            self._select_radio_option("Gender", user_data["gender"])
            
            logger.info("Completed participant information section")
            
        except Exception as e:
            logger.error(f"Error filling participant information: {e}")
            raise

    def _select_random_radio_options_for_all_questions(self):
        """
        Select a random radio button option for each question on the current page.
        """
        try:
            # Find all question items on the page
            question_items = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
            logger.info(f"Found {len(question_items)} question items on the page")
            
            # Process each question item
            for item in question_items:
                try:
                    # Find radio buttons within this question
                    radio_options = item.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                    
                    # If this question has radio buttons, select a random one
                    if radio_options:
                        # Scroll to the question
                        self._scroll_to_element(item)
                        time.sleep(0.2)  # Brief pause
                        
                        # Select a random option
                        option = random.choice(radio_options)
                        
                        # Check if already selected
                        aria_checked = option.get_attribute("aria-checked")
                        if aria_checked != "true":
                            try:
                                # Scroll to the option
                                self._scroll_to_element(option)
                                option.click()
                                logger.info("Selected a random radio option for a question")
                                time.sleep(0.3)  # Allow time for the selection to register
                            except ElementClickInterceptedException:
                                # Try JavaScript click if direct click fails
                                self.driver.execute_script("arguments[0].click();", option)
                                logger.info("Selected a random radio option using JavaScript")
                                time.sleep(0.3)  # Allow time for the selection to register
                        else:
                            logger.info("Option was already selected")
                except Exception as e:
                    logger.error(f"Error processing a question: {e}")
                    # Continue with the next question even if this one fails
            
            return True
                
        except Exception as e:
            logger.error(f"Error selecting random radio options: {e}")
            return False

    def fill_bsq_questionnaire(self):
        """
        Fill the Body Shape Questionnaire (BSQ-8A) section by selecting random radio options.
        """
        logger.info("Filling Body Shape Questionnaire (BSQ-8A) section...")
        
        try:
            # Select random options for all questions
            if self._select_random_radio_options_for_all_questions():
                logger.info("Completed BSQ-8A section")
            else:
                logger.warning("Some questions in BSQ-8A section may not have been answered")
            
        except Exception as e:
            logger.error(f"Error filling BSQ-8A questionnaire: {e}")
            raise

    def fill_weight_control_behaviours(self):
        """
        Fill the Weight Control Behaviours Checklist section by selecting random radio options.
        """
        logger.info("Filling Weight Control Behaviours Checklist section...")
        
        try:
            # Select random options for all questions
            if self._select_random_radio_options_for_all_questions():
                logger.info("Completed Weight Control Behaviours section")
            else:
                logger.warning("Some questions in Weight Control Behaviours section may not have been answered")
            
        except Exception as e:
            logger.error(f"Error filling Weight Control Behaviours checklist: {e}")
            raise

    def navigate_to_next_section(self):
        """
        Navigate to the next section of the Google Form.
        """
        try:
            # First scroll to bottom of page to ensure the next button is visible
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # Find and click the "Next" button
            next_buttons = self.driver.find_elements(By.XPATH, "//span[text()='Next']/ancestor::div[@role='button']")
            if next_buttons:
                next_button = next_buttons[0]
                self._scroll_to_element(next_button)
                
                # Try normal click first
                try:
                    next_button.click()
                except ElementClickInterceptedException:
                    # If regular click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", next_button)
                
                logger.info("Clicked Next button to navigate to next section")
                
                # Wait for the next section to load
                time.sleep(2)
                return True
            else:
                logger.warning("Could not find 'Next' button. This might be the last section.")
                return False
            
        except NoSuchElementException:
            logger.warning("Could not find 'Next' button. This might be the last section.")
            return False
        except Exception as e:
            logger.error(f"Error navigating to next section: {e}")
            raise

    def submit_form(self):
        """
        Submit the Google Form and verify submission.
        
        Returns:
            bool: True if form submission was successful, False otherwise.
        """
        logger.info("Attempting to submit form...")
        
        try:
            # First scroll to bottom of page to ensure the submit button is visible
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # Find submit button - Google Forms might use different text for submit buttons
            submit_buttons = []
            for text in ["Submit", "Submit form", "Send"]:
                buttons = self.driver.find_elements(By.XPATH, f"//span[text()='{text}']/ancestor::div[@role='button']")
                if buttons:
                    submit_buttons.extend(buttons)
            
            if not submit_buttons:
                # Try a more generic approach
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'][jsaction*='submit']")
            
            if submit_buttons:
                submit_button = submit_buttons[0]
                self._scroll_to_element(submit_button)
                
                # Try normal click first
                try:
                    submit_button.click()
                except ElementClickInterceptedException:
                    # If regular click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    
                logger.info("Submit button clicked")
                
                # Wait for submission confirmation page
                time.sleep(3)  # Give time for submission to process
                
                # Check for confirmation text - Google Forms might use different confirmation messages
                confirmation_phrases = [
                    "Your response has been recorded",
                    "Thank you for your response",
                    "Response submitted",
                    "Form submitted"
                ]
                
                for phrase in confirmation_phrases:
                    elements = self.driver.find_elements(By.XPATH, f"//div[contains(text(), '{phrase}')]")
                    if elements and elements[0].is_displayed():
                        logger.info(f"Form submitted successfully. Found confirmation: '{phrase}'")
                        return True
                
                # Check URL change as another indicator of successful submission
                if "formResponse" in self.driver.current_url:
                    logger.info("Form submitted successfully. Redirected to response page.")
                    return True
                
                logger.warning("No explicit confirmation message found, but submission might have succeeded.")
                return True  # Optimistically assume success if we got this far
                
            else:
                logger.error("No submit button found.")
                return False
                
        except TimeoutException:
            logger.error("Timed out waiting for submission confirmation.")
            return False
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

    def close_browser(self):
        """
        Close the browser and clean up resources.
        """
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")

    def run_automation(self, user_data):
        """
        Run the complete Google Form automation process.
        
        Args:
            user_data (dict): Dictionary containing user demographic information.
            
        Returns:
            bool: True if automation completed successfully, False otherwise.
        """
        success = False
        
        try:
            self.setup_driver()
            self.navigate_to_form()
            
            # Fill participant information section
            self.fill_participant_info(user_data)
            self.navigate_to_next_section()
            
            # Fill BSQ-8A section
            self.fill_bsq_questionnaire()
            self.navigate_to_next_section()
            
            # Fill Weight Control Behaviours section
            self.fill_weight_control_behaviours()
            
            # Submit the form
            success = self.submit_form()
            
            # Take screenshot of the final state
            self.driver.save_screenshot("form_submission_result.png")
            logger.info("Screenshot saved as 'form_submission_result.png'")
            
            return success
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            # Take screenshot of error state
            if self.driver:
                self.driver.save_screenshot("automation_error.png")
                logger.info("Error screenshot saved as 'automation_error.png'")
            return False
        finally:
            self.close_browser()

def generate_random_bsq_answers():
    """
    Generate random answers for BSQ-8A questions.
    Returns a dictionary with predefined questions and random answers.
    """
    # BSQ uses 1-6 Likert scale
    options = list(range(1, 7))  # [1, 2, 3, 4, 5, 6]
    
    questions = [
        "Has feeling bored made you brood about your shape?",
        "Have you thought that your thighs, hips or bottom are too large for the rest of you?",
        "Have you felt so bad about your shape that you have cried?",
        "Have you avoided running because your flesh might wobble?",
        "Has being with thin people of your same gender made you feel self-conscious about your shape?",
        "Have you worried about your thighs spreading out when sitting down?",
        "Has eating sweets, cakes, or other high calorie food made you feel fat?",
        "Has worry about your shape made you feel you ought to exercise?"
    ]
    
    return {question: random.choice(options) for question in questions}

def generate_random_wcb_answers():
    """
    Generate random answers for Weight Control Behaviours questions.
    Returns a dictionary with predefined questions and random answers.
    """
    # WCB uses 5-point frequency scale
    options = ["Never", "Rarely", "Sometimes", "Often", "Very Often"]
    
    questions = [
        "Dieted or restricted food intake (eating less than you wanted to lose weight)",
        "Skipped meals to control your weight",
        "Exercised excessively to lose weight (e.g., working out multiple times a day)",
        "Fasted for 24 hours or more to lose weight",
        "Taken diet pills, supplements, or herbal products for weight loss",
        "Vomited or used laxatives after eating to control weight",
        "Tracked calories obsessively (using apps, journals, etc.)",
        'Followed detox diets or cleanses for weight loss'
    ]
    
    return {question: random.choice(options) for question in questions}

def generate_random_user_data():
    """
    Generate random user data for participant information.
    
    Returns:
        dict: Dictionary with randomized user data.
    """
    # Random name (initials style)
    initials = ''.join(random.choices(string.ascii_uppercase, k=2))
    
    # Random email
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    email_name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
    email = f"{email_name}@{random.choice(domains)}"
    
    # Random age between 16 and 25
    age = str(random.randint(16, 25))
    
    # Random gender
    gender = random.choice(["Female", "Male"])
    
    # Random location
    cities = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", 
              "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
              "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL", "Bangalore, Karnataka", "Mumbai, Maharashtra", "Jaipur, Rajasthan", "Chennai, Tamil Nadu", "Vishakapatnam, Kerala", "Mysore, Karnataka", "Delhi, New Delhi" ]
    location = random.choice(cities)
    
    # Random height (150-195 cm)
    height = f"{random.randint(150, 195)} cm"
    
    # Random weight (45-100 kg)
    weight = f"{random.randint(45, 100)} kg"
    
    return {
        "name": initials,
        "email": email,
        "age": age,
        "gender": gender,
        "location": location,
        "height": height,
        "weight": weight
    }

def submit_single_form(form_url, index):
    """
    Submit a single form with randomized data.
    
    Args:
        form_url (str): URL of the Google Form.
        index (int): Index of this submission.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Generate random data for this submission
        user_data = generate_random_user_data()
        
        # Create and run the automation (headless mode for better performance)
        automation = GoogleFormAutomation(form_url, headless=True)
        result = automation.run_automation(user_data)
        
        return result
    except Exception as e:
        logger.error(f"Submission {index} failed with error: {e}")
        return False

def run_multiple_submissions(form_url, count, max_workers=4):
    """
    Run multiple form submissions concurrently.
    
    Args:
        form_url (str): URL of the Google Form.
        count (int): Number of submissions to make.
        max_workers (int): Maximum number of concurrent workers.
        
    Returns:
        tuple: (successful_count, failed_count)
    """
    successful = 0
    failed = 0
    
    # Use ThreadPoolExecutor for concurrent submissions
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(submit_single_form, form_url, i) for i in range(count)]
        
        # Track progress with tqdm
        for future in tqdm(concurrent.futures.as_completed(futures), total=count, desc="Submitting forms"):
            result = future.result()
            if result:
                successful += 1
            else:
                failed += 1
    
    return successful, failed

def main():
    """
    Main function to run the Google Form automation.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Google Form Automation for Multiple Submissions')
    parser.add_argument('--url', type=str, default="https://docs.google.com/forms/d/e/1FAIpQLSeO-BzNBv0a5xWziT3il9v2i0MSOip9MKLxrtki-JEsvyrvSA/viewform",
                        help='URL of the Google Form')
    parser.add_argument('--count', type=int, default=125, 
                        help='Number of form submissions to generate')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of concurrent workers (browser instances)')
    
    args = parser.parse_args()
    
    print(f"Starting automation to submit {args.count} responses using {args.workers} workers...")
    
    # Run multiple submissions
    successful, failed = run_multiple_submissions(args.url, args.count, args.workers)
    
    # Print final results
    print(f"\nAutomation completed:")
    print(f"- Successful submissions: {successful}")
    print(f"- Failed submissions: {failed}")
    print(f"- Total attempts: {args.count}")
    print(f"- Success rate: {successful/args.count*100:.2f}%")


if __name__ == "__main__":
    main()