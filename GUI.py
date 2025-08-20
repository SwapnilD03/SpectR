import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import tensorflow as tf
from keras.models import load_model
from keras.utils import img_to_array
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
try:
    import pyrebase
    FIREBASE_AVAILABLE = True
except ImportError:
    print("Pyrebase not available. Firebase upload will be disabled.")
    FIREBASE_AVAILABLE = False
import threading

class AgeingClassifier:
    def __init__(self, root):
        self.root = root
        self.root.title("SpectR.")
        self.root.geometry("900x1200")
        self.root.configure(bg="#121212")  
        self.root.overrideredirect(True)  
        
        # Initialize Firebase
        self.init_firebase()
        
        # Custom Title Bar
        self.create_custom_title_bar()
        
        # Main Content Frame
        self.main_frame = tk.Frame(self.root, bg="#121212")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Title Label
        self.title_label = tk.Label(
            self.main_frame,
            text="SpectR: Oil Adulteration Classifier",
            font=("Orbitron", 20, "bold"),
            fg="#FF0000",  
            bg="#121212"
        )
        self.title_label.pack(pady=20)
        
        # Button Frame
        self.button_frame = tk.Frame(self.main_frame, bg="#121212")
        self.button_frame.pack(pady=10)
        
        self.choose_button = self.create_button(
            self.button_frame, "Choose Image", self.choose_image
        )
        self.choose_button.grid(row=0, column=0, padx=10)
        
        self.capture_button = self.create_button(
            self.button_frame, "Capture Image", self.capture_image
        )
        self.capture_button.grid(row=0, column=1, padx=10)
        
        self.upload_button = self.create_button(
            self.button_frame, "Send to Firebase", self.manual_upload
        )
        self.upload_button.grid(row=0, column=2, padx=10)
        self.upload_button.config(state="disabled")  # Initially disabled
        
        # Firebase Status Label
        self.firebase_status_label = tk.Label(
            self.main_frame, 
            text="Firebase: Ready", 
            fg="#00FF00", 
            bg="#121212", 
            font=("Orbitron", 10)
        )
        self.firebase_status_label.pack(pady=5)
        
        # Image Display Area
        self.image_label = tk.Label(
            self.main_frame, text="Image Preview", fg="#FFFFFF", bg="#121212", font=("Orbitron", 14)
        )
        self.image_label.pack(pady=10)
        
        # Result Label
        self.result_label = tk.Label(
            self.main_frame, text="Prediction Result:", fg="#FFD700", bg="#121212", font=("Orbitron", 16, "bold")
        )
        self.result_label.pack(pady=10)
        
        # Track current image and results
        self.current_image_path = None
        self.current_prediction = None
        self.current_wavelengths = None
        self.current_intensity = None
        
        # Plot Display Area
        self.plot_frame = tk.Frame(self.main_frame, bg="#121212")
        self.plot_frame.pack(pady=20)

    def init_firebase(self):
        """Initialize Firebase configuration"""
        if not FIREBASE_AVAILABLE:
            print("Firebase not available - skipping initialization")
            self.storage = None
            return
            
        try:
            config = {
                "apiKey": "AIzaSyBU7EuPMYnoqBVilzlPItSPnVWVsfJoYwM",
                "authDomain": "spectrophotometer-97c4f.firebaseapp.com",
                "projectId": "spectrophotometer-97c4f",
                "storageBucket": "spectrophotometer-97c4f.appspot.com",
                "messagingSenderId": "311251530300",
                "appId": "1:311251530300:web:04a071b0c0bf9129b78939",
                "measurementId": "G-94RX2FGZQ1",
                "serviceAccount": "ServiceAccount.json",
                "databaseURL": "https://console.firebase.google.com/project/spectrophotometer-97c4f/database/spectrophotometer-97c4f-default-rtdb/data/~2F"
            }
            
            self.firebase = pyrebase.initialize_app(config)
            self.storage = self.firebase.storage()
            print("Firebase initialized successfully")
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            self.storage = None

    def upload_to_firebase(self, local_file_path, firebase_filename="SentImage.jpg", include_data=True):
        """Upload image and data to Firebase Storage in a separate thread"""
        def upload():
            try:
                self.update_firebase_status("Uploading...")
                
                # Upload image
                self.storage.child(firebase_filename).put(local_file_path)
                
                # Upload analysis data if available and requested
                if include_data and self.current_prediction and self.current_wavelengths is not None:
                    import json
                    import tempfile
                    import os
                    
                    # Create data dictionary
                    data = {
                        "prediction": self.current_prediction,
                        "wavelengths": self.current_wavelengths.tolist() if hasattr(self.current_wavelengths, 'tolist') else list(self.current_wavelengths),
                        "intensity": self.current_intensity.tolist() if hasattr(self.current_intensity, 'tolist') else list(self.current_intensity),
                        "timestamp": str(np.datetime64('now'))
                    }
                    
                    # Save to temporary JSON file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        json.dump(data, temp_file, indent=2)
                        temp_json_path = temp_file.name
                    
                    # Upload JSON data
                    json_filename = firebase_filename.replace('.jpg', '_data.json')
                    self.storage.child(json_filename).put(temp_json_path)
                    
                    # Clean up temp file
                    os.unlink(temp_json_path)
                
                self.update_firebase_status("Upload Complete!", "#00FF00")
                print(f"Image and data uploaded to Firebase as {firebase_filename}")
            except Exception as e:
                self.update_firebase_status("Upload Failed!", "#FF0000")
                print(f"Firebase upload error: {e}")
        
        if self.storage:
            # Run upload in separate thread to avoid blocking GUI
            upload_thread = threading.Thread(target=upload)
            upload_thread.daemon = True
            upload_thread.start()
        else:
            self.update_firebase_status("Firebase Not Available", "#FF0000")

    def manual_upload(self):
        """Manual upload triggered by button click"""
        if self.current_image_path:
            self.upload_to_firebase(self.current_image_path, include_data=True)
        else:
            messagebox.showwarning("No Image", "Please capture or select an image first!")

    def update_firebase_status(self, message, color="#FFFFFF"):
        """Update Firebase status label safely from any thread"""
        def update():
            self.firebase_status_label.config(text=f"Firebase: {message}", fg=color)
        
        # Schedule the update on the main thread
        self.root.after(0, update)

    def create_custom_title_bar(self):
        # Title Bar Frame
        self.title_bar = tk.Frame(self.root, bg="#333333", relief=tk.FLAT, height=30)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        
        # Title Label
        title_label = tk.Label(
            self.title_bar,
            text="SpectR",
            fg="#FFFFFF",
            bg="#333333",
            font=("Orbitron", 14, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Close Button
        close_button = tk.Button(
            self.title_bar,
            text="✕",
            bg="#333333",
            fg="#FF5555",
            font=("Arial", 12, "bold"),
            borderwidth=0,
            command=self.root.quit,
            activebackground="#FF5555",
            activeforeground="#FFFFFF"
        )
        close_button.pack(side=tk.RIGHT, padx=10)
        
        # Enable Dragging of the Custom Title Bar
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        x = self.root.winfo_x() + event.x - self.x
        y = self.root.winfo_y() + event.y - self.y
        self.root.geometry(f"+{x}+{y}")

    def create_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Orbitron", 12),
            bg="#1E1E1E",
            fg="#FF0000",  # Changed to red
            activebackground="#FF0000",  # Changed to red
            activeforeground="#1E1E1E",
            relief="flat",
            width=20
        )
        return button

    def choose_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )
        if file_path:
            self.process_image(file_path)

    def capture_image(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.result_label.config(text="Error: Could not open webcam")
            return

        print("Press 'Enter' to capture an image or 'q' to quit")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            cv2.imshow('Webcam View', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 13:  # Enter key
                # Select ROI like in your original Firebase code
                roi = frame[190:275, 250:385]  # Region of Interest
                file_path = 'Image.jpg'
                cv2.imwrite(file_path, roi)  # Save ROI instead of full frame
                print("Image saved as Image.jpg")
                break
            elif key == ord('q'):
                print("Quitting without saving.")
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()
        cv2.destroyAllWindows()
        self.process_image(file_path)

    def process_image(self, file_path):
        try:
            self.current_image_path = file_path  # Store current image path
            self.display_image(file_path)
            self.predict(file_path)
            self.plot_wavelength_vs_intensity(file_path)
            
            # Enable upload button now that we have processed an image
            self.upload_button.config(state="normal")
            
        except Exception as e:
            self.result_label.config(text=f"Error: {e}")

    def display_image(self, file_path):
        img = Image.open(file_path)
        img = img.resize((135, 85))
        img = ImageTk.PhotoImage(img)
        self.image_label.configure(image=img)
        self.image_label.image = img

    def predict(self, file_path):
        try:
            model = load_model(r'Models\1.keras')  # loading the model
            image = Image.open(file_path)
            image = image.resize((135, 85))   # resizing the captured image according to our model
            image = img_to_array(image)
            image = tf.expand_dims(image, axis=0)  

            prediction = model.predict(image)   # Doing the prediction

            predicted_class = np.argmax(prediction[0])   # Determining the predicted class of ageing

            class_names = ['Fresh', 'Highly Aged', 'Lightly Aged', 'Moderately Aged']
            predicted_class_name = class_names[predicted_class]
            
            # Store prediction for Firebase upload
            self.current_prediction = predicted_class_name

            self.result_label.config(text=f"Prediction: {predicted_class_name}")
        except Exception as e:
            self.result_label.config(text=f"Prediction Error: {e}")

    def plot_wavelength_vs_intensity(self, file_path):
        try:
            image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

            # Sum intensity values across rows to get the intensity distribution
            intensity = np.sum(image, axis=0)
            
            num_wavelengths = image.shape[1]
            wavelengths = np.linspace(400, 700, num_wavelengths)
            
            # Store data for Firebase upload
            self.current_wavelengths = wavelengths
            self.current_intensity = intensity  
            
            # Clear the previous plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()

            # Create the plot
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(wavelengths, intensity, label="Intensity")
            ax.set_title("Wavelength vs Intensity")
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity (arbitrary units)")
            ax.legend()

            # Embed the plot in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()
        except Exception as e:
            print(f"Plotting error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AgeingClassifier(root)
    root.mainloop()