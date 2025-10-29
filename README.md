# 🕵️‍♂️ Kafka Fraud Detector

Sistema de **detecção de fraudes em transações financeiras em tempo real**, utilizando **Apache Kafka**, **Python** e **MySQL**.  
Desenvolvido para simular o fluxo de dados de um ambiente de streaming: o **Producer** envia transações aleatórias, o **Consumer** consome e aplica regras de detecção de fraude, registrando alertas automaticamente no banco.

---

## 🚀 Tecnologias Utilizadas

| Componente | Função | Tecnologia |
|-------------|--------|-------------|
| **Mensageria** | Stream de dados em tempo real | Apache Kafka (com Zookeeper) |
| **Broker de Mensagens** | Comunicação entre Producer e Consumer | `bitnami/kafka:3.6` |
| **Coordenação** | Gerenciamento de cluster Kafka | `bitnami/zookeeper:3.9` |
| **Banco de Dados** | Persistência de transações e alertas | MySQL 8 |
| **Aplicação** | Produção e consumo de mensagens | Python 3.12 |
| **Interface DB** | Visualização via navegador | Adminer |
| **Orquestração** | Contêineres Docker | Docker Compose |

---

## ⚙️ Pré-requisitos

Antes de iniciar, instale:

| Programa | Versão mínima | Verificação |
|-----------|----------------|--------------|
| **Docker** | 24.x | `docker --version` |
| **Docker Compose Plugin** | 2.20+ | `docker compose version` |
| **Python** | 3.12+ | `python3 --version` |
| **Pip** | 24+ | `pip --version` |
| **Git** | 2.30+ | `git --version` |

---

## 🧱 Configuração do Ambiente

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/seuusuario/kafka-fraud-detector.git
cd kafka-fraud-detector
