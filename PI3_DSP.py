import re
import time
import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, freqz
from scipy.fft import fft, fftfreq

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    y = filtfilt(b, a, data)  # Usando filtfilt para evitar deslocamento de fase
    return y, b, a

def process_samples(signal, fs):

    chosen_channel = 0

    # Normaliza o sinal para que os valores variem de -1 a 1
    signal_min = np.min(signal)
    signal_max = np.max(signal)

    if signal_max - signal_min != 0:
        normalized_signal = 2 * (signal - signal_min) / (signal_max - signal_min) - 1
    else:
        print("Todos os valores do sinal são iguais. A normalização não é possível.")
        return None

    # Aplicação dos filtros passa-faixa
    filtered_15Hz, b15, a15 = bandpass_filter(normalized_signal, 12, 18, fs, order=5)
    filtered_70Hz, b70, a70 = bandpass_filter(normalized_signal, 67, 83, fs, order=5)

    # Cálculo da potência dos sinais filtrados
    power_15Hz = np.mean(filtered_15Hz**2)
    power_70Hz = np.mean(filtered_70Hz**2)

    # Determinação da ocupação dos canais (limiar de ocupação arbitrário)
    threshold_occupancy = 0.1
    is_15Hz_occupied = power_15Hz > threshold_occupancy
    is_70Hz_occupied = power_70Hz > threshold_occupancy

    # Escolha do canal de transmissão
    if is_15Hz_occupied:
        if is_70Hz_occupied:
            chosen_channel = 3 # Caso: Ambos Ocupados
        else:
            chosen_channel = 1 # Caso: 15Hz Ocupado
    elif is_70Hz_occupied:
        chosen_channel = 2 # Caso: 70Hz Ocupado

    # Resultados
    print("-------------------------RESULTADO-------------------------")
    print(f"Potência no canal 15 Hz: {power_15Hz:.4f}")
    print(f"Potência no canal 70 Hz: {power_70Hz:.4f}")
    print(f"Canal 15 Hz ocupado: {is_15Hz_occupied}")
    print(f"Canal 70 Hz ocupado: {is_70Hz_occupied}")
    print(f"Modo de transmissão: {chosen_channel}")

    # Wait to assure that Arduino returned to the listening function
    print("Waiting a bit...") 
    time.sleep(2)

    return {
        'normalized_signal': normalized_signal,
        'filtered_15Hz': filtered_15Hz,
        'filtered_70Hz': filtered_70Hz,
        'power_15Hz': power_15Hz,
        'power_70Hz': power_70Hz,
        'chosen_channel': chosen_channel,
        'b15': b15,
        'a15': a15,
        'b70': b70,
        'a70': a70
    }

def plot_results(t, processed_data, fs):
    normalized_signal = processed_data['normalized_signal']
    filtered_15Hz = processed_data['filtered_15Hz']
    filtered_70Hz = processed_data['filtered_70Hz']

    # Espectro do sinal combinado
    N = len(normalized_signal)
    yf = fft(normalized_signal)
    xf = fftfreq(N, 1 / fs)

    # Plot dos sinais
    plt.figure(figsize=(12, 10))

    plt.subplot(4, 1, 1)
    plt.plot(t, normalized_signal)
    plt.title('Sinal Combinado (15 Hz + 70 Hz)')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Amplitude Normalizada (-1 a 1)')
    plt.grid(True)

    plt.subplot(4, 1, 2)
    plt.plot(t, filtered_15Hz, 'g')
    plt.title('Sinal Filtrado no Canal 15 Hz')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)

    plt.subplot(4, 1, 3)
    plt.plot(t, filtered_70Hz, 'r')
    plt.title('Sinal Filtrado no Canal 70 Hz')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)

    plt.subplot(4, 1, 4)
    plt.plot(xf[:N // 2], 2.0 / N * np.abs(yf[:N // 2]))
    plt.title('Espectro do Sinal Combinado')
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Amplitude')
    plt.grid(True)

    plt.tight_layout()
    plt.show(block=False) # Exibe o gráfico

    plt.pause(2.5)
    plt.close()

def main():

    # Definição dos comandos da Serial
    ch_a = "SETMODEenergia\n".encode('ascii')
    ch_b = "SETMODEtaxa\n".encode('ascii')
    ch_c = "SETMODEalcance\n".encode('ascii')
    command_0 = "SETCH120\n".encode('ascii')
    command_1 = "SETCH002\n".encode('ascii')
    command_2 = "SETCH054\n".encode('ascii')
    command_3 = "SETCH076\n".encode('ascii')

    # Recolhe a escolha do usuário sobre o modo de operação
    modo = input("Escolha o modo de trasmissão:\n(a) Economia de energia | (b) Maior taxa de comunicação | (c) Maior alcance\nSua escolha: ")

    # Configurações da Serial
    SERIAL_PORT = '/dev/ttyACM0'
    BAUD_RATE = 115200
    TIMEOUT = 1

    # Configurações de Amostragem
    SAMPLE_PERIOD_SIGNAL = 0.001  # Período de amostragem em segundos
    DURATION_SIGNAL = 1           # Duração da coleta de dados em segundos

    # Parâmetros do projeto
    fs = int(1 / SAMPLE_PERIOD_SIGNAL)  # Frequência de amostragem
    num_samples = int(DURATION_SIGNAL / SAMPLE_PERIOD_SIGNAL)
    
    print(f"Frequência de amostragem (fs): {fs} Hz")
    print(f"Número de amostras por coleta: {num_samples}")

    # Vetor de tempo ajustado para DURATION_SIGNAL
    t = np.arange(0, DURATION_SIGNAL, 1/fs)

    # Tag para identificar as linhas de amostra
    SIGNAL_TAG = "(SignalType)"

    # Compila uma expressão regular para extrair o valor após a tag
    signal_pattern = re.compile(rf"^{re.escape(SIGNAL_TAG)}([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)$")

    # Inicializa a conexão serial
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT, write_timeout=2)
        print(f"Conectado à porta {SERIAL_PORT} a {BAUD_RATE} bps.")
    except serial.SerialException as e:
        print(f"Erro ao conectar à porta serial: {e}")
        return

    # Aguarda a conexão serial estabilizar
    time.sleep(2)
    
    if modo == 'a':
        print("Modo de operação definido como: Economia de energia")
        bytes_written = ser.write(ch_a)
        print(f"Enviado ch_a: {ch_a} ({bytes_written} bytes enviados)")
    elif modo == 'b':
        print("Modo de operação definido como: Maior taxa de comunicação")
        bytes_written = ser.write(ch_b)
        print(f"Enviado ch_b: {ch_b} ({bytes_written} bytes enviados)")
    elif modo == 'c':
        print("Modo de operação definido como: Maior alcance")
        bytes_written = ser.write(ch_c)
        print(f"Enviado ch_c: {ch_c} ({bytes_written} bytes enviados)")
    else:
        print("Nenhuma das opções (a, b ou c) foram escolhidas, mantendo configuração padrão.")

    try:
        while True:

            print("\nIniciando nova coleta de dados...")

            samples = []
            received_samples = 0
            invalid_lines = 0

            start_time = time.time()
            while received_samples < num_samples:
                try:
                    # Lê uma linha da serial com tratamento de erros
                    raw_line = ser.readline()
                    if not raw_line:
                        continue  # Timeout ou linha vazia

                    try:
                        # Tenta decodificar ignorando bytes inválidos
                        line = raw_line.decode('utf-8', errors='ignore').strip()
                    except UnicodeDecodeError:
                        # Incrementa contador e pula para a próxima iteração
                        invalid_lines += 1
                        continue

                    if not line:
                        continue  # Linha vazia, tenta novamente

                    # Tenta corresponder a linha com o padrão de sinal
                    match = signal_pattern.match(line)
                    if match:
                        # Extrai o valor da amostra
                        sample_str = match.group(1)
                        try:
                            sample = float(sample_str)
                            samples.append(sample)
                            received_samples += 1

                            # Opcional: exibir progresso a cada 100 amostras
                            if received_samples % 100 == 0 or received_samples == num_samples:
                                print(f"{received_samples}/{num_samples} amostras coletadas...")
                        except ValueError:
                            # Valor não pôde ser convertido para float
                            invalid_lines += 1
                            print(f"Valor inválido na linha: {line}")
                    else:
                        # Linha não corresponde ao padrão de sinal, ignora
                        invalid_lines += 1
                except serial.SerialException as e:
                    print(f"Erro na leitura da serial: {e}")
                    break

            end_time = time.time()
            elapsed_time = end_time - start_time

            print(f"Coleta concluída em {elapsed_time:.2f} segundos.")
            print(f"Total de amostras recebidas: {received_samples}")
            print(f"Total de linhas inválidas ignoradas: {invalid_lines}")

            # Verifica se coletou amostras suficientes
            if not samples:
                print("Nenhuma amostra válida foi coletada. Tentando novamente...")
                continue

            # Converte as amostras para um array NumPy
            signal = np.array(samples)

            # Processa as amostras
            processed_data = process_samples(signal, fs)
            if processed_data is None:
                print("Não foi possível processar pois não existe sinal, logo ambos os canais estão livres")

                print("-------------------Canal definido para 120-------------------")
                bytes_written = ser.write(command_0)
                print(f"Enviado command_0: {command_0} ({bytes_written} bytes enviados)")
                continue

            # Plot dos sinais e espectro
            plot_results(t, processed_data, fs)

            #Envia o canal que deve ser usado via Serial
            channel = processed_data['chosen_channel']

            if channel == 0:
                print("-------------------Canal definido para 120-------------------")
                bytes_written = ser.write(command_0)
                print(f"Enviado command_0: {command_0} ({bytes_written} bytes enviados)")
            
            elif channel == 1:
                print("-------------------Canal definido para 02-------------------")
                bytes_written = ser.write(command_1)
                print(f"Enviado command_1: {command_1} ({bytes_written} bytes enviados)")
            
            elif channel == 2:
                print("-------------------Canal definido para 54-------------------")
                bytes_written = ser.write(command_2)
                print(f"Enviado command_2: {command_2} ({bytes_written} bytes enviados)")
            
            elif channel == 3:
                print("-------------------Canal definido para 76-------------------")
                bytes_written = ser.write(command_3)
                print(f"Enviado command_3: {command_3} ({bytes_written} bytes enviados)")

            # See the arduino response on what it received:
            response = ser.readline().decode('ascii').strip()
            print(f"Resposta do Arduino: {response}")

            # Pequena pausa antes da próxima coleta
            print("Aguardando próxima coleta...")
            time.sleep(2)  # Ajuste conforme necessário

    except KeyboardInterrupt:
        print("\nInterrupção pelo usuário. Encerrando o programa...")

    finally:
        # Fecha a conexão serial ao encerrar o programa
        ser.close()
        print("Conexão serial fechada.")

if __name__ == "__main__":

    main()