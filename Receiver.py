import pyrebase
import json
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
import requests
from datetime import datetime
import os

class FirebaseDataRetriever:
    def __init__(self):
        """Initialize Firebase connection"""
        self.init_firebase()
    
    def init_firebase(self):
        """Initialize Firebase configuration"""
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
    
    def download_image(self, firebase_filename="SentImage.jpg", local_filename="downloaded_image.jpg"):
        """Download image from Firebase Storage"""
        try:
            if not self.storage:
                print("Firebase not initialized")
                return None
            
            # Get download URL
            url = self.storage.child(firebase_filename).get_url(None)
            
            # Download the image
            response = requests.get(url)
            if response.status_code == 200:
                with open(local_filename, 'wb') as f:
                    f.write(response.content)
                print(f"Image downloaded as {local_filename}")
                return local_filename
            else:
                print(f"Failed to download image. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def download_data(self, firebase_filename="SentImage_data.json", local_filename="analysis_data.json"):
        """Download analysis data from Firebase Storage"""
        try:
            if not self.storage:
                print("Firebase not initialized")
                return None
            
            # Get download URL
            url = self.storage.child(firebase_filename).get_url(None)
            
            # Download the data
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Save locally
                with open(local_filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"Analysis data downloaded as {local_filename}")
                return data
            else:
                print(f"Failed to download data. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading data: {e}")
            return None
    
    def display_complete_analysis(self, image_filename="SentImage.jpg", data_filename="SentImage_data.json"):
        """Download and display complete analysis"""
        print("=" * 50)
        print("SPECTR ANALYSIS RETRIEVAL")
        print("=" * 50)
        
        # Download image
        image_path = self.download_image(image_filename)
        
        # Download analysis data
        analysis_data = self.download_data(data_filename)
        
        if not analysis_data:
            print("No analysis data found. Displaying image only.")
            if image_path:
                self.display_image_only(image_path)
            return
        
        # Display results
        self.show_analysis_results(image_path, analysis_data)
    
    def display_image_only(self, image_path):
        """Display just the image"""
        try:
            img = Image.open(image_path)
            plt.figure(figsize=(8, 6))
            plt.imshow(img)
            plt.title("Downloaded SpectR Image")
            plt.axis('off')
            plt.show()
        except Exception as e:
            print(f"Error displaying image: {e}")
    
    def show_analysis_results(self, image_path, analysis_data):
        """Display complete analysis with image, prediction, and plot"""
        try:
            # Create figure with subplots
            fig = plt.figure(figsize=(15, 10))
            
            # Display image
            ax1 = plt.subplot(2, 2, 1)
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                ax1.imshow(img)
                ax1.set_title("SpectR Analysis Image", fontsize=14, fontweight='bold')
                ax1.axis('off')
            else:
                ax1.text(0.5, 0.5, 'Image not available', ha='center', va='center')
                ax1.set_title("Image Not Found")
            
            # Display prediction
            ax2 = plt.subplot(2, 2, 2)
            prediction = analysis_data.get('prediction', 'Unknown')
            timestamp = analysis_data.get('timestamp', 'Unknown time')
            
            ax2.text(0.5, 0.7, 'PREDICTION RESULT', ha='center', va='center', 
                    fontsize=16, fontweight='bold')
            ax2.text(0.5, 0.5, f'{prediction}', ha='center', va='center', 
                    fontsize=20, fontweight='bold', color='red')
            ax2.text(0.5, 0.3, f'Analysis Time: {timestamp[:19]}', ha='center', va='center', 
                    fontsize=10)
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
            
            # Plot wavelength vs intensity
            ax3 = plt.subplot(2, 1, 2)
            wavelengths = np.array(analysis_data.get('wavelengths', []))
            intensity = np.array(analysis_data.get('intensity', []))
            
            if len(wavelengths) > 0 and len(intensity) > 0:
                ax3.plot(wavelengths, intensity, 'b-', linewidth=2, label='Intensity')
                ax3.set_xlabel('Wavelength (nm)', fontsize=12)
                ax3.set_ylabel('Intensity (arbitrary units)', fontsize=12)
                ax3.set_title('Spectral Analysis: Wavelength vs Intensity', fontsize=14, fontweight='bold')
                ax3.grid(True, alpha=0.3)
                ax3.legend()
            else:
                ax3.text(0.5, 0.5, 'No spectral data available', ha='center', va='center')
            
            plt.tight_layout()
            plt.suptitle('SpectR: Oil Adulteration Analysis Results', fontsize=16, fontweight='bold', y=0.98)
            plt.show()
            
            # Print summary to console
            print("\n" + "="*50)
            print("ANALYSIS SUMMARY")
            print("="*50)
            print(f"Prediction: {prediction}")
            print(f"Timestamp: {timestamp}")
            print(f"Spectral data points: {len(wavelengths)}")
            print(f"Wavelength range: {wavelengths[0]:.1f} - {wavelengths[-1]:.1f} nm" if len(wavelengths) > 0 else "No wavelength data")
            print("="*50)
            
        except Exception as e:
            print(f"Error displaying results: {e}")
    
    def list_firebase_files(self):
        """List all files in Firebase Storage"""
        try:
            if not self.storage:
                print("Firebase not initialized")
                return
            
            # Note: pyrebase doesn't have a direct list function
            # This is a workaround to check common file names
            common_files = [
                "SentImage.jpg",
                "SentImage_data.json",
                "Image.jpg",
                "Image_data.json"
            ]
            
            print("Checking for files in Firebase Storage:")
            print("-" * 40)
            
            available_files = []
            for filename in common_files:
                try:
                    url = self.storage.child(filename).get_url(None)
                    print(f"✓ {filename} - Available")
                    available_files.append(filename)
                except:
                    print(f"✗ {filename} - Not found")
            
            return available_files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

def main():
    """Main function to run the retriever"""
    retriever = FirebaseDataRetriever()
    
    print("SpectR Firebase Data Retriever")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Download and display latest analysis")
        print("2. Download specific file")
        print("3. List available files")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            retriever.display_complete_analysis()
        
        elif choice == '2':
            image_file = input("Enter image filename (e.g., SentImage.jpg): ").strip()
            data_file = input("Enter data filename (e.g., SentImage_data.json): ").strip()
            if image_file:
                retriever.display_complete_analysis(image_file, data_file)
        
        elif choice == '3':
            retriever.list_firebase_files()
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()