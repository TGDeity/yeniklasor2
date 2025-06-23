# Proje Test ve Yardımcı Script Özeti

Aşağıda projede bulunan tüm test ve yardımcı scriptlerin amacı ve kullanımı özetlenmiştir.

---

## Python Test Scriptleri

### test_upload.py
# Video yükleme API'sini manuel olarak test etmek için kullanılır. Bir video dosyasını API'ye yükler, yanıtı ve durumu kontrol eder.

### test_language_upload.py
# Video yükleme API'sini farklı dillerde çeviri seçeneğiyle test etmek için kullanılır. Desteklenen dilleri listeler, seçilen dilde video yükler, işlenmesini izler ve çıktıyı indirir.

### debug_video_processing.py
# Video işleme pipeline'ında sorun giderme ve sistem kontrolleri için kullanılır. Sistem kaynakları, GPU, Docker servisleri, Celery worker, Redis, loglar ve dosya varlıklarını kontrol eder.

---

## PowerShell Test Scriptleri

### test_upload.ps1
# test_video.mp4 dosyasını API'ye yükleyerek video yükleme fonksiyonunu test eder. Yanıtı ve task_id'yi ekrana basar.

### test_new_video.ps1
# testen.mp4 dosyasını API'ye yükler, yanıtı ekrana basar ve video_id ile işleme durumunu sorgular.

### simple_test.ps1
# Var olan bir test videosunu uploads klasörüne kopyalar ve ardından curl ile API'ye yükler. Temel yükleme testi için kullanılır.

### quick_test.ps1
# test_copy.mp4 dosyasını API'ye yükler, video_id'yi alır ve kısa bir süre sonra işleme durumunu sorgular.

### test_gpu_ffmpeg.ps1
# GPU destekli ffmpeg ile video işleme pipeline'ını test eder. Video yükler, işlenmesini izler ve worker loglarında GPU/FFmpeg kullanımı ile ilgili çıktıları kontrol eder.

### final_test.ps1
# ffe27801-5e05-4cb4-8f00-1342ed39f151_test.mp4 dosyasını API'ye yükler, işlenmesini izler ve sonucu ekrana basar. Son test olarak tüm pipeline'ı uçtan uca doğrular.

### check_gpu_usage.ps1
# Worker container ve ana makinede GPU kullanımını, nvidia-smi çıktısını, Docker GPU erişimini ve ilgili logları kontrol eder. GPU ile ilgili sorunları teşhis etmek için kullanılır.

---

Her bir script, API'nin veya altyapının belirli bir parçasını test etmek, doğrulamak veya sorun gidermek için hazırlanmıştır. Kullanım öncesi ilgili video dosyalarının uploads klasöründe mevcut olduğundan emin olunmalıdır. 