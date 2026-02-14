#include <Wire.h>                                 // Bibliothek um I2C-Bus mit Arduino zu nutzen
#include <Adafruit_ADS1015.h>                     // Bibliothek für ADS1x15
#include <Adafruit_MCP4725.h>                     // Bibliothek für MCP4725
#include <TimerOne.h>

Adafruit_ADS1115 ads(0x48);                       // ADS1115 mit Adresse 0x48
Adafruit_MCP4725 dac;                             // MCP4725

float FGEN_Frequenz = 10;
float FGEN_Amplitude = 2;
float FGEN_Offset = 0;
String FGEN_Waveform = "SIN";
bool FGEN_On = true;

const int DSO_MaxAnzahlMesswerte = 100;
volatile float DSO_Messwerte1[DSO_MaxAnzahlMesswerte];
volatile float DSO_Messwerte2[DSO_MaxAnzahlMesswerte];
volatile int DSO_Messwertzaehler = 0;
volatile bool DSO_On = false;
volatile bool DSO_Fertig = false;
int DSO_AnzahlMesswerte = 100;
float DSO_Abtastzeit = 10e-3;

void setup(void) 
{
  Serial.begin(9600);                             // Initialisieren der seriellen Verbindung zum PC
  
  dac.begin(0x62);                                // Initialisieren der I2C Verbindung zum MCP4725 mit Adresse 0x62
  ads.begin();                                    // Initialisieren der I2C Verbindung zum ADS1115

  Timer1.initialize(DSO_Abtastzeit*1e6);          // Initialisieren des Timers
}

void readDSO(void)
{
  if (DSO_Messwertzaehler<DSO_AnzahlMesswerte)
  {
    int Messwert1 = analogRead(A6);                                                   // Auslesen von Aanalogeingang 6
    DSO_Messwerte1[DSO_Messwertzaehler] = (float(Messwert1)/1024*4.599-2.5)*220/50;   // Umrechnen in Spannung am Eingang des DSO

    int Messwert2 = analogRead(A7);                                                   // Auslesen von Aanalogeingang 7
    DSO_Messwerte2[DSO_Messwertzaehler] = (float(Messwert2)/1024*4.599-2.5)*220/50;   // Umrechnen in Spannung am Eingang des DSO
    
    DSO_Messwertzaehler++;
  }
  else
  {
    Timer1.detachInterrupt();
    DSO_On = false;
    DSO_Fertig = true;
  }
}

void loop(void) 
{
  if (not DSO_On && not DSO_Fertig && Serial.available())
  {
    String Befehl = Serial.readStringUntil('\r');
    Befehl.trim();

    if(Befehl == "*IDN?")
    {
      Serial.println("CoMeter v2019 (Arduino Nano)"); 
    }
    else if(Befehl=="A0?")
    {
      int Messwert = analogRead(A0);                        // Auslesen von Aanalogeingang 0
      Serial.println(Messwert);                             // Messwert an PC senden
    }
    else if(Befehl=="A1?")
    {
      int Messwert = analogRead(A1);                        // Auslesen von Aanalogeingang 1
      Serial.println(Messwert);                             // Messwert an PC senden
    }
    else if(Befehl=="A2?")
    {
      int Messwert = analogRead(A2);                        // Auslesen von Aanalogeingang 2
      Serial.println(Messwert);                             // Messwert an PC senden
    }
    else if(Befehl=="A3?")
    {
      int Messwert = analogRead(A3);                        // Auslesen von Aanalogeingang 3
      Serial.println(Messwert);                             // Messwert an PC senden
    }
    else if(Befehl=="ADS:A0?")
    {
      int16_t Messwert_A0 = ads.readADC_SingleEnded(0);     // Auslesen von Eingang A0 des ADS1115 (16 Bit)
      Serial.println(Messwert_A0);                          // Messwert an PC senden
    }
    else if(Befehl=="ADS:A1?")
    {
      int16_t Messwert_A1 = ads.readADC_SingleEnded(1);     // Auslesen von Eingang A1 des ADS1115 (16 Bit)
      Serial.println(Messwert_A1);                          // Messwert an PC senden
    }
    else if(Befehl=="ADS:A2?")
    {
      int16_t Messwert_A2 = ads.readADC_SingleEnded(2);     // Auslesen von Eingang A2 des ADS1115 (16 Bit)
      Serial.println(Messwert_A2);                          // Messwert an PC senden
    }
    else if(Befehl=="MEAS:VOLT:DC?" || Befehl=="MEAS:VOLT?")
    {   
      int16_t Messwert_A3 = ads.readADC_SingleEnded(3);     // Auslesen von Eingang A3 des ADS1115 (16 Bit)
      float Spannung_A3 = Messwert_A3*0.1875e-3;            // Umrechnen in Spannung am Eingang A3 des ADS1115
      float Spannung_DMM = Spannung_A3;                     // Umrechnen in Spannung am Eingang des DMM
  
      Serial.println(Spannung_DMM,4);                       // DMM-Spannung an PC senden (mit 4 Nachkommastellen)
    }
    else if(Befehl=="MEAS:CURR:DC?" || Befehl=="MEAS:CURR?")
    {   
      int16_t Messwert_A3 = ads.readADC_SingleEnded(3);     // Auslesen von Eingang A3 des ADS1115 (16 Bit)
      float Spannung_A3 = Messwert_A3*0.1875e-3;            // Umrechnen in Spannung am Eingang A3 des ADS1115
      float Strom_DMM = Spannung_A3;                        // Umrechnen in Strom durch Shunt
  
      Serial.println(Strom_DMM,5);                          // DMM-Strom an PC senden (mit 5 Nachkommastellen)
    }        
    else if(Befehl.substring(0,5)=="FREQ ")
    {
      FGEN_Frequenz = Befehl.substring(5).toFloat();
    }
    else if(Befehl.substring(0,5) == "VOLT ")
    {
      FGEN_Amplitude = Befehl.substring(5).toFloat();
    }
    else if(Befehl.substring(0,5) == "FUNC ")
    {
      FGEN_Waveform = Befehl.substring(5);
    }
    else if(Befehl.substring(0,10) == "VOLT:OFFS ")
    {
      FGEN_Offset = Befehl.substring(10).toFloat();
    }
    else if(Befehl.substring(0,5) == "OUTP ")
    {
      if (Befehl.substring(5) == "ON")
      {
        FGEN_On = true;
      }
      else if (Befehl.substring(5) == "OFF")
      {
        int Counts_DAC = (0.0+10)/20*4095;
        dac.setVoltage(Counts_DAC, false);        // DAC-Wert (Counts) setzen
        FGEN_On = false;
      }
    }
    else if (Befehl == "WAV:DATA?")
    {
      DSO_Messwertzaehler = 0;
      Timer1.setPeriod(DSO_Abtastzeit*1e6);
      Timer1.attachInterrupt(readDSO);               // Funktion readDSO() mit Timer ausführen

      DSO_On = true;
    }
    else if (Befehl.substring(0,9) == "WAV:POIN ")
    {
      if (Befehl.substring(9).toInt() < DSO_MaxAnzahlMesswerte)
      {
        DSO_AnzahlMesswerte = Befehl.substring(9).toInt();
      }
    }
    else if (Befehl.substring(0,9) == "TIM:SCAL ")
    {
      DSO_Abtastzeit = Befehl.substring(9).toFloat()*10/DSO_AnzahlMesswerte;
    }
    else if (Befehl == "TIM:SCAL?")
    {
      Serial.println(DSO_Abtastzeit*float(DSO_AnzahlMesswerte)/10);
    }
  }
  else if (DSO_Fertig)
  {
    Serial.print(DSO_Messwerte1[0]);                             // Messwerte an PC senden
      for (int i = 1; i < DSO_AnzahlMesswerte; i++)
      {
        Serial.print(",");
        Serial.print(DSO_Messwerte1[i]);                         // Messwerte an PC senden
      }
      Serial.print(",");
      Serial.print(DSO_Messwerte2[0]);                             // Messwerte an PC senden
      for (int i = 1; i < DSO_AnzahlMesswerte; i++)
      {
        Serial.print(",");
        Serial.print(DSO_Messwerte2[i]);                         // Messwerte an PC senden
      }
      Serial.println("");

      DSO_Fertig = false;
  }

  if(FGEN_On)
  {
    if(FGEN_Waveform == "SIN")
    {
      float Spannung_DAC = 0.5*FGEN_Amplitude*sin(2*3.14*FGEN_Frequenz*micros()*1e-6) - FGEN_Offset;
      int Counts_DAC = (Spannung_DAC+10)/20*4095;
      dac.setVoltage(Counts_DAC, false);            // DAC-Wert (Counts) setzen
    }
    else if(FGEN_Waveform == "SQU")
    {
      float Spannung_DAC = sin(2*3.14*FGEN_Frequenz*micros()*1e-6);
      Spannung_DAC = 0.5*FGEN_Amplitude*Spannung_DAC/abs(Spannung_DAC) - FGEN_Offset;
      int Counts_DAC = (Spannung_DAC+10)/20*4095;
      dac.setVoltage(Counts_DAC, false);            // DAC-Wert (Counts) setzen
    }  
  }
}
