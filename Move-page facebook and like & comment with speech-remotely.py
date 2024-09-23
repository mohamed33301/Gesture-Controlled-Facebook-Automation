import cv2
import mediapipe as mp
import time
import speech_recognition as sr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Function to recognize gestures
def recognize_gesture(landmarks, handedness):
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]

    thumb_up = thumb_tip.y < thumb_ip.y < thumb_mcp.y
    index_down = index_tip.y > index_pip.y
    middle_down = middle_tip.y > middle_pip.y
    ring_down = ring_tip.y > ring_pip.y
    pinky_down = pinky_tip.y > pinky_pip.y

    if thumb_up and index_down and middle_down and ring_down and pinky_down:
        return "liked"
    
    # Calculate the average y-coordinate of the MCP joints to determine if the hand is raised
    mcp_y_avg = (landmarks[5].y + landmarks[9].y + landmarks[13].y + landmarks[17].y) / 4

    # Distinguish "next" and "prev" gestures
    if mcp_y_avg < 0.5:
        if handedness == "Right" and not (thumb_up and index_down and middle_down and ring_down and pinky_down):
            return "next"
        elif handedness == "Left" and not (thumb_up and index_down and middle_down and ring_down and pinky_down):
            return "prev"
        
    index_up = index_tip.y < index_pip.y
    middle_up = middle_tip.y < middle_pip.y
    if index_up and middle_up and ring_down and pinky_down:
        return "open_comments"

    if thumb_tip.y > thumb_ip.y and index_tip.y > index_pip.y and middle_tip.y > middle_pip.y and ring_tip.y > ring_pip.y and pinky_tip.y > pinky_pip.y:
        return "share"

    return "none"

# Function to find buttons by aria-label
def find_button_by_label(driver, label):
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@aria-label='{label}']"))
        )
        return button
    except Exception as e:
        print(f"Error finding button '{label}': {e}")
        return None

# Function to convert speech to text
def speech_to_text():
    with sr.Microphone() as source:
        print("Listening for speech...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        
        try:
            text = recognizer.recognize_google(audio, language="ar-SA")  # Using Arabic for recognition
            print(f"Recognized text: {text}")
            return text
        except sr.UnknownValueError:
            print("Speech not understood")
            return ""
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return ""
        


# Function to perform the send action (for Facebook post send button)
def perform_facebook_send(driver):
    try:
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Send this to friends']"))
        )
        if send_button:
            actions = ActionChains(driver)
            actions.move_to_element(send_button).perform()
            send_button.click()
            print("Send button on Facebook post clicked")
    except Exception as e:
        print(f"Error performing send action on Facebook: {e}")

# Function to perform the share action
def perform_facebook_share(driver):
    try:
        share_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Send this to friends or post it on your timeline.']"))
        )
        if share_button:
            actions = ActionChains(driver)
            actions.move_to_element(share_button).perform()
            share_button.click()
            print("Facebook Share button clicked")

            # Optionally, handle further actions after clicking Share (if necessary)
            # Example: choosing "Share now" from the menu
            share_now_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Share now']"))
            )
            if share_now_button:
                share_now_button.click()
                print("Post shared on your timeline")
                
    except Exception as e:
        print(f"Error performing share action: {e}")

# Perform Facebook action based on the gesture
def perform_facebook_action(driver, gesture):
    if gesture == "liked":
        try:
            like_button = find_button_by_label(driver, "Like")
            if like_button:
                actions = ActionChains(driver)
                actions.move_to_element(like_button).perform()
                like_button.click()
                print("Like button clicked")
        except Exception as e:
            print(f"Error performing like action: {e}")
    
    elif gesture == "open_comments":
        try:
            comment_button = find_button_by_label(driver, "Comment")
            if comment_button:
                actions = ActionChains(driver)
                actions.move_to_element(comment_button).perform()
                comment_button.click()
                print("Comment section opened")

                # Capture speech and enter it into the comment box once
                comment_text = speech_to_text()
                if comment_text:
                    # Wait for the comment box to be clickable
                    comment_box = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Comment']"))
                    )
                    # Add a short delay to ensure the comment box is ready for input
                    time.sleep(2)
                    comment_box.click()
                    actions.send_keys(comment_text).perform()
                    print(f"Comment written: {comment_text}")
                    
                    # Submit the comment after writing it
                    actions.send_keys(Keys.RETURN).perform()
                    print("Comment submitted")
                    
        except Exception as e:
            print(f"Error opening comments: {e}")
    elif gesture == "send":
        perform_facebook_send(driver)
    elif gesture == "share":
        perform_facebook_share(driver)

# Selenium setup
chrome_options = Options()
chrome_options.add_argument(r"C:\Users\Lenovo\AppData\Local\Google\Chrome\User Data")  # Replace with your Chrome user data path
chrome_service = Service("D:/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")  # Path to ChromeDriver

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

facebook_url="https://www.facebook.com/profile.php?id=100039778362581"
driver.get(facebook_url)

# Wait for the page to load
time.sleep(2)

# State variables
liked_state = False
scroll_timestamp = time.time()

def scroll_faster(driver, direction, scrolls=1):
    body = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(scrolls):
        if direction == "down":
            body.send_keys(Keys.PAGE_DOWN)
        elif direction == "up":
            body.send_keys(Keys.PAGE_UP)
        time.sleep(0.1)  # Small delay for content to load

# Start capturing video from webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            handedness = hand_handedness.classification[0].label
            gesture = recognize_gesture(landmarks, handedness)

            print(f"Hand: {handedness}, Gesture: {gesture}")

            # Only allow scrolling if the liked state is False
            if not liked_state and (time.time() - scroll_timestamp > 1):
                if gesture == "next":
                    print("Next gesture detected - Scrolling down")
                    scroll_faster(driver, "down", scrolls=1)  # Scroll down faster
                    scroll_timestamp = time.time()  # Reset timestamp for debounce

                elif gesture == "prev":
                    print("Previous gesture detected - Scrolling up")
                    scroll_faster(driver, "up", scrolls=1)  # Scroll up faster
                    scroll_timestamp = time.time()  # Reset timestamp for debounce

            if gesture != "none":
                perform_facebook_action(driver, gesture)

    # Display the frame
    cv2.imshow("Hand Gesture Control", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
driver.quit()
