import easyocr
import sys
import cv2
import os

def ocr_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} does not exist.")
        return

    # Load image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: OpenCV could not load image {image_path}.")
        return
    
    # Convert BGR (OpenCV default) to RGB for EasyOCR
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    print(f"Image loaded successfully. Size: {img_rgb.shape}")

    try:
        reader = easyocr.Reader(['nl', 'en'], gpu=False)
        # Pass the image array directly
        result = reader.readtext(img_rgb, detail=0)
        if not result:
            print("No text detected in the image.")
        for text in result:
            print(text)
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_script.py <image_path>")
        sys.exit(1)
    ocr_image(sys.argv[1])
