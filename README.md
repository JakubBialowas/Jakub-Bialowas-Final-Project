Celem projektu jest stworzenie aplikacji monitorującej jakość powietrza w Polsce przy wykorzystaniu danych z Głównego Inspektoratu Ochrony Środowiska.

Podstawowe funkcjonalności aplikacji:
1. możliwość pobrania danych pomiarowych z Internetu 
2. możliwość zapisu danych do lokalnej relacyjnej bazy danych
3. możliwość pobrania danych „historycznych” z bazy ograniczona do 15 godzin wstech 
4. możliwość prezentacji danych w formie wykresu
5. możliwość analizy danych:
- liczba pomiarów
- Wartość minimalna
- Wartość maksymalna
- Średnia wartość
- Mediana
- Odchylenie Standardowe
- Zakres 
- Analiza trendu
- Analiza siły trendu

DANE POMIAROWE

Aplikacja powinna wykorzystywać dane publikowane bezpłatnie przez Główny Inspektorat
Ochrony Środowiska. Dane są dostępne poprzez dostępną w Internecie usługę REST.
Usługa zwraca odpowiedzi w formacie JSON. W zależności od skierowanego żądania (typu
GET) można uzyskać następujące informacje:
 - stacje pomiarowe w Polsce:
 - id – unikalny identyfikator stacji
 - stationName – nazwa stacji pomiarowej
 - gegrLat – szerokość geograficzna położenia stacji
 - gegrLon – długość geograficzna położenia stacji
 - city – informacje o adresie stacji, na którą składa się:
 - id – unikalny identyfikator lokalizacji
 - name – nazwa miejscowości w której znajduje się stacja
 - commune – informacje o gminie na które się składają się:
 - communeName – nazwa gminy
 - districtName – nazwa powiatu
 - provinceName – nazwa województwa
 - addressStreet – nazwa ulicy na której znajduje się stacja

Stanowiska pomiarowe, czyli czujniki w danej stacji pomiarowej:
 - id – unikalny identyfikator stanowiska pomiarowego
 - stationId – identyfikator stacji pomiarowej w której znajduje się dane
stanowisko pomiarowe
 - param – informacje o tym co jest mierzone:
 - paramName – nazwa mierzonego parametru
 - paramFormula – symbol mierzonego parametru
 - paramCode – kod parametru
 - idParam – identyfikator mierzonego parametru

dane pomiarowe:
 - key – kod mierzonego parametru
 - values - sekwencja par:
 - date – data i czas pomiaru
 - value – wartość mierzonego parametru

indeks jakości powietrza:
 - id – identyfikator stacji pomiarowej
 - stCalcDate – data i czas obliczenia indeksu
 - stIndexLevel – najgorszy indeks dla danej stacji:
 - id – poziom indeksu (w skali od 0 do 5)
 - indexLevelName – tekstowy opis poziomu indeksu
 - stSourceDataDate – data i czas zebrania danych na podstawie których liczony
był indeks
 - dalej podobne parametry dla każdego stanowiska pomiarowego
 - oraz wartości krytyczne – szczegóły w opisie API

Sposób wywołania usługi REST oraz przykładowe dane są dostępne na stronie:
https://powietrze.gios.gov.pl/pjp/content/api
Należy pamiętać, że wszystkie dane pobrane z usługi są tekstowe (nawet jeśli reprezentują
wartości liczbowe).
Dane pomiarowe są zbierane standardowo co godzinę. Mogą wystąpić sytuacje, gdy
o zadanej porze pomiar nie zostanie dokonany – wówczas zwracana jest wartość null.

DZIAŁANIE PROGRAMU

Program powinien być odporny na sytuacje, gdy nie mamy łączności lub usługa jest niedostępna. W takiej sytuacji użytkownik powinien zostać poinformowany o niedostępności danych i ewentualnie zaproponować skorzystanie z danych
„historycznych” (jeśli takie zostały wcześniej zapisane w bazie danych)

## Uruchomienie aplikacji

1. Proszę się upowenić, że posiadana jest wersja Pythona 3.10+.
2. (Opcjonalnie) Utwórz i aktywuj wirtualne środowisko:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. Zainstaluj zależności (apliakcja powinna automatycznie zainstalować pakiey):
   ```bash
   pip install -r requirements.txt
   ```
4. Uruchom aplikację GUI:
   ```bash
   python main.py
   ```

Domyślnie lokalna baza danych SQLite tworzona jest w katalogu `data/air_quality.db`.

## Uruchomienie testów

Aplikacja pozwala na uruchomienienie testów z poziomu aplikacji
Aby uruchomić, proszę kliknąć przycisk test danych historycznych

```bash
python -m unittest discover -s tests
```
