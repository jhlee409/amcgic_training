import cv2
import numpy as np

# 동영상 설정
width = 1000
height = 10
fps = 30
duration = 10  # 초 단위

# VideoWriter 객체 생성
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('000.mp4', fourcc, fps, (width, height))

# 프레임 생성 및 저장
for _ in range(duration * fps):
    frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    out.write(frame)

# 동영상 파일 닫기
out.release()