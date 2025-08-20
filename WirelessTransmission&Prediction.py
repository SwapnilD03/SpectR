import pyrebase
import matplotlib.pyplot as plt
import cv2
import numpy as np
from keras.models import load_model
from PIL import Image
from keras.preprocessing.image import img_to_array
from urllib3.contrib.appengine import is_appengine_sandbox

# Firebase configuration

config={
     "apiKey": "AIzaSyBU7EuPMYnoqBVilzlPItSPnVWVsfJoYwM",
     "authDomain": "spectrophotometer-97c4f.firebaseapp.com",
     "databaseURL":"https://console.firebase.google.com/project/spectrophotometer-97c4f/database/spectrophotometer-97c4f-default-rtdb/data",
     "projectId": "spectrophotometer-97c4f",
     "storageBucket": "spectrophotometer-97c4f.appspot.com",
     "messagingSenderId": "311251530300",
     "appId": "1:311251530300:web:04a071b0c0bf9129b78939",
     "measurementId": "G-94RX2FGZQ1",
     "serviceAccount":"ServiceAccount.json",
     "databaseURL":"https://console.firebase.google.com/project/spectrophotometer-97c4f/database/spectrophotometer-97c4f-default-rtdb/data/~2F"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()

# Download the image
image_path = "saved_image.jpg"
storage.child("SentImage.jpg").download(filename="Received.jpg", path=image_path)

# Load the image using OpenCV
image = cv2.imread(image_path)
# cv2.imwrite("received_processed.jpg", image)
# Display the image using OpenCV
cv2.imshow('Received Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Assuming that the image contains spectrum data across its width:
# Convert the image to grayscale if it's not already
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Calculate the average intensity across the height for each column (wavelength)
intensity = np.mean(gray_image, axis=0)

# Generate the wavelength range from 400 to 720 nm
wavelengths = np.linspace(400, 700, len(intensity))

# Plot the Intensity vs Wavelength graph
plt.figure(figsize=(10, 6))
plt.plot(wavelengths, intensity, label='Intensity')
plt.xlabel('Wavelength (nm)')
plt.ylabel('Intensity')
plt.title('Intensity vs Wavelength')
plt.grid(True)

plot_image_path = "ivsw_plot.png"
plt.savefig(plot_image_path)
print(f"Intensity vs. Wavelength plot saved as '{plot_image_path}'")

plt.show()





# Load the pre-trained model
model = load_model(r"Models\1.keras")

# Load an image file
image = Image.open(image_path)

# Resize the image to match the input size of the model (e.g., 224x224 for many models)
image = image.resize((135, 85))

# Convert the image to array and normalize it
image = img_to_array(image)
image = np.expand_dims(image, axis=0)
#image = image / 255.0  # Normalize the image to the range [0, 1]

# Make predictions
predictions = model.predict(image)

# Assuming a single image, extract the predictions
predicted_class = np.argmax(predictions[0])

# Define the class names (this should match the classes used during training)
class_names = ['Fresh', 'Highly Aged', 'Lightly Aged', 'Moderately Aged']

# Get the predicted class name
predicted_class_name = class_names[predicted_class]

print(f"Predicted class: {predicted_class_name}")