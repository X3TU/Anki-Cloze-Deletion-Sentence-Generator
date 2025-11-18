# AI-Powered Anki Cloze Deletion Card Generator 🚀

This tool automates the creation of **Cloze Deletion English vocabulary flashcards** using **Google Gemini 2.0 Flash** and **AnkiConnect**. It generates context-rich sentences with cloze deletions and hints, checking for duplicates to maintain a clean database.

## ✨ Features
- **Batch Processing:** Reads vocabulary from a text file.
- **Smart Context:** Generates C1-level sentences tailored for Data Science/Academic context.
- **Duplicate Prevention:** Uses tagging (`vocab:word_name`) to prevent duplicate entries.
- **Hint Injection:** Automatically adds definitions as hints in Anki cards.
- **Rate Limit Safe:** Optimized to work within Gemini API free tier limits.
- **Customizable Prompt:** The default prompt is engineered for **C1-level academic English**. You can easily modify the `prompt` variable in `anki_batch_bot.py` to target different proficiency levels (e.g., B2, TOEFL) or languages.



## 🛠️ Setup
1. **Prerequisites:**
   - Python 3.8+
   - Anki Desktop App + [AnkiConnect Add-on](https://ankiweb.net/shared/info/2055492159)

2. **Installation:**
   ```bash
   git clone https://github.com/X3TU/Anki-Cloze-Deletion-Sentence-Generator.git
   cd Anki-Cloze-Deletion-Sentence-Generator
   pip install -r requirements.txt

3. **Change .env.example to .env**
   
