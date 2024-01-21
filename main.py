import random
import math
import time
import threading
import tkinter as tk
import logging
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(filename='symulacja.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Klasa Klienta
class Klient:
    def __init__(self, id_klienta):
        self.id_klienta = id_klienta
        self.pliki = self.generuj_pliki()
        self.czas_start = None
        self.ostatni_wynik_aukcji = 0

    def generuj_pliki(self):
        liczba_plikow = random.randint(1, 10)  # Maksymalnie 10 plików
        return sorted([random.randint(1*10**6, 512*10**6) for _ in range(liczba_plikow)])  # Rozmiar od 1MB do 512MB

    def rozpocznij_odliczanie(self):
        if not self.czas_start:
            self.czas_start = datetime.now()

    def zatrzymaj_odliczanie(self):
        if self.czas_start:
            self.czas_start = None

    def oblicz_czas_oczekiwania(self):
        if self.czas_start:
            return (datetime.now() - self.czas_start).total_seconds()
        return 0

# Klasa Dysku
class Dysk(threading.Thread):
    def __init__(self, id_dysku, serwer):
        super().__init__()
        self.id_dysku = id_dysku
        self.serwer = serwer
        self.predkosc_przesylania = 25 * 10 ** 6  # 10MB/s
        self.zatrzymaj = False
        self.aktywny_plik = None
        self.aktualny_klient = None  # Dodajemy nową właściwość
        self.postep_przesylania = 0
        self.blokada = threading.Lock()


    def run(self):
        while True:
            if self.zatrzymaj:
                time.sleep(1)  # Czekaj, gdy symulacja jest zatrzymana
                continue

            if not self.aktywny_plik:
                klient, plik = self.przeprowadz_aukcje(self.serwer.klienci)
                if klient:
                    self.aktywny_plik = plik
                    self.aktualny_klient = klient
                    # Rozpocznij przesyłanie od zapisanego postępu
                    start = self.postep_przesylania // 10
                    self.przeslij_plik(plik, start=start)
                    # Resetuj stan, jeśli przesyłanie zostało zakończone
                    if not self.zatrzymaj:
                        self.aktywny_plik = None
                        self.aktualny_klient = None

    def przeslij_plik(self, rozmiar_pliku, start=0):
        try:
            czas_przesylania = (rozmiar_pliku / self.predkosc_przesylania) / 10
            for i in range(start, 10):
                if self.zatrzymaj:
                    time.sleep(1)  # Czekaj, gdy symulacja jest zatrzymana
                    continue
                time.sleep(czas_przesylania)
                self.postep_przesylania += 10
            # Resetuj postęp, jeśli cały plik został przesłany
            if self.postep_przesylania == 100:
                logging.info(f"Dysk {self.id_dysku}: Zakończono przesyłanie pliku o rozmiarze {rozmiar_pliku}")
                self.postep_przesylania = 0
        except Exception as e:
            logging.error(f"Dysk {self.id_dysku}: Wystąpił błąd podczas przesyłania pliku - {e}")

    def przeprowadz_aukcje(self, klienci):
        najlepszy_wynik = -1
        wybrany_klient = None
        wybrany_plik = None

        # Lista klientów z plikami do przesłania
        klienci_z_plikami = [klient for klient in klienci if klient.pliki]

        # Liczba klientów biorących udział w aukcji
        k = len(klienci_z_plikami)

        for klient in klienci_z_plikami:
            rozmiar_pliku = klient.pliki[0]  # najmniejszy plik
            t = klient.oblicz_czas_oczekiwania()
            wynik = (k * 10 ** 9 / (rozmiar_pliku + 1)) + math.log(t + 1) / k
            if wynik > najlepszy_wynik:
                najlepszy_wynik = wynik
                wybrany_klient = klient
                wybrany_plik = rozmiar_pliku

        # Aktualizujemy wynik aukcji dla klienta, który wygrał aukcję
        if wybrany_klient:
            wybrany_klient.ostatni_wynik_aukcji = najlepszy_wynik
            wybrany_klient.pliki.pop(0)  # Usunięcie pliku z listy klienta
            return wybrany_klient, wybrany_plik
        else:
            return None, None

# Klasa Serwera
class Serwer:
    def __init__(self):
        self.klienci = []
        self.dyski = [Dysk(i, self) for i in range(5)]
        self.czy_aktywowana = False

    def czy_symulacja_aktywna(self):
        # Sprawdza, czy jakikolwiek dysk jest aktywny
        return any(dysk.is_alive() for dysk in self.dyski)

    def dodaj_klienta(self):
        nowy_klient = Klient(len(self.klienci) + 1)
        self.klienci.append(nowy_klient)

        # Jeśli symulacja jest aktywna, rozpocznij odliczanie czasu dla nowego klienta
        if self.czy_symulacja_aktywna():
            nowy_klient.rozpocznij_odliczanie()

    def uruchom(self):
        self.zatrzymaj_dyski()  # Upewniamy się, że poprzednie dyski są zatrzymane
        self.dyski = [Dysk(i, self) for i in range(5)]  # Tworzymy nowe wątki dysków
        for dysk in self.dyski:
            dysk.start()

    def zatrzymaj_dyski(self):
        for dysk in self.dyski:
            dysk.zatrzymaj = True
            if dysk.is_alive():  # Sprawdzenie, czy wątek został uruchomiony
                dysk.join()      # Oczekujemy na zakończenie wątku tylko jeśli był uruchomiony


    def rozpocznij_symulacje(self):
        for klient in self.klienci:
            klient.rozpocznij_odliczanie()
        if not self.czy_aktywowana:
            self.uruchom()
            self.czy_aktywowana = True
        else:
            for dysk in self.dyski:
                dysk.zatrzymaj = False

    def zatrzymaj_symulacje(self):
        for dysk in self.dyski:
            dysk.zatrzymaj = True
        for klient in self.klienci:
            klient.zatrzymaj_odliczanie()

    def czy_zakonczyc(self):
        return all(not klient.pliki for klient in self.klienci)

# Klasa Interfejsu Graficznego
class GUI:
    def __init__(self, serwer):
        self.serwer = serwer
        self.root = tk.Tk()
        self.root.title("Symulacja Serwera")
        self.root.geometry("800x600")  # Ustawienie stałego rozmiaru okna
        self.stworz_widgety()
        self.labels_dyski = [tk.Label(self.root) for _ in range(5)]
        self.labels_klienci = []
        self.aktualizuj_interfejs()

    def stworz_widgety(self):
        self.przycisk_start = tk.Button(self.root, text="Rozpocznij", command=self.rozpocznij_symulacje)
        self.przycisk_stop = tk.Button(self.root, text="Zatrzymaj", command=self.zatrzymaj_symulacje)
        self.przycisk_dodaj_klienta = tk.Button(self.root, text="Dodaj Klienta", command=self.dodaj_klienta)
        self.przycisk_start.pack()
        self.przycisk_stop.pack()
        self.przycisk_dodaj_klienta.pack()

    def aktualizuj_interfejs(self):
        for i, dysk in enumerate(self.serwer.dyski):
            postep = f"{dysk.postep_przesylania}%" if dysk.aktywny_plik else "Wolny"
            klient_info = f", Klient {dysk.aktualny_klient.id_klienta}" if dysk.aktualny_klient else ""
            self.labels_dyski[i].config(text=f"Dysk {i}: {postep}{klient_info}")
            self.labels_dyski[i].pack()

        for label in self.labels_klienci:
            label.destroy()
        self.labels_klienci.clear()

        for i, klient in enumerate(self.serwer.klienci):
            czas_oczekiwania = klient.oblicz_czas_oczekiwania()
            wynik_aukcji = f", Wynik aukcji: {klient.ostatni_wynik_aukcji:.2f}"
            rozmiary_plikow = ', '.join([f"{rozmiar//10**6}MB" for rozmiar in klient.pliki])
            label_text = f"Klient {klient.id_klienta}: {len(klient.pliki)} plików [{rozmiary_plikow}], Czas : {czas_oczekiwania:.2f} sekund{wynik_aukcji}"
            # label_text = f"Klient {klient.id_klienta}: {len(klient.pliki)} plików [{rozmiary_plikow}], {wynik_aukcji}"
            label = tk.Label(self.root, text=label_text)
            label.pack()
            self.labels_klienci.append(label)

        self.root.after(1000, self.aktualizuj_interfejs)

    def rozpocznij_symulacje(self):
        self.serwer.rozpocznij_symulacje()
        self.aktualizuj_interfejs()

    def zatrzymaj_symulacje(self):
        self.serwer.zatrzymaj_symulacje()
        self.aktualizuj_interfejs()

    def dodaj_klienta(self):
        self.serwer.dodaj_klienta()
        self.aktualizuj_interfejs()

    def uruchom(self):
        self.root.mainloop()

# Główna funkcja uruchamiająca symulację
def main():
    serwer = Serwer()
    gui = GUI(serwer)
    gui.uruchom()

if __name__ == "__main__":
    main()
