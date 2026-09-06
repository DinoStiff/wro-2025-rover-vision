import sensor, image, time
from matrix_mini import send_data

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_vflip(True)
sensor.set_hmirror(True)



THRESHOLDS = [
    (25, 67, 11, 89, -1, 88),    # class_id = 0
    (30, 66, -7, 34, -77, -37),  # class_id = 1
    (0, 22, -15, 7, -12, 13),     # class_id = 2
    (89, 100, -33, 13, -128, 14),
]

PIXELS_MIN = 120
AREA_MIN   = 120
MAX_BLOBS  = 24

NUM_ROWS   = 8                 # <- set to your expected vertical blocks
ROW_H      = 240 // NUM_ROWS

clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    found = []
    for r in range(NUM_ROWS):
        roi = (0, r * ROW_H, 320, ROW_H)  # x,y,w,h (band)
        for class_id, th in enumerate(THRESHOLDS):
            blobs = img.find_blobs(
                [th],
                pixels_threshold=PIXELS_MIN,
                area_threshold=AREA_MIN,
                merge=False,
                margin=0,
                roi=roi
            )
            if blobs:
                for b in blobs:
                    found.append((class_id, b))

    if found:
        found.sort(key=lambda t]: t[1].area(), reverse=True)
        found = found[:MAX_BLOBS]

        payload = [len(found)]
        for class_id, b in found:
            x, y = b.cx(), b.cy()
            a = int(b.area() / 2)
            img.draw_rectangle(b.rect())
            img.draw_cross(x, y)
            img.draw_string(b.x(), b.y()-10, f"C{class_id}:{x},{y}")
            payload += [class_id, x, y, a]

        send_data(payload)

    print(clock.fps())
