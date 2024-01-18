import random
import math
import time
import threading
import tkinter as tk
import logging

# Konfiguracja logowania
logging.basicConfig(filename='symulacja.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Klasa Klienta
class Klient:
    def __init__(self, id_klienta):
        self.id_klienta = id_klienta
        self.pliki = self.generuj_pliki()
        self.czas_oczekiwania = 0

    def generuj_pliki(self):
        liczba_plikow = random.randint(1, 25)
        return sorted([random.randint(1*10**6, 2*10**9) for _ in range(liczba_plikow)])  # Rozmiar w bajtach

# Klasa Dysku
class Dysk(threading.Thread):
    def __init__(self, id_dysku, serwer):
        super().__init__()
        self.id_dysku = id_dysku
        self.serwer = serwer
        self.zatrzymaj = False
        self.aktywny_plik = None
        self.blokada = threading.Lock()

    def run(self):
        while not self.zatrzymaj:
            with self.blokada:
                if not self.aktywny_plik:
                    klient, plik = self.przeprowadz_aukcje(self.serwer.klienci)
                    if klient:
                        self.aktywny_plik = plik
                        self.przeslij_plik(plik)
                        self.aktywny_plik = None
            time.sleep(1)

    def przeslij_plik(self, rozmiar_pliku):
        try:
            czas_przesylania = rozmiar_pliku / (10 * 10**6)  # 10MB/s
            time.sleep(czas_przesylania)
            logging.info(f"Dysk {self.id_dysku}: Zakończono przesyłanie pliku o rozmiarze {rozmiar_pliku}")
        except Exception as e:
            logging.error(f"Dysk {self.id_dysku}: Wystąpił błąd podczas przesyłania pliku - {e}")

    def przeprowadz_aukcje(self, klienci):
        najlepszy_wynik = -1
        wybrany_klient = None
        wybrany_plik = None

        for klient in klienci:
            if klient.pliki:
                rozmiar_pliku = klient.pliki[0]  # najmniejszy plik
                t = klient.czas_oczekiwania
                k = len(klienci)
                wynik = (k / (rozmiar_pliku + 1)) + math.log(t + 1) / k

                if wynik > najlepszy_wynik:
                    najlepszy_wynik = wynik
                    wybrany_klient = klient
                    wybrany_plik = rozmiar_pliku

        if wybrany_klient:
            wybrany_klient.pliki.pop(0)  # Usunięcie pliku z listy klienta
            return wybrany_klient, wybrany_plik
        else:
            return None, None

# Klasa Serwera
class Serwer:
    def __init__(self):
        self.klienci = []
        self.dyski = [Dysk(i, self) for i in range(5)]  # 5 dysków

    def dodaj_klienta(self):
        nowy_klient = Klient(len(self.klienci) + 1)
        self.klienci.append(nowy_klient)

    def uruchom(self):
        for dysk in self.dyski:
            dysk.start()

    def zatrzymaj_wszystko(self):
        for dysk in self.dyski:
            dysk.zatrzymaj = True
            dysk.join()

    def czy_zakonczyc(self):
        return all(not klient.pliki for klient in self.klienci)

# Klasa Interfejsu Graficznego
class GUI:
    def __init__(self, serwer):
        self.serwer = serwer
        self.root = tk.Tk()
        self.root.title("Symulacja Serwera")
        self.stworz_widgety()
        self.aktualizuj_interfejs()

    def stworz_widgety(self):
        self.przycisk_start = tk.Button(self.root, text="Rozpocznij", command=self.rozpocznij_symulacje)
        self.przycisk_stop = tk.Button(self.root, text="Zatrzymaj", command=self.zatrzymaj_symulacje)
        self.przycisk_dodaj_klienta = tk.Button(self.root, text="Dodaj Klienta", command=self.dodaj_klienta)
        self.przycisk_start.pack()
        self.przycisk_stop.pack()
        self.przycisk_dodaj_klienta.pack()

    def aktualizuj_interfejs(self):
        # Usunięcie starych widgetów
        for widget in self.root.winfo_children():
            widget.destroy()

        self.stworz_widgety()

        # Wyświetlanie stanu dysków i klientów
        for i, dysk in enumerate(self.serwer.dyski):
            tk.Label(self.root, text=f"Dysk {i}: {'Przesyła' if dysk.aktywny_plik else 'Wolny'}").pack()

        for i, klient in enumerate(self.serwer.klienci):
            tk.Label(self.root, text=f"Klient {klient.id_klienta}: {len(klient.pliki)} plików").pack()

        self.root.after(1000, self.aktualizuj_interfejs)

    def rozpocznij_symulacje(self):
        self.serwer.uruchom()

    def zatrzymaj_symulacje(self):
        self.serwer.zatrzymaj_wszystko()

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
