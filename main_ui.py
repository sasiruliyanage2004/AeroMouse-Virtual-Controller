import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item
from core.gesture_worker import GestureWorker

def create_image():
    width = 64
    height = 64
    color1 = (0, 120, 215) # Windows blue
    color2 = (255, 255, 255)
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill=color2)
    return image

icon = None
worker = None

def update_status(status_text):
    global icon
    if icon:
        icon.title = f"AI Mouse: {status_text}"
        try:
            # Show a notification bubble in Windows
            icon.notify(status_text, title="AI Virtual Mouse")
        except:
            pass

def on_quit(icon, item):
    global worker
    if worker:
        worker.stop()
    icon.stop()

def setup_app():
    global icon, worker
    
    # Start the AI Background Worker
    worker = GestureWorker(status_callback=update_status)
    worker.start()
    
    # Create System Tray icon
    menu = pystray.Menu(
        item('Exit', on_quit)
    )
    icon = pystray.Icon("VirtualMouse", create_image(), "Virtual Mouse Initializing...", menu)
    
    print("System Tray icon created! Running in background...")
    icon.run()

if __name__ == "__main__":
    setup_app()
