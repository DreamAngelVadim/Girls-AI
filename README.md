# 🎀 Girls-AI — Голосовой помощник с двумя персонажами

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![GitHub last commit](https://img.shields.io/github/last-commit/DreamAngelVadim/Girls-AI)

</div>

**Голосовой помощник с двумя девушками** — **Чу Чу** (18 лет, косплей-модель) и **Мэй** (22 года, крафтерша). Ассистент распознаёт голос, отвечает через нейросеть Qwen 2.5-7B (локально, без интернета), поддерживает фоновые диалоги между персонажами и автоматическое исправление опечаток.

---

## ✨ Возможности

| Возможность | Описание |
|-------------|----------|
| 🎤 Голосовое управление | Говорит и слушает через микрофон |
| 🧠 Локальный ИИ | Qwen 2.5-7B работает на вашем ПК, не требуя интернета |
| 👩‍🦰 Два персонажа | Чу Чу и Мэй отвечают каждая своим голосом (Silero TTS) |
| 💬 Фоновые диалоги | Персонажи разговаривают между собой в тишине |
| 🎭 Хоровые ответы | Иногда отвечают вместе (15% вероятность) |
| 🔇 Автоотключение микрофона | Во время фоновых диалогов микрофон не слушает |
| ✏️ Исправление опечаток | Через `autocorrect` и словарь замен |
| 🧹 Очистка текста | Удаление эмодзи и специальных символов |

---

## 🚀 Быстрая установка

<div align="center">

| Шаг | Команда |
|:---:|:---|
| **1** | `git clone https://github.com/DreamAngelVadim/Girls-AI.git && cd Girls-AI` |
| **2** | `python -m venv Girls-AI` |
| **3** | `source Girls-AI/bin/activate` — Linux/Mac<br>`.\Girls-AI\Scripts\activate` — Windows |
| **4** | `pip install -r requirements.txt` |
| **5** | Скачайте [Ollama](https://ollama.com) |
| **6** | `ollama run hf.co/RefalMachine/ruadapt_qwen2.5_7B_ext_u48_instruct_gguf:Q4_K_M` |
| **7** | `python main.py` |

</div>

🎮 Команды
Что сказать	Реакция
Чу Чу, привет	Чу Чу отвечает
Мэй, как дела?	Мэй отвечает
Девочки, помогите	Отвечают вместе (или хором)
хором	Чу Чу и Мэй говорят вместе
диалог	Короткий диалог между сёстрами
пока	Выход из программы

## 🛠️ Технологии

| Компонент | Технология |
|-----------|-----------|
| TTS (синтез речи) | Silero TTS v5_ru |
| LLM (генерация ответов) | Qwen 2.5-7B (GGUF) через Ollama |
| STT (распознавание речи) | Google Speech Recognition |
| Шумоподавление | DeepFilterNet / noisereduce |
| Автокоррекция | autocorrect |
| Очистка текста | emoji, regex |

📝 Лицензия
MIT License — свободное использование, модификация и распространение.

## 🙏 Благодарности

<div align="center">

| | |
|:---:|:---:|
| [![Silero](https://img.shields.io/badge/Silero-TTS-181717?style=for-the-badge&logo=github)](https://github.com/snakers4/silero-models) | [![Qwen](https://img.shields.io/badge/Qwen-LLM-181717?style=for-the-badge&logo=github)](https://github.com/QwenLM/Qwen) |
| За голосовые модели | За языковую модель |

| | |
|:---:|:---:|
| [![Ollama](https://img.shields.io/badge/Ollama-LLM-181717?style=for-the-badge&logo=ollama)](https://ollama.com) | [![SpeechRecognition](https://img.shields.io/badge/SpeechRecognition-STT-181717?style=for-the-badge&logo=github)](https://github.com/Uberi/speech_recognition) |
| За простоту запуска LLM | За распознавание речи |

</div>

## 🤝 Контакты

<div align="center">

| Платформа | Ссылка |
|:---:|:---|
| 🐙 **GitHub** | [DreamAngelVadim](https://github.com/DreamAngelVadim) |
| 🎀 **Проект** | [Girls-AI](https://github.com/DreamAngelVadim/Girls-AI) |

</div>

---

<div align="center">
  <sub>💬 Предложения и пожелания приветствуются в Issues! 💬</sub>
</div>
