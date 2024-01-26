from machine import Pin, PWM,SoftI2C
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from BlynkLib import Blynk 
import network
import time
import urequests as requests
import utime
import gc

wifi_ssid = "Redmi Note 12"  # WiFi ağınızın SSID'si
wifi_password = "akigo4510"  # WiFi ağınızın şifresi
BLYNK_AUTH_TOKEN = "34KZfr_Q2k9DYUIn5unfwVaO-SMSPAIT"
blynk = Blynk(BLYNK_AUTH_TOKEN)



def send_to_blynk(value):
    virtual_pin = 0  # Göndermek istediğiniz sanal pin numarası
    print(f'Sending value {value} to virtual pin {virtual_pin}')
    blynk.virtual_write(virtual_pin, value)



api_key = "9XITFWAREAGRNFQ2"  # ThinkSpeak API anahtarınız
telegram_bot_token = "6709346715:AAEwoOJHJltM7UaE75IOM6ucR3aDT6tB-zQ"  # Telegram botunuzun token'ı
chat_id = "1612260988"  # Telegram chat ID'niz

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000) #I2C for ESP32
#i2c = I2C(scl=Pin(5), sda=Pin(4), freq=10000) #I2C for ESP8266
lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)
echo_pin = 17
trig_pin = 16
echo_pin_2 = 25
trig_pin_2 = 26
servo_pin = 27 
MAX_DISTANCE = 230  # Çöp kutusunun maksimum doluluk mesafesi

echo = Pin(echo_pin, Pin.IN)
trig = Pin(trig_pin, Pin.OUT)
echo_2 = Pin(echo_pin_2, Pin.IN)
trig_2 = Pin(trig_pin_2, Pin.OUT)
servo = PWM(Pin(servo_pin), freq=50)
wifi = network.WLAN(network.STA_IF)

notification_sent = False  # Bildirimin bir kez gönderildiğini belirten bayrak




def connect_wifi():
    wifi.active(True)
    if not wifi.isconnected():
        print('Ağa bağlanılıyor...')
        wifi.connect(wifi_ssid, wifi_password)
        while not wifi.isconnected():
            pass
        print('Bağlantı Başarılı! Ağ Ayarları:', wifi.ifconfig())
    return wifi

def check_wifi_connection():
    if wifi.isconnected():
        print("Bağlantı kuruldu!")
    else:
        print("Bağlantı başarısız oldu.")

def send_to_thingspeak(data):
    thingspeak_url = "https://api.thingspeak.com/update?api_key=" + api_key + "&field1=" + str(data) 

    response = requests.get(thingspeak_url)
    print("ThinkSpeak'a veri gönderildi. Yanıt:", response.text)
    response.close()


# (Önceki kodlar burada yer alır)

# (Önceki kodlar burada yer alır)

def calculate_fill_percentage(distance):
    if distance == -1 or distance == -1.00:  # Mesafe -1 cm ölçüldüğünde
        return 0  # Doluluk oranını 0 yap
    elif 0 < distance < MAX_DISTANCE:
        base_fill_percentage = 100 - ((distance / MAX_DISTANCE) * 100)
        adjusted_fill_percentage = base_fill_percentage   # Adding 10% to the base fill percentage
        return adjusted_fill_percentage if adjusted_fill_percentage <= 100 else 100  # Eğer hesaplanan oran 100'den büyükse 100 olarak döndür
    else:
        return -1





# (Kodun geri kalan kısmı burada yer alır)

# (Kodun geri kalan kısmı burada yer alır)

def measure_distance(samples=5):
    distances = []
    trig = Pin(trig_pin, Pin.OUT)
    echo = Pin(echo_pin, Pin.IN)

    def ultrasonic_sensor():
        trig.value(1)
        utime.sleep_us(10)
        trig.value(0)

        pulse_time = utime.ticks_us()

        while echo.value() == 0:
            pulse_time = utime.ticks_us()

        while echo.value() == 1:
            end_time = utime.ticks_us()

        pulse_duration = utime.ticks_diff(end_time, pulse_time)
        distance = (pulse_duration * 100) / 582  # HC-SR04 datasheet'ine göre hesaplama

        return distance

    try:
        for _ in range(samples):
            distance_cm = ultrasonic_sensor()
            if 2 < distance_cm < MAX_DISTANCE:  # Belirli bir alt sınır ekleyerek anormal değerleri eleme
                distances.append(distance_cm)
            utime.sleep_ms(20)  # Ölçümler arası bekleme süresi

        if distances:
            avg_distance = sum(distances) / len(distances)
            gc.collect()
            return avg_distance
        else:
            return -1

    except Exception as e:
        print("Hata:", e)
        return -1


def measure_distance_2(samples=5):
    distances = []
    trig_2 = Pin(trig_pin_2, Pin.OUT)
    echo_2 = Pin(echo_pin_2, Pin.IN)

    def ultrasonic_sensor_2():
        trig_2.value(1)
        utime.sleep_us(10)
        trig_2.value(0)

        pulse_time_start = time.ticks_us()
        pulse_time_end = pulse_time_start

        while echo_2.value() == 0:
            pulse_time_start = time.ticks_us()
            
            if time.ticks_diff(pulse_time_start, pulse_time_end) > 30000:  # Maksimum ölçüm süresi 30ms
                return -1

        while echo_2.value() == 1:
            pulse_time_end = time.ticks_us()

        pulse_duration = time.ticks_diff(pulse_time_end, pulse_time_start)
        distance = pulse_duration / 58  # HC-SR04 datasheet'ine göre hesaplama

        return distance if distance < 400 else -1  # 400cm'den uzak mesafeleri dikkate alma

    try:
        for _ in range(samples):
            distance_cm = ultrasonic_sensor_2()
            if 2 < distance_cm < 10:  # El algılama aralığını 2 cm ile 10 cm arasında ayarla
                distances.append(distance_cm)
            utime.sleep_ms(50)  # Ölçümler arası bekleme süresi

        if distances:
            avg_distance = sum(distances) / len(distances)
            gc.collect()
            return avg_distance
        else:
            return -1

    except Exception as e:
        print("Hata:", e)
        return -1



def send_telegram_message():
    telegram_url = "https://api.telegram.org/bot" + telegram_bot_token + "/sendMessage?chat_id=" + chat_id + "&text=Çöp%20kutusu%20doluluk%20oranı%20%90'ın%20üstüne%20çıktı!"
    response = requests.get(telegram_url)
    print("Telegram'a mesaj gönderildi. Yanıt:", response.text)
    response.close()

def activate_url():
    # Örnek olarak belirli bir URL'yi aktif hale getirme
    response = requests.get("https://api.telegram.org/bot6709346715:AAEwoOJHJltM7UaE75IOM6ucR3aDT6tB-zQ/sendMessage?chat_id=1612260988&text=%C3%87%C3%B6p%20kutusu%20doluluk%20oran%C4%B1%20%2570%27%C4%B1n%20%C3%BCst%C3%BCne%20%C3%A7%C4%B1kt%C4%B1!")
    if response.status_code == 200:
        print("URL aktive edildi.")
    else:
        print("URL aktive edilemedi.")







# (Previous code remains unchanged)

def get_distance():
    try:
        global notification_sent
        skip_measurement_time = 0  # Timestamp to track when to skip ultrasonic measurements

        while True:
            current_time = time.time()

            # Check if skip time has elapsed, and ultrasonic sensor is not in skip mode
            if current_time > skip_measurement_time:
                distance_2 = measure_distance_2()
                if distance_2 > 0 and distance_2 < 10:
                    print("El algılandı!")
                    lcd.clear()
                    lcd.putstr('El algılandı!')

                    # Servo activation
                    servo.duty(77)  # Servo motoru 90 derece konumuna getir (hesaplama değeri)
                    time.sleep(5)   # 2 saniye bekle
                    servo.duty(26)  # Servo motoru 0 derece konumuna getir (hesaplama değeri)
                    time.sleep(4)

                    lcd.clear()  # Clear the LCD after servo movement
                    

                    skip_measurement_time = current_time + 4  # Set skip time to current time + 4 seconds
                    time.sleep(2)

                check_wifi_connection()

                distance = measure_distance()
                print("Mesafe: %.2f cm" % distance)

                if distance == -1 or distance == -1.00:
                    fill_percentage = 0
                else:
                    fill_percentage = calculate_fill_percentage(distance)

                if fill_percentage >= 0:
                    if fill_percentage > 0:
                        print("Doluluk Oranı: %.2f%%" % fill_percentage)
                        lcd.move_to(0, 1)
                        lcd.putstr('Doluluk:')
                        text_to_display = '%.2f%%' % fill_percentage
                        lcd.putstr(text_to_display)
                        send_to_blynk(fill_percentage)

                    else:
                        print("Doluluk Oranı: %.2f%%" % fill_percentage)

                    if fill_percentage > 70 and not notification_sent:
                        activate_url()
                        send_telegram_message()
                        notification_sent = True

                    if fill_percentage <= 70:
                        notification_sent = False

                    send_to_thingspeak(fill_percentage)

            utime.sleep(1)

    except KeyboardInterrupt:
        pass

# (Rest of the code remains unchanged)






try:
    wifi = connect_wifi()
    while True:
        distance_2 = measure_distance_2()
        if distance_2 > 0 and distance_2 < 10:  # Eğer algılanan mesafe belirtilen maksimum mesafenin altındaysa
                print("El algılandı!")
                
                    
                servo.duty(77)  # Servo motoru 90 derece konumuna getir (hesaplama değeri)
                time.sleep(2)   # 2 saniye bekle
                servo.duty(26)  # Servo motoru 0 derece konumuna getir (hesaplama değeri)
                time.sleep(2)
        check_wifi_connection()

        distance = get_distance()
        print("Mesafe: %.2f cm" % distance)

        if distance > 0:
            fill_percentage = (distance / MAX_DISTANCE) * 100
            print("Doluluk Oranı: %.2f%%" % fill_percentage)
            

            if fill_percentage > 70 and not notification_sent:
                activate_url()
                send_telegram_message()
                notification_sent = True

            if fill_percentage <= 70:  # Yüzde 80'in altındaysa bildirimin tekrar gönderilmesine izin ver
                notification_sent = False

            send_to_thingspeak(fill_percentage)

        utime.sleep(1)

except KeyboardInterrupt:
    pass
