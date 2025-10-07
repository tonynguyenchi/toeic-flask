from PIL import Image
import os

# Folder containing your PNG files
input_folder = "F:\TOEIC Coach\ToeicCoach\ToeicCoach\static\images\input_pngs"
output_folder = "F:\TOEIC Coach\ToeicCoach\ToeicCoach\static\images\output_pngs"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".png"):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)

        width, height = img.size

       # Split horizontally (top/bottom)
        top_half = img.crop((0, 0, width, height // 2))
        bottom_half = img.crop((0, height // 2, width, height))


        # Save results
        base_name = os.path.splitext(filename)[0]
        top_half.save(os.path.join(output_folder, f"{base_name}_1.png"))
        bottom_half.save(os.path.join(output_folder, f"{base_name}_2.png"))

print("✅ Done! All files have been split.")
