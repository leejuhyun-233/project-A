from PIL import Image, ImageDraw

# Create a new image with white background
car_image = Image.new("RGB", (50, 100), "white")
draw = ImageDraw.Draw(car_image)

# Draw a simple car shape (rectangle with two circles for wheels)
draw.rectangle([10, 30, 40, 90], fill="blue", outline="black")
draw.ellipse([5, 80, 15, 90], fill="black")
draw.ellipse([35, 80, 45, 90], fill="black")

# Save the image
car_image.save("car.png")
