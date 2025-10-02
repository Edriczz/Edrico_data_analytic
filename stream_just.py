import cv2
import subprocess as sp
import os
from dotenv import load_dotenv

# Muat variabel dari file .env ke environment
load_dotenv()

# ================================= KONFIGURASI =================================
# Ambil konfigurasi dari environment variable yang dimuat dari file .env
rtsp_url = os.getenv("RTSP_URL")
rtmp_url = os.getenv("AMS_URL")

# Validasi: Pastikan variabel berhasil dimuat
if not rtsp_url or not rtmp_url:
    print("Error: Pastikan RTSP_URL dan AMS_URL sudah diatur dengan benar di file .env Anda.")
    exit()
# ===============================================================================

print("Mencoba membuka stream RTSP...")
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print(f"Error: Gagal membuka stream RTSP di URL: {rtsp_url}")
    exit()

print("Stream RTSP berhasil dibuka.")

# Dapatkan properti video
frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Gunakan FPS default jika tidak terdeteksi
if fps <= 0 or fps > 60: # Batasi FPS yg tidak wajar
    print(f"FPS tidak valid ({fps}), menggunakan default: 25.")
    fps = 25

print(f"Dimensi Frame Asli: {frame_w}x{frame_h}, FPS: {fps}")

# Tentukan koordinat ROI sesuai konfigurasi Anda
roi_x1 = int(frame_w * 0.25)
roi_y1 = int(frame_h * 0.10)
roi_x2 = int(frame_w * 0.50)
roi_y2 = int(frame_h * 0.90)

# Hitung dimensi frame ROI yang baru
roi_w = roi_x2 - roi_x1
roi_h = roi_y2 - roi_y1

print(f"Dimensi ROI: {roi_w}x{roi_h}")

# Perintah FFmpeg dengan encoder h264_nvenc dan preset 'p1'
command = [
    'ffmpeg',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', f'{roi_w}x{roi_h}',
    '-r', str(fps),
    '-i', '-',
    '-c:v', 'h264_nvenc',
    '-preset', 'p1',
    '-b:v', '2500k',
    '-maxrate', '3000k',
    '-bufsize', '5000k',
    '-pix_fmt', 'yuv420p',
    '-f', 'flv',
    rtmp_url
]

# Jalankan proses FFmpeg
print("Memulai proses FFmpeg untuk streaming ke Ant Media Server...")
ffmpeg_process = sp.Popen(command, stdin=sp.PIPE)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream selesai atau koneksi terputus.")
            break

        # Potong frame sesuai dengan koordinat ROI
        roi_frame = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        # Tulis frame yang sudah dipotong ke proses FFmpeg
        try:
            ffmpeg_process.stdin.write(roi_frame.tobytes())
        except BrokenPipeError:
            print("Koneksi ke FFmpeg terputus. Menghentikan stream.")
            break

except KeyboardInterrupt:
    print("Stream dihentikan oleh pengguna.")

finally:
    # Tutup semua proses dengan benar
    print("Membersihkan dan menutup semua proses...")
    if ffmpeg_process.stdin:
        ffmpeg_process.stdin.close()
    ffmpeg_process.wait()
    cap.release()
    print("Semua proses telah dihentikan.")