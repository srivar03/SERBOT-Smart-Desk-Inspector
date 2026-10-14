import qrcode

classrooms = ["CLASSROOM-101", "CLASSROOM-102", "LIBRARY-A"]

for room in classrooms:
    img = qrcode.make(room)
    filename = f"{room}.png"
    img.save(filename)
    print(f"Generated: {filename}")