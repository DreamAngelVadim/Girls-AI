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
| 🔐 Голосовая идентификация | Узнаёт владельца по голосу при запуске |
| 🔞 Автоматическое переключение режимов | Меняет NSFW/SFW в зависимости от говорящего |
| ✏️ Исправление опечаток | Через `autocorrect` и словарь замен |
| 🧹 Очистка текста | Удаление эмодзи и специальных символов |

---

## 🚀 Быстрая установка

<div align="center">

| Шаг | Действие | Команда / Ссылка |
|:---:|:---|:---|
| **1️⃣** | **Клонирование** | `git clone https://github.com/DreamAngelVadim/Girls-AI.git && cd Girls-AI` |
| **2️⃣** | **Виртуальное окружение** | `python -m venv Girls-AI` |
| **3️⃣** | **Активация (Linux/Mac)** | `source Girls-AI/bin/activate` |
| **3️⃣** | **Активация (Windows)** | `.\Girls-AI\Scripts\activate` |
| **4️⃣** | **Зависимости** | `pip install -r requirements.txt` |
| **5️⃣** | **Ollama** | Скачайте с [ollama.com](https://ollama.com) |
| **6️⃣** | **Модель Qwen** | `ollama run hf.co/RefalMachine/ruadapt_qwen2.5_7B_ext_u48_instruct_gguf:Q4_K_M` |
| **7️⃣** | **Запуск** | `python main.py` |

</div>

---

<div align="center">
  <sub>✨ После выполнения всех шагов ассистент готов к работе! ✨</sub>
</div>

---

## 🎮 Команды

<div align="center">

| Команда | Реакция |
|:---|:---|
| `Чу Чу, привет` | Чу Чу отвечает |
| `Мэй, как дела?` | Мэй отвечает |
| `Девочки, помогите` | Отвечают вместе (или хором) |
| `хором` | Чу Чу и Мэй говорят вместе |
| `диалог` | Короткий диалог между сёстрами |
| `спать` | Отправить девушек спать |
| `просыпайтесь` | Разбудить девушек |
| `взрослый режим` | Включить взрослый режим (NSFW) |
| `обычный режим` | Выключить взрослый режим (SFW) |
| `пока` | Выход из программы |

</div>

---

## 🔐 Голосовая идентификация

При первом запуске ассистент запомнит ваш голос и имя:

1. **Первый запуск** — запись образца голоса и имени владельца
2. **Последующие запуски** — автоматическое распознавание владельца по голосу
3. **Гостевой режим** — если голос не распознан, включится SFW режим
4. **Автоматическое переключение** — режим меняется в зависимости от говорящего

---

## 🛠️ Технологии

<div align="center">

| Компонент | Технология |
|:---|:---|
| 🗣️ TTS (синтез речи) | Silero TTS v5_ru |
| 🧠 LLM (генерация ответов) | Qwen 2.5-7B (GGUF) через Ollama |
| 🎙️ STT (распознавание речи) | Google Speech Recognition |
| 🔇 Шумоподавление | DeepFilterNet / noisereduce |
| 🔐 Голосовая идентификация | Спектральный анализ через scipy |
| ✏️ Автокоррекция | autocorrect |
| 🧹 Очистка текста | emoji, regex |

</div>

---

## 📝 Лицензия

<div align="center">

**MIT License** — свободное использование, модификация и распространение.

</div>

---

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

---

## 🤝 Контакты

<div align="center">

| Платформа | Ссылка |
|:---:|:---|
| 🐙 **GitHub** | [DreamAngelVadim](https://github.com/DreamAngelVadim) |
| 🎀 **Проект** | [Girls-AI](https://github.com/DreamAngelVadim/Girls-AI) |
| 💬 **Discord** | [DreamAngelVadim](https://discord.com/users/418392722806669322) |

</div>

<div align="center">
  <sub>💬 Предложения и пожелания приветствуются в Issues! 💬</sub>
</div>

---

<div align="center">

### ⭐ Поставьте звезду проекту, если он вам понравился! ⭐

</div>

---

<div align="center">

> 💡 *Чу Чу и Мэй всегда рядом — скажи им «привет», и они ответят!* 🎀

</div>
