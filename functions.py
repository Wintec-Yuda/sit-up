import cv2
import math
import mediapipe as mp

# set validasi pinggul kiri
minPinggulKiri=105
maxPinggulKiri=165
# set validasi lutut kiri
minLututKiri=50
maxLututKiri=110

mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils
pose = mpPose.Pose()
red = (0, 0, 255)
green = (0, 255, 0)
blue = (255, 0, 0)
yellow = (0, 255, 255)
distance_threshold = 50

def calculate_angle(point1, point2, point3):
    a = math.dist(point1, point2)
    b = math.dist(point2, point3)
    c = math.dist(point1, point3)

    cosC = (a**2 + b**2 - c**2) / (2 * a * b)
    angleC = math.degrees(math.acos(cosC))

    return round(angleC, 2)

def draw_landmark_points(img, landmarks):
    for id, lm in enumerate(landmarks):
        h, w, c = img.shape
        cx, cy = int(lm.x * w), int(lm.y * h)

        if id in [11, 23, 25, 27]:
            cv2.circle(img, (cx, cy), 10, (0, 255, 0))
            cv2.putText(img, str(id), (cx - 10, cy - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            if id == 11:
                point_11 = (cx, cy)
            elif id == 23:
                point_23 = (cx, cy)
            elif id == 25:
                point_25 = (cx, cy)
            elif id == 27:
                point_27 = (cx, cy)

    return point_11, point_23, point_25, point_27, cx, cy

# validasi sit up
def validate_initial_position(angle_23, angle_25):
    if minPinggulKiri <= angle_23 <= maxPinggulKiri and minLututKiri <= angle_25 <= maxLututKiri:
        return True
    return False

# def validate_elbow(point_13, point_25):
#     distance = math.dist(point_13, point_25)

#     if distance < distance_threshold:
#         return True
#     return False

def validate_initial_sit_up(angle_25, initial_position_verified):
    if (minLututKiri <= angle_25 <= maxLututKiri) and initial_position_verified:
        return True
    return False

def draw_correct_position(img):
    cv2.putText(img, "Posisi Benar", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, green, 2)

def draw_wrong_position(img):
    cv2.putText(img, "Posisi Salah", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, red, 2)

def draw_remaining_time(img, remaining_time):
    cv2.putText(img, "Remaining Time: {:.2f}".format(remaining_time), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, yellow, 2)

def draw_count_sit_up(img, situp_count):
    cv2.putText(img, "Sit up: " + str(situp_count // 2), (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, yellow, 2)

def convert_to_hms(detik):
    if detik is None:
        return '--:--:--'  # Atau nilai default lainnya
    else:
        jam = detik // 3600
        detik_sisa = detik % 3600
        menit = detik_sisa // 60
        detik = detik_sisa % 60
        
        return '{:02}:{:02}:{:02}'.format(jam, menit, detik)
