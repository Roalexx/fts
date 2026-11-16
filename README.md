**[English](#filament-labeler) | [Türkçe](#filament-etiketleyici)**

# Filament Labeler

A local web application that extracts product information from a filament label photo, generates editable JSON, and optionally adds a spool record to Bambu Cloud Filament Management.

## Why this project?

Adding a filament spool can involve manually entering details such as SKU, brand, material, and color, which takes time and can lead to typos. This project extracts those fields from a label photo, lets you review and edit them, and saves them as reusable JSON. The Bambu Cloud integration is optional.

## Features

- Select a label photo from a file or take one with a camera.
- Extract OCR text locally with EasyOCR and use the Gemini API to turn it into structured fields.
- Edit the recognized material, color, HEX color, brand, and SKU; preview, copy, or download the result as JSON.
- Resolve `filament_id` from the material catalog instead of relying on the model to guess it.
- Calculate used, total, and remaining spool weight:
  - Values below 1000 g are treated as the amount used, with the total assumed to be 1000 g.
  - Values of 1000 g or more are treated as the full spool weight, with 0 g used.
- Optionally find or create a slicer profile in Bambu Cloud and add a spool to Filament Management.
- Run an HTTPS server for local-network access and mobile camera use.

## Requirements

- Python 3.10 or later.
- A Gemini API key, required to convert label information into structured output.
- A Bambu Cloud Bearer token, required only to add a spool to Bambu Cloud.
- EasyOCR may download model files on first use. OCR runs on the CPU, so the first run may be slow.

## Installation

### Windows PowerShell

From the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## API key and Bambu token

Create a file named `.env` in the project root:

```dotenv
GEMINI_API_KEY=your_Google_AI_Studio_API_key
BAMBU_TOKEN=your_Bambu_Bearer_token
```

`GEMINI_API_KEY` is used by the Google Gemini API client. To get a key, sign in with your Google account, open the [Google AI Studio API key page](https://aistudio.google.com/app/apikey), and create an API key. Check your quota, billing, and usage terms in Google AI Studio.

`BAMBU_TOKEN` is needed only for the Bambu Cloud integration. This project uses the Bearer token used in Bambu Cloud requests rather than a public, stable OAuth API flow from Bambu. In a browser where you are signed in to your own account, open Developer Tools and go to the Network tab. Find the `Authorization: Bearer ...` value in the Request Headers of a Bambu Cloud API request, and put only the part after `Bearer ` in your `.env` file. This is not an official or guaranteed permanent integration; the token may expire or the Bambu API may change.

Do not share your API key or token, or include them in source code or screenshots. The `.env` file is ignored by [.gitignore](.gitignore). Do not force-add it to Git. If a token is accidentally exposed, renew or revoke it with the relevant service.

You can optionally check the token using the read-only listing command:

```powershell
.\.venv\Scripts\python.exe entegration.py --list-cloud-filaments
```

## Run the web application

From the project root:

```powershell
.\.venv\Scripts\python.exe app.py
```

By default, the application starts on HTTP port `8000` and HTTPS port `8443`. Open the local address printed in the terminal. To connect from a phone or another device on the same Wi-Fi network, use the listed LAN address. If Windows Firewall prompts you, allow Python access only on trusted Private networks.

To use a phone camera:

1. Download the local CA certificate from `http://<LAN_IP>:8000/root-ca.crt` using the LAN address printed by the application.
2. Install the certificate on your phone as a trusted CA. On iOS, you may also need to enable full trust after installing the certificate profile.
3. Open `https://<LAN_IP>:8443` and grant the browser permission to use the camera.

The certificate must be installed to access the camera; opening the HTTP address alone is not enough. The certificate fingerprint is printed in the terminal when the application starts. Do not expose this application to the internet or configure port forwarding on your router; use it only on a trusted local network. To allow access only from the same computer:

```powershell
.\.venv\Scripts\python.exe app.py --host 127.0.0.1
```

Use the `--port` and `--https-port` options to change the ports, for example `--port 8002 --https-port 8445`.

## Generate JSON from the command line

To read a label photo with OCR and generate structured JSON with Gemini:

```powershell
.\.venv\Scripts\python.exe labeling.py "C:\images\filament-label.jpg"
```

The JSON is printed to the terminal. If no image path is provided, `ornek_belge.jpg` is used.

## Data flow and privacy

- The image in the browser is sent to the local application server for labeling; the application does not save the image in the project directory.
- OCR runs on the local computer. The text extracted by OCR is sent to the Google Gemini API to generate structured fields.
- Data is sent to Bambu Cloud only when the user starts the action to add a spool to Filament Management.
- Review this data flow and the privacy terms of the relevant services before using labels that contain personal or confidential information.

## Technical notes

- Material and `filament_id` mappings are in `filament_profiles.py`. Unknown materials currently fall back to the PLA profile.
- When creating a Bambu Cloud slicer profile, the printer profile defaults to `@BBL A1`. The integration settings need to be adapted for other printers.
- Do not assume Gemini interpreted the OCR text correctly; review the information in the editing screen before adding it to the cloud.

## Contributing

Bug reports and suggestions for improvements are welcome. Before submitting a contribution, make sure it does not include an API key, token, `.env` file, or personal label photos.

## License

This project is licensed under the [GNU Affero General Public License v3 (AGPL-3.0)](LICENSE). See the `LICENSE` file for the terms of use, modification, and distribution.

---

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

Bu proje, [GNU Affero Genel Kamu Lisansı sürüm 3 (AGPL-3.0)](LICENSE) kapsamında lisanslanmıştır. Kullanım, değiştirme ve dağıtım koşulları için `LICENSE` dosyasına bakın.
