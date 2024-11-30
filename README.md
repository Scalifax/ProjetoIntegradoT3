# Projeto Integrado – Terceiro Trimestre 2024

## Apresentação do Projeto

O **Projeto Integrado T3** foi desenvolvido com o objetivo de explorar técnicas de *compartilhamento espectral*, essenciais para otimizar o uso do espectro radioelétrico, maximizando a eficiência e reduzindo interferências entre usuários. Essa abordagem torna-se ainda mais relevante no contexto do **6G**, onde a alta densidade de dispositivos conectados e os serviços com baixa latência exigem soluções avançadas de gestão de espectro.

## O Desafio do Compartilhamento Espectral

O espectro é um recurso limitado e altamente demandado. Para atender às necessidades crescentes, utilizamos **radios cognitivos**, dispositivos capazes de:

- Detectar o ambiente de espectro ao redor.
- Ajustar automaticamente suas frequências de operação.
- Minimizar interferências com outros usuários.

Uma das funções centrais do rádio cognitivo é o **sensoriamento espectral**, que detecta faixas livres para uso temporário, garantindo comunicação eficiente e sem interferências.

## O Centro de Fusão

No projeto, implementamos um **Centro de Fusão**, responsável por:

1. Monitorar dois canais distintos (15 Hz e 70 Hz).
2. Combinar os canais através de um circuito somador.
3. Digitalizar os sinais combinados com intervalo de amostragem adequado.
4. Analisar graficamente o sinal somado e os sinais individuais.
5. Decidir, com base em técnicas de processamento digital de sinais (DSP), quais canais estão ocupados.
6. Selecionar o canal de transmissão mais adequado ao cenário escolhido.
7. Transmitir dados pelo canal selecionado.

## Cenários de Operação

O sistema foi projetado para operar em diferentes cenários:

- **Economia de energia**: Maximiza a eficiência energética.
- **Maior taxa de comunicação**: Otimiza o fluxo de dados.
- **Maior alcance**: Garante comunicações em distâncias maiores.

## O que foi utilizado

Para o desenvovimento, foi utilizado um Arduino mega, que controla o funcionamento de um rádio nRF24L01 e realiza a amostragem dos canais. Para a DSP, foi utilizado um código em python executado em um computador, que está ligado a fisicamente ao Arduino.
O **Projeto Integrado T3** representa um passo significativo no desenvolvimento de soluções inteligentes e eficientes para a gestão de espectro, alinhando-se às demandas tecnológicas do futuro das telecomunicações.

