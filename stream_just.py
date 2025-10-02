import cv2
import subprocess as sp
import os
from dotenv import load_dotenv

# Muat variabel dari file .env ke environment
load_dotenv()

# ================================= KONFIGURASI =================================
# Ambil konfigurasi dari environment variable
rtsp_url = os.getenv("RTSP_URL")
rtmp_url = os.getenv("AMS_URL")

# Validasi
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

if fps <= 0 or fps > 60:
    print(f"FPS tidak valid ({fps}), menggunakan default: 25.")
    fps = 25

print(f"Dimensi Frame Asli: {frame_w}x{frame_h}, FPS: {fps}")

# Tentukan koordinat ROI
roi_x1 = int(frame_w * 0.25)
roi_y1 = int(frame_h * 0.10)
roi_x2 = int(frame_w * 0.50)
roi_y2 = int(frame_h * 0.90)

# Perintah FFmpeg dengan ukuran frame asli
command = [
    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
    '-s', f'{frame_w}x{frame_h}', '-r', str(fps), '-i', '-',
    '-c:v', 'h264_nvenc', '-preset', 'p1', '-b:v', '2500k',
    '-maxrate', '3000k', '-bufsize', '5000k', '-pix_fmt', 'yuv420p',
    '-f', 'flv', rtmp_url
]

print("Memulai proses FFmpeg untuk streaming ke Ant Media Server...")
ffmpeg_process = sp.Popen(command, stdin=sp.PIPE)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream selesai atau koneksi terputus.")
            break

        # ==================== PERUBAHAN WARNA ROI ====================
        # Mengubah warna dari (0, 255, 0) [Hijau] menjadi (255, 0, 0) [Biru]
        cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (255, 0, 0), 2)
        # =============================================================

        try:
            ffmpeg_process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("Koneksi ke FFmpeg terputus. Menghentikan stream.")
            break

except KeyboardInterrupt:
    print("Stream dihentikan oleh pengguna.")

finally:
    print("Membersihkan dan menutup semua proses...")
    if ffmpeg_process.stdin:
        ffmpeg_process.stdin.close()
    ffmpeg_process.wait()
    cap.release()
    print("Semua proses telah dihentikan.")