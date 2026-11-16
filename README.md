# Filament Etiketleyici

Filament etiketinin fotoğrafından ürün bilgilerini çıkaran, düzenlenebilir JSON üreten ve isteğe bağlı olarak makara kaydını Bambu Cloud Filament Yönetimi'ne ekleyen yerel bir web uygulaması.

## Neden yapıldı?

Filament makarası eklerken SKU, marka, malzeme ve renk gibi bilgileri elle girmek zaman alabiliyor ve yazım hatalarına yol açabiliyor. Bu proje etiket fotoğrafından bu alanları çıkarmayı, kullanıcıya doğrulatıp düzenletmeyi ve tekrar kullanılabilir JSON olarak kaydetmeyi amaçlıyor. Bambu Cloud bağlantısı isteğe bağlıdır.

## Özellikler

- Etiket fotoğrafını dosyadan seçme veya kamera ile çekme.
- EasyOCR ile görüntüden yerel OCR metni çıkarma; metni Gemini API ile yapılandırılmış alanlara dönüştürme.
- Tanınan malzeme, renk, HEX renk, marka ve SKU bilgilerini düzenleyip JSON olarak önizleme, kopyalama veya indirme.
- `filament_id` değerini malzeme kataloğundan belirleme; modelin bu ID'yi tahmin etmesine güvenmeme.
- Makara ağırlığını kullanılan, toplam ve kalan ağırlık olarak hesaplama:
  - Girilen değer 1000 g'dan azsa kullanılan miktar kabul edilir; toplam 1000 g varsayılır.
  - Girilen değer 1000 g veya daha fazlaysa tam makara ağırlığı kabul edilir; kullanılan miktar 0 g olur.
- İsteğe bağlı olarak Bambu Cloud'da slicer profilini bulma veya oluşturma ve Filament Yönetimi'ne makara ekleme.
- Yerel ağdan erişim ve mobil kamera için HTTPS sunucusu.

## Gereksinimler

- Python 3.10 veya üzeri.
- Gemini API anahtarı; etiket bilgisini yapılandırılmış çıktıya dönüştürmek için gereklidir.
- Bambu Cloud Bearer token'ı; yalnızca Bambu Cloud'a makara eklemek için gereklidir.
- EasyOCR ilk kullanımında OCR model dosyalarını indirebilir. Uygulama OCR'ı CPU'da çalıştırır; ilk çalışma yavaş olabilir.

## Kurulum

### Windows PowerShell

Proje klasöründe:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS veya Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## API anahtarı ve Bambu token'ı

Proje kökünde `.env` adlı dosya oluşturun:

```dotenv
GEMINI_API_KEY=Google_AI_Studio_API_anahtariniz
BAMBU_TOKEN=Bambu_Bearer_tokeniniz
```

`GEMINI_API_KEY`, Google Gemini API istemcisi tarafından kullanılır. Anahtar almak için Google hesabınızla [Google AI Studio API key sayfasını](https://aistudio.google.com/app/apikey) açıp bir API anahtarı oluşturun. Kota, faturalandırma ve kullanım koşullarını Google AI Studio'da kontrol edin.

`BAMBU_TOKEN` yalnızca Bambu Cloud entegrasyonu için gerekir. Bu proje Bambu'nun herkese açık, kararlı bir OAuth API akışını değil, Bambu Cloud isteklerinde kullanılan Bearer token'ı kullanır. Kendi hesabınızla giriş yaptığınız tarayıcıda geliştirici araçlarının Network sekmesini açıp Bambu Cloud API isteğinin Request Headers bölümündeki `Authorization: Bearer ...` değerini bulun; `.env` dosyasına yalnızca `Bearer ` sonrasındaki token kısmını yazın. Bu yöntem resmi ve kalıcı bir entegrasyon garantisi değildir; token süresi dolabilir veya Bambu API'si değişebilir.

API anahtarınızı ve token'ınızı kimseyle paylaşmayın, kaynak koda veya ekran görüntülerine eklemeyin. `.env` dosyası [.gitignore](.gitignore) içinde yok sayılır. Bu dosyayı Git'e zorla eklemeyin. Bir token yanlışlıkla paylaşıldıysa ilgili hizmetten yenileyin veya iptal edin.

İsteğe bağlı olarak token'ı salt okunur listeleme komutuyla kontrol edebilirsiniz:

```powershell
.\.venv\Scripts\python.exe entegration.py --list-cloud-filaments
```

## Web uygulamasını çalıştırma

Proje kökünde:

```powershell
.\.venv\Scripts\python.exe app.py
```

Uygulama varsayılan olarak HTTP `8000` ve HTTPS `8443` portlarında başlar. Terminalde yazdırılan yerel adresi açın. Aynı Wi-Fi ağındaki telefon veya başka bir cihaz için listelenen LAN adresini kullanın. Windows Güvenlik Duvarı sorarsa Python'a yalnızca güvenilir Özel ağlarda erişim izni verin.

Telefon kamerası için:

1. Uygulamanın yazdırdığı LAN adresindeki `http://<LAN_IP>:8000/root-ca.crt` adresinden yerel CA sertifikasını indirin.
2. Sertifikayı telefona güvenilir CA olarak kurun. iOS'ta sertifika profili kurulumuna ek olarak tam güveni etkinleştirmek gerekebilir.
3. `https://<LAN_IP>:8443` adresini açıp tarayıcının kamera iznini verin.

Kamera erişimi için sertifikanın kurulması gerekir; yalnızca HTTP adresini açmak yeterli değildir. Sertifika parmak izi uygulama başlangıcında terminale yazdırılır. Bu uygulamayı internete açmayın veya yönlendiricide port yönlendirmesi oluşturmayın; yalnızca güvendiğiniz yerel ağda kullanın. Sadece aynı bilgisayardan erişmek için:

```powershell
.\.venv\Scripts\python.exe app.py --host 127.0.0.1
```

Portları değiştirmek için `--port` ve `--https-port` seçeneklerini kullanabilirsiniz; örneğin `--port 8002 --https-port 8445`.

## Komut satırından JSON üretme

Etiket fotoğrafını OCR ile okuyup Gemini ile yapılandırılmış JSON üretmek için:

```powershell
.\.venv\Scripts\python.exe labeling.py "C:\gorseller\filament-etiketi.jpg"
```

JSON terminale yazdırılır. Görsel yolu verilmezse `ornek_belge.jpg` kullanılır.

## Veri akışı ve gizlilik

- Tarayıcıdaki görsel, etiketleme için yerel uygulama sunucusuna gönderilir; uygulama görseli proje klasörüne kaydetmez.
- OCR yerel bilgisayarda çalışır. OCR'dan çıkan metin, yapılandırılmış alanları üretmek için Google Gemini API'ye gönderilir.
- Bambu Cloud'a veri ancak kullanıcı Filament Yönetimi'ne ekleme işlemini başlattığında gönderilir.
- Etiketlerdeki kişisel veya gizli bilgileri kullanmadan önce bu veri akışını ve ilgili hizmetlerin gizlilik koşullarını değerlendirin.

## Teknik notlar

- Malzeme ve `filament_id` eşlemesi `filament_profiles.py` içindedir. Bilinmeyen malzemeler şu anda PLA profiline düşer.
- Bambu Cloud slicer profili oluşturulurken yazıcı profili varsayılan olarak `@BBL A1` kullanır. Başka yazıcılar için entegrasyon ayarı uyarlanmalıdır.
- OCR metninin Gemini tarafından doğru yorumlandığını varsaymayın; buluta eklemeden önce düzenleme ekranındaki bilgileri kontrol edin.

## Katkıda bulunma

Hata bildirimleri ve iyileştirme önerileri memnuniyetle karşılanır. Katkı göndermeden önce API anahtarı, token, `.env` dosyası veya kişisel etiket görselleri eklemediğinizi kontrol edin.

## Lisans

Bu depoda henüz bir `LICENSE` dosyası bulunmuyor. Açık kaynak olarak yeniden kullanım ve dağıtım izni vermek için yayımlamadan önce uygun bir lisans seçilip eklenmelidir.
