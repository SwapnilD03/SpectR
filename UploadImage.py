import pyrebase
import cv2

config={
     "apiKey": "AIzaSyBU7EuPMYnoqBVilzlPItSPnVWVsfJoYwM",
     "authDomain": "spectrophotometer-97c4f.firebaseapp.com",
     "projectId": "spectrophotometer-97c4f",
     "storageBucket": "spectrophotometer-97c4f.appspot.com",
     "messagingSenderId": "311251530300",
     "appId": "1:311251530300:web:04a071b0c0bf9129b78939",
     "measurementId": "G-94RX2FGZQ1",
     "serviceAccount":"ServiceAccount.json",
     "databaseURL":"https://console.firebase.google.com/project/spectrophotometer-97c4f/database/spectrophotometer-97c4f-default-rtdb/data/~2F"
}

firebase=pyrebase.initialize_app(config)
storage=firebase.storage()



capture = cv2.VideoCapture(0)  # Open the webcam connected to the device

if not capture.isOpened():

        print("Error!! Could not open video stream from webcam")
else:
        print("Press 'Enter' to capture an image or 'q' to quit")

        while True:
          
        
          ret, frame = capture.read() # Read an image from the webcam

          if not ret:

            print("Error!! Could not read image from webcam.")
            break

          cv2.imshow('Webcam View', frame)  # Display the image

          key = cv2.waitKey(1) & 0xFF    # Wait for the user to press a key and capture the image

        #Check if 'Enter' key is pressed to capture the image
          if key == 13:  # 13 -> the Enter key
            roi = frame[190:275, 250:385]  # Select the Region of Interest(ROI) [This has been adjusted according to our setup]
            
            filename="Image.jpg"
            cv2.imwrite(filename, roi)  # Save the captured image to a file named Image.jpg
            print("Image saved as Image.jpg")
            break
          elif key == ord('q'):
            # Check if 'q' key is pressed to quit without saving
            print("Quitting without saving.") 
            exit(0)
        
          

    # Release the video capture object and close all windows
capture.release()
cv2.destroyAllWindows()    

#Uploading the image
storage.child("SentImage.jpg").put("Image.jpg")