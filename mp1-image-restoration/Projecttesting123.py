import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

#MENGDIFINISIKAN MEDIAN FILTER

def median_filter(channel, ukuran_kernel=3):
    tinggi, lebar = channel.shape
    pad = ukuran_kernel // 2
    channel_padded = np.pad(channel, pad, mode='reflect')
    hasil = np.zeros((tinggi, lebar), dtype=np.float64)
    for i in range(tinggi):
        for j in range(lebar):
            kotak = channel_padded[i : i + ukuran_kernel, j : j + ukuran_kernel]
            hasil[i, j] = np.median(kotak)  # ambil nilai tengah

    return np.clip(hasil, 0, 255).astype(np.uint8)


#GAUSSIAN FILLTER, MITIP MEDIAN FILTER TTETAPI MEMILKI CARA YANG BERBEDA DENGAB MENGAMBIL NILAI RATA RATA DENGAN MEMILIKI BOBOT

def buat_kernel_gaussian(ukuran, sigma):
    sumbu = np.arange(ukuran) - ukuran // 2
    x, y = np.meshgrid(sumbu, sumbu)

    kernel = np.exp(-(x**2 + y**2) / (2 * sigma**2))     # Rumus Gaussian 2D

    kernel = kernel / kernel.sum()
    return kernel


def gaussian_filter(channel, ukuran_kernel=5, sigma=1.0):
    tinggi, lebar = channel.shape
    pad = ukuran_kernel // 2
    kernel = buat_kernel_gaussian(ukuran_kernel, sigma)

    channel_padded = np.pad(channel.astype(np.float64), pad, mode='reflect')
    hasil = np.zeros((tinggi, lebar), dtype=np.float64)

    for i in range(tinggi):
        for j in range(lebar):
            kotak = channel_padded[i : i + ukuran_kernel, j : j + ukuran_kernel]
            # Kalikan kotak dengan kernel, lalu jumlahkan
            hasil[i, j] = np.sum(kotak * kernel)

    return np.clip(hasil, 0, 255).astype(np.uint8)


#HISTOGRAM EQUALIZATION

def histogram_equalization(channel):
    tinggi, lebar = channel.shape
    total_piksel = tinggi * lebar

    histogram = np.zeros(256, dtype=np.float64)
    for nilai in channel.ravel():
        histogram[nilai] += 1

    cdf = np.cumsum(histogram)
    cdf_min = cdf[cdf > 0][0]

    lookup_table = np.round((cdf - cdf_min) / (total_piksel - cdf_min) * 255)
    lookup_table = np.clip(lookup_table, 0, 255).astype(np.uint8)

    # Terapkan lookup table ke semua piksel
    return lookup_table[channel]


#UNSHARP MASKING

def unsharp_masking(channel, ukuran_blur=5, sigma_blur=1.5, kekuatan=1.2):
    # Buat versi blur dari gambar
    versi_blur = gaussian_filter(channel, ukuran_kernel=ukuran_blur, sigma=sigma_blur)

    img_float  = channel.astype(np.float64)
    blur_float = versi_blur.astype(np.float64)

    mask = img_float - blur_float
    hasil = img_float + kekuatan * mask

    return np.clip(hasil, 0, 255).astype(np.uint8)


#GABUNGKAN SEMUA FILTER

def jalankan_restorasi():
    path_input  = 'input/lena_noisy.png'
    path_output = 'output/lena_restored.png'

    gambar_bgr = cv2.imread(path_input)
    if gambar_bgr is None:
        print("File Gada -> " + path_input)
        return

    print("Memulai Testing..")
   
   #konversi ke ruang warna YUV
    gambar_yuv = cv2.cvtColor(gambar_bgr, cv2.COLOR_BGR2YUV)
    Y, U, V    = cv2.split(gambar_yuv)


    tahapan = []
    tahapan.append(("Input (Rusak)", cv2.cvtColor(gambar_bgr, cv2.COLOR_BGR2RGB)))

    #MENGGUNAKAN MEDIAN FILTER HAPUS SALT N PEPPER NOISE
    print("Menggunakan Median Filter")
    Y = median_filter(Y, ukuran_kernel=5)
    U = median_filter(U, ukuran_kernel=5)
    V = median_filter(V, ukuran_kernel=5)

    # Simpan hasil step 1
    yuv_step1 = cv2.merge([Y, U, V])
    bgr_step1 = cv2.cvtColor(yuv_step1, cv2.COLOR_YUV2BGR)
    tahapan.append(( "Median Filter", cv2.cvtColor(bgr_step1, cv2.COLOR_BGR2RGB)))


    #MENGGUNAKAN GAUSSIAN FILTER UNTUK MENGURANGI GAUSSIAN NOISE
    print("Menggunaakn Gaussian Filter")
    Y = gaussian_filter(Y, ukuran_kernel=5, sigma=1.2)

    # Simpan hasil step 2
    yuv_step2 = cv2.merge([Y, U, V])
    bgr_step2 = cv2.cvtColor(yuv_step2, cv2.COLOR_YUV2BGR)
    tahapan.append(("Gaussian Filter", cv2.cvtColor(bgr_step2, cv2.COLOR_BGR2RGB)))


    #MENGGUNAKAN HISTOGRAM EQUALIZATION UNTUK MEMPERBAIKI KONTRAST
    print("Menggunakan Histogram Equalization")
    Y = histogram_equalization(Y)

    # Simpan hasil step 3
    yuv_step3 = cv2.merge([Y, U, V])
    bgr_step3 = cv2.cvtColor(yuv_step3, cv2.COLOR_YUV2BGR)
    tahapan.append(("Histogram Equalization", cv2.cvtColor(bgr_step3, cv2.COLOR_BGR2RGB)))

    #MENGGUNAKAN UNSHARP MASKING UNTUK MEMPERTAJAM DETAIL GAMBAR
    print("Menggunakan Unsharp Masking")
    Y = unsharp_masking(Y, ukuran_blur=5, sigma_blur=1.5, kekuatan=1.2)

    # Simpan hasil akhir
    yuv_akhir   = cv2.merge([Y, U, V])
    gambar_hasil = cv2.cvtColor(yuv_akhir, cv2.COLOR_YUV2BGR)
    tahapan.append(("Hasil Akhir", cv2.cvtColor(gambar_hasil, cv2.COLOR_BGR2RGB)))

    #OTUPUT GAMBAR DAN ERBANDINGAN GAMBAR
    cv2.imwrite(path_output, gambar_hasil)
    gambar_input_rgb  = cv2.cvtColor(gambar_bgr,    cv2.COLOR_BGR2RGB)
    gambar_output_rgb = cv2.cvtColor(gambar_hasil, cv2.COLOR_BGR2RGB)

    # Plot 1: Sebelum vs Sesudah
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle("Sebelum vs Sesudah Restorasi", fontsize=13)

    axes[0].imshow(gambar_input_rgb)
    axes[0].set_title("Gambar Rusak (Input)")
    axes[0].axis('off')

    axes[1].imshow(gambar_output_rgb)
    axes[1].set_title("Gambar Hasil Restorasi")
    axes[1].axis('off')

    plt.tight_layout()
    plt.savefig('output/comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Perbandingan disimpan ke: output/comparison.png")

    # Plot 2: Semua tahap pipeline
    jumlah_tahap = len(tahapan)
    fig2, axes2 = plt.subplots(1, jumlah_tahap, figsize=(4 * jumlah_tahap, 5))
    fig2.suptitle("Setiap Tahap Pipeline Restorasi", fontsize=13)

    for i in range(jumlah_tahap):
        label, gambar = tahapan[i]
        axes2[i].imshow(gambar)
        axes2[i].set_title(label, fontsize=9)
        axes2[i].axis('off')

    plt.tight_layout()
    plt.savefig('output/pipeline_steps.png', dpi=150, bbox_inches='tight')
    plt.close()

jalankan_restorasi()
