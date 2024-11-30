#include <SPI.h>

// Definições de pinos
#define CE  9     // Pino CE do NRF
#define CSN 53     // Pino CSN do NRF

// Registradores do NRF24
#define _NRF24_CONFIG      0x00
#define _NRF24_EN_AA       0x01
#define _NRF24_RF_CH       0x05
#define _NRF24_RF_SETUP    0x06
#define _NRF24_STATUS      0x07
#define _NRF24_TX_ADDR     0x10
#define _NRF24_RX_ADDR_P0  0x0A
#define _NRF24_RX_PW_P0    0x11

// Definições de parâmetros para as amostras:
#define NUM_OF_SAMPLES 1000
#define SAMPLE_PERIOD 1000 // em [us]

// Variável para controlar alguns delay's utilizados para fins de debug
bool debug = false;
bool mode_set = false;

// Array para guardar todas as amostras medidas:
int analog_samples[NUM_OF_SAMPLES];

// Variáveis para habilitar as tarefas:
bool enable_task1 = true;
bool enable_task2 = false;

// Variável para armazenar o tempo em [ms]
unsigned long loop_time = 0;

// Variáveis para a lógica de timeout da task 2:
unsigned long last_timeout = 0;
int task1_delay = 0, timeout_interval = 25000; // Mude esse valor para aumentar o tempo de espera

// Função para ler um registrador
byte getRegister(byte r)
{
  byte c;
  digitalWrite(CSN, LOW);
  SPI.transfer(r & 0x1F);
  c = SPI.transfer(0xFF);
  digitalWrite(CSN, HIGH);
  return c;
}

// Função para escrever em um registrador
void setRegister(byte r, byte v)
{
  digitalWrite(CSN, LOW);
  SPI.transfer((r & 0x1F) | 0x20); // Comando de escrita
  SPI.transfer(v);
  digitalWrite(CSN, HIGH);
}

// Função para ligar o nRF24L01
void powerUp(void)
{
  byte config = getRegister(_NRF24_CONFIG);
  config |= 0x02; // Setar bit PWR_UP
  setRegister(_NRF24_CONFIG, config);
  delayMicroseconds(130);
}

// Função para desligar o nRF24L01
void powerDown(void)
{
  byte config = getRegister(_NRF24_CONFIG);
  config &= ~0x02; // Clear bit PWR_UP
  setRegister(_NRF24_CONFIG, config);
}

// Função para habilitar o modo transmissor (PTX)
void enableTX()
{
  // Configurar como PTX
  byte config = getRegister(_NRF24_CONFIG);
  config &= ~0x01; // Clear bit PRIM_RX para PTX
  setRegister(_NRF24_CONFIG, config);
  
  digitalWrite(CE, LOW); // Inicialmente LOW
}

// Função para desabilitar o modo transmissor
void disableTX()
{
  digitalWrite(CE, LOW);
}

// Função para definir o canal de transmissão
void setChannel(byte channel)
{
  if(channel > 125){
    channel = 125; // nRF24L01 suporta canais de 0 a 125
  }
  setRegister(_NRF24_RF_CH, channel);
  
  Serial.print("Canal definido para: ");
  Serial.println(channel);

  if(debug){
    delay(1000);
  }
}

void setMode(String mode = ""){
  
  if(mode == "energia"){
    Serial.println("Modo de transmissão: economia de energia");
    setRegister(_NRF24_RF_SETUP, 0x01);
  }
  else if(mode == "alcance"){
    Serial.println("Modo de transmissão: maior alcance");
    setRegister(_NRF24_RF_SETUP, 0x07);
  }
  else if(mode == "taxa"){
    Serial.println("Modo de transmissão: maior taxa");
    setRegister(_NRF24_RF_SETUP, 0x0D);
  }
  else{
    Serial.println("Modo de transmissão: padrão");
    setRegister(_NRF24_RF_SETUP, 0x0F);
  }

  if(debug){
    delay(1000);
  }
}

// Função para enviar dados
void sendData(const byte* data, byte length)
{
  digitalWrite(CSN, LOW);
  SPI.transfer(0xA0); // Comando W_TX_PAYLOAD
  for(byte i = 0; i < length; i++){
    SPI.transfer(data[i]);
  }
  digitalWrite(CSN, HIGH);
  
  // Pulsar CE para iniciar a transmissão
  digitalWrite(CE, HIGH);
  delayMicroseconds(15);
  digitalWrite(CE, LOW);
  
  // Aguardar até a transmissão ser concluída com timeout
  unsigned long startTime = millis();
  while(!(getRegister(_NRF24_STATUS) & 0x20)){
    if (millis() - startTime > 1000) { // Timeout de 1 segundo
      Serial.println("Erro: Timeout na transmissão");
      break;
    }
  }
  
  // Limpar os bits de status
  byte status = getRegister(_NRF24_STATUS);
  setRegister(_NRF24_STATUS, status | 0x20); // Limpar TX_DS
  setRegister(_NRF24_STATUS, 0x70); // Limpar outros bits de status
}

void setup()
{
  Serial.begin(115200);
  Serial.println("Iniciando Transmissor nRF24L01 ...");
  
  // Inicializa SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV2);
  SPI.setBitOrder(MSBFIRST);
  
  // Configura pinos
  pinMode(CE, OUTPUT);
  pinMode(CSN, OUTPUT);
  digitalWrite(CE, LOW);
  digitalWrite(CSN, HIGH);
  
  // Configura nRF24L01
  powerUp();
  
  // Desativa Auto Acknowledgment
  setRegister(_NRF24_EN_AA, 0x00);
  
  // Configura RF Setup: potência e data rate padrões
  setMode();
    
  // Configura endereço de transmissão (usando 5 bytes padrão)
  byte txAddr[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};
  digitalWrite(CSN, LOW);
  SPI.transfer(0x20 | _NRF24_TX_ADDR);
  for(byte i = 0; i < 5; i++) {
    SPI.transfer(txAddr[i]);
  }
  digitalWrite(CSN, HIGH);
  
  // Configura endereço de recepção para PIPE0 (necessário mesmo em PTX)
  byte rxAddr[5] = {0xD7, 0xD7, 0xD7, 0xD7, 0xD7};
  digitalWrite(CSN, LOW);
  SPI.transfer(0x20 | _NRF24_RX_ADDR_P0);
  for(byte i = 0; i < 5; i++) {
    SPI.transfer(rxAddr[i]);
  }
  digitalWrite(CSN, HIGH);
  
  // Define o tamanho do payload para o pipe 0
  setRegister(_NRF24_RX_PW_P0, 5); // 5 bytes para "Hello"
  
  // Limpa as filas de TX e RX
  digitalWrite(CSN, LOW);
  SPI.transfer(0xE1); // Comando FLUSH_TX
  digitalWrite(CSN, HIGH);
  
  digitalWrite(CSN, LOW);
  SPI.transfer(0xE2); // Comando FLUSH_RX
  digitalWrite(CSN, HIGH);
  
  enableTX();
  
  Serial.println("Transmissor configurado.");

  pinMode(13,OUTPUT);
  digitalWrite(13,0);
}

void loop() {
  loop_time = millis();

  // Processa comandos seriais com prioridade
  while (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    Serial.print("Comando recebido: ");
    Serial.println(input);

    if (input.startsWith("SETMODE")) {
      String mode = input.substring(7);
      setMode(mode);
      Serial.print("MODE_DEF: ");
      Serial.println(mode);
      mode_set = true;
      return;
    }

    if (mode_set) {
      if (input.startsWith("SETCH")) {
        String ch_str = input.substring(5, 9);
        int ch = ch_str.toInt();
        digitalWrite(13, HIGH);
        setChannel((byte)ch);
      } else if (input.startsWith("DEBUG")) {
        debug = !debug;
        Serial.print("debug definido para: ");
        Serial.println(debug);
        delay(500);
        Serial.print("DEBUG_TOGGLE: ");
        Serial.println(debug);
      }
    } else {
      Serial.println("Erro: Modo não definido. Use SET_MODE primeiro.");
    }
  }

  // Executa tarefas normais apenas se o modo estiver definido
  if (mode_set) {
    if (enable_task1) {
      for(int i = 0; i < NUM_OF_SAMPLES; i++) {
        analog_samples[i] = analogRead(A8);
        delayMicroseconds(SAMPLE_PERIOD);
      }
      for(int i = 0; i < NUM_OF_SAMPLES; i++) {
        Serial.print("(SignalType)");
        Serial.println(analog_samples[i]);
      }
      enable_task1 = false;
      enable_task2 = true;
      task1_delay = millis() - loop_time;
    }

    if (enable_task2) {
      if (loop_time - last_timeout > timeout_interval + task1_delay) {
        last_timeout = loop_time;
        enable_task1 = true;
        enable_task2 = false;
      }

      String msg = "Hello";
      byte data[msg.length() + 1];
      msg.getBytes(data, sizeof(data));
      sendData(data, msg.length());
      Serial.println("Mensagem transmitida!");
      delay(1);
    }
  } else {
    delay(100); // Aguardando definição do modo
  }
}
