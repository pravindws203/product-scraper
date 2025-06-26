# 🛒 E-Commerce Product Scraping Bots

This repository contains scalable and modular Python bots to scrape product data and customer reviews from major Indian e-commerce platforms including:

- Amazon  
- Flipkart  
- Zepto  
- JioMart

These bots are designed to automate the extraction of structured product information and reviews for use in price comparison, catalog enrichment, sentiment analysis, and competitive market research.

---

## 🚀 Features

- ✅ Platform-specific scrapers with clean and extensible structure  
- ✅ Headless browsing with Selenium for dynamic content  
- ✅ CAPTCHA bypass support via `selenium-wire` and `cloudscraper`  
- ✅ Data export to CSV / JSON / MySQL  
- ✅ Built-in logging, retry handling, and progress tracking with `tqdm`

---

## 📦 Requirements

Install the required dependencies using:

```bash
pip install -r requirements.txt

















# ==============================================================================
# 📦 PACCHETTO COMPLETO BOT CRIPTOVALUTA.IT
# Versione: 1.0 - Pronto per deploy immediato
# ==============================================================================

# 📁 STRUTTURA PROGETTO (Crea questa struttura):
# criptovaluta-bot/
# ├── crypto_bot.py                    # Bot principale
# ├── config.py                            # Configurazione
# ├── requirements.txt              # Dipendenze
# ├── install.sh                          # Installazione automatica
# ├── deploy.sh                            # Deploy produzione
# ├── monitor.sh                          # Monitoraggio
# ├── test_config.py                  # Test configurazione
# ├── start.sh                              # Avvio rapido
# └── README.md                            # Documentazione

mkdir -p criptovaluta-bot
cd criptovaluta-bot

# ==============================================================================
# 📄 FILE 1: README.md
# ==============================================================================
cat > README.md << 'EOF'
# 🚀 Bot Telegram Criptovaluta.it - News Finanziarie

Bot ultra-reattivo per breaking news crypto finanziarie e macroeconomiche.
**Pubblica automaticamente solo le 5-8 news più rilevanti al giorno** su @criptovalutait.

## ⚡ Quick Start (5 minuti)

```bash
# 1. Download e setup
git clone <repository> && cd criptovaluta-bot
chmod +x *.sh

# 2. Installazione automatica
./install.sh

# 3. Configurazione bot
nano config.py    # Inserisci BOT_TOKEN e IDs canali

# 4. Test configurazione
python test_config.py

# 5. Avvio bot
./start.sh
```

## 🎯 Caratteristiche Principali

- ✅ **Solo news finanziarie**: SEC, Fed, ETF, aziende Fortune 500, dati macro
- ✅ **Ultra-veloce**: Breaking score >90 pubblicati in 1-3 minuti
- ✅ **Anti-spam intelligente**: 5-8 news selezionate/giorno, max 3/ora
- ✅ **Traduzioni automatiche**: Inglese → Italiano con Google Translate
- ✅ **4 fonti premium**: Phoenix News, Wu Blockchain, Unfolded, Coingraph
- ✅ **Database SQLite**: Tracking completo, anti-duplicati, statistiche

## 📊 Sistema Scoring Avanzato

| Score | Azione | Esempi |
|-------|--------|---------|
| **90+** | 🚨 IMMEDIATA | "SEC approves Bitcoin ETF" |
| **80+** | ⚡ RAPIDA | "Fed cuts rates, BTC surges" |
| **70+** | 💰 NORMALE | "BlackRock files ETH ETF" |
| **<70** | 💾 SALVATO | News secondarie |

## 🛡️ Filtri Anti-Spam

- **Rate limiting**: Max 3 post/ora, min 45min tra post
- **Pausa notturna**: 1-6 AM (eccetto score >95)
- **Esclusioni**: Technical analysis, airdrop, meme coin, DYOR
- **Target dinamico**: 5-8 news/giorno (weekend ridotto)

## 🔧 Setup Dettagliato

### 1. Creazione Bot Telegram
```bash
# 1. Vai su @BotFather
# 2. /newbot → Nome: "Criptovaluta News Bot"    
# 3. Copia il TOKEN ricevuto
```

### 2. Ottenere IDs Canali
```bash
python crypto_bot.py --setup-ids
# Inserisci token → Ottieni IDs numerici dei 4 canali fonte
```

### 3. Configurazione config.py
```python
BOT_CONFIG = {
        'bot_token': 'YOUR_TOKEN_HERE',          # Da @BotFather
        'target_channel': '@criptovalutait', # Canale pubblicazione
        'admin_chat_id': 'YOUR_USER_ID',        # Per notifiche admin
}
```

### 4. Deploy Produzione (VPS)
```bash
sudo ./deploy.sh    # Installa come servizio systemd
```

## 📋 Comandi Bot Disponibili

- `/stats` - Statistiche giornaliere e performance
- `/status` - Stato sistema e monitoraggio fonti

## 📊 Monitoraggio Sistema

```bash
# Stato generale
./monitor.sh

# Logs in tempo reale
sudo journalctl -u crypto-bot -f

# Controllo database
sqlite3 criptovaluta_news.db "SELECT COUNT(*) FROM news_items WHERE published=1 AND DATE(published_at)=DATE('now');"
```

## 🔄 Manutenzione

### Aggiornamento Keywords
Modifica `FINANCIAL_IMPACT_KEYWORDS` in `crypto_bot.py`:
```python
'nuovo_evento': 75,    # Aggiungi nuove keywords rilevanti
```

### Backup Database
```bash
# Backup automatico giornaliero
cp criptovaluta_news.db backup_$(date +%Y%m%d).db
```

## 🆘 Troubleshooting

**❌ Bot non riceve messaggi:**
- Verifica IDs canali corretti con `--setup-ids`
- Aggiungi bot ai canali fonte come amministratore
- Controlla token valido

**❌ Errori traduzione:**
- Il bot usa fallback al testo inglese se Google Translate fallisce
- Rate limit gestito automaticamente

**❌ News non pubblicate:**
- Verifica score con `/stats` (deve essere ≥70)
- Controlla limiti giornalieri raggiunti
- Verifica non sia pausa notturna

## 📈 Esempi News Filtrate

### ✅ News che PASSANO (Score alto)
- "SEC approves first Bitcoin ETF with $2B day-1 inflow" (Score: 95)
- "Fed announces 0.5% rate cut, Bitcoin surges 8%" (Score: 88) 
- "BlackRock files Ethereum ETF application" (Score: 82)
- "Tesla reports additional $500M Bitcoin purchase" (Score: 78)

### ❌ News ESCLUSE automaticamente
- "Bitcoin technical analysis shows bullish pattern" (Analisi tecnica)
- "Top 10 altcoins for massive gains" (Speculation)
- "Free crypto airdrop for early adopters" (Airdrop)
- "Diamond hands HODL to the moon" (Meme content)

## 📞 Supporto

Bot sviluppato specificamente per **Criptovaluta.it**
Focus: News finanziarie/macroeconomiche ultra-rilevanti per trading/investimenti

---
🚀 **Ready per aumentare reattività e valore del vostro canale @criptovalutait!**
EOF

# ==============================================================================
# 📄 FILE 2: requirements.txt
# ==============================================================================
cat > requirements.txt << 'EOF'
python-telegram-bot==20.7
googletrans==4.0.0rc1
beautifulsoup4==4.12.2
aiohttp==3.9.1
requests==2.31.0
sqlite3
EOF

# ==============================================================================
# 📄 FILE 3: config.py (Template configurazione)
# ==============================================================================
cat > config.py << 'EOF'
#!/usr/bin/env python3
"""
Configurazione Bot Criptovaluta.it
MODIFICA I VALORI QUI SOTTO PRIMA DI AVVIARE IL BOT
"""

# =============================================================================
# CONFIGURAZIONE PRINCIPALE - MODIFICARE QUESTI VALORI
# =============================================================================

BOT_CONFIG = {
        'bot_token': 'YOUR_BOT_TOKEN_HERE',    # INSERISCI TOKEN DA @BotFather
        'target_channel': '@criptovalutait',    # Canale di pubblicazione
        'admin_chat_id': 'YOUR_ADMIN_CHAT_ID',    # INSERISCI IL TUO USER ID
        'database_path': 'criptovaluta_news.db'
}

# =============================================================================
# IDS CANALI FONTE - AGGIORNARE CON IDS REALI (usa --setup-ids)
# =============================================================================

SOURCE_CHANNELS = {
        'phoenix_news': {
                'telegram_id': -1001234567890,    # AGGIORNA CON ID REALE
                'username': '@PhoenixNewsImportant',
                'website': 'https://phoenixnews.io/',
                'reliability_score': 1.4,
                'specialization': 'breaking_financial'
        },
        'wu_blockchain': {
                'telegram_id': -1001234567891,    # AGGIORNA CON ID REALE
                'username': '@wublockchainenglish', 
                'reliability_score': 1.5,
                'specialization': 'institutional_asia'
        },
        'unfolded': {
                'telegram_id': -1001234567892,    # AGGIORNA CON ID REALE
                'username': '@unfolded',
                'reliability_score': 1.3, 
                'specialization': 'financial_analysis'
        },
        'coingraph_news': {
                'telegram_id': -1001234567893,    # AGGIORNA CON ID REALE
                'username': '@CoingraphNews',
                'reliability_score': 1.2,
                'specialization': 'market_data'
        }
}

# =============================================================================
# PARAMETRI AVANZATI (Opzionali - valori ottimali già impostati)
# =============================================================================

ADVANCED_CONFIG = {
        # Target pubblicazioni giornaliere
        'daily_target_range': {'min': 5, 'max': 8},
        
        # Soglie score per pubblicazione
        'critical_score_threshold': 90,        # Pubblicazione immediata
        'high_score_threshold': 80,                # Pubblicazione rapida    
        'normal_score_threshold': 70,            # Pubblicazione normale
        
        # Rate limiting
        'min_interval_minutes': 45,                # Minimo tra post
        'max_posts_per_hour': 3,                      # Max burst orario
        
        # Orari e timing
        'night_pause_hours': [1,2,3,4,5,6],    # Pausa notturna
        'weekend_reduction': 0.8,                          # Riduzione weekend (80% target)
        
        # Soglie notifiche admin
        'admin_notify_threshold': 85,            # Notifica admin per score >85
        'emergency_override_score': 95          # Override tutti i limiti
}
EOF

# ==============================================================================
# 📄 FILE 4: crypto_bot.py (BOT PRINCIPALE - VERSIONE COMPLETA)
# ==============================================================================
cat > crypto_bot.py << 'EOF'
#!/usr/bin/env python3
"""
Bot Telegram per Breaking News Crypto Finanziarie - Criptovaluta.it
Ultra-reattivo, focus su news macroeconomiche e annunci ufficiali
Versione: 1.0 - Production Ready
"""

import asyncio
import sqlite3
import hashlib
import re
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Telegram imports
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# Translation imports    
from googletrans import Translator
import aiohttp
from bs4 import BeautifulSoup

# Import configurazione
try:
        from config import BOT_CONFIG, SOURCE_CHANNELS, ADVANCED_CONFIG
except ImportError:
        print("❌ ERRORE: File config.py non trovato!")
        print("💡 Modifica config.py con i tuoi valori prima di avviare")
        sys.exit(1)

# Setup logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
                logging.FileHandler('crypto_bot.log'),
                logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SISTEMA FILTRI FINANZIARI ULTRA-SPECIFICI
# =============================================================================

class FinancialNewsFilter:
        """Filtri ultra-specifici per news finanziarie e macroeconomiche"""
        
        FINANCIAL_IMPACT_KEYWORDS = {
                # Regolamentazione governativa (massima priorità)
                'SEC approves': 80, 'SEC rejects': 75, 'SEC decision': 70,
                'Fed announces': 75, 'Federal Reserve': 70, 'FOMC': 65,
                'Treasury': 65, 'Biden administration': 60, 'Congress': 55,
                'regulation passed': 70, 'bill signed': 65, 'law enacted': 65,
                
                # ETF e prodotti istituzionali
                'ETF approved': 85, 'ETF rejected': 80, 'ETF filing': 60,
                'BlackRock': 65, 'Fidelity': 60, 'Vanguard': 60, 'Grayscale': 65,
                
                # Dati macroeconomici ufficiali
                'inflation data': 70, 'CPI': 65, 'GDP': 60, 'unemployment': 55,
                'interest rates': 70, 'rate hike': 75, 'rate cut': 75,
                'QE': 70, 'quantitative easing': 70, 'monetary policy': 65,
                
                # Eventi di mercato significativi    
                'market crash': 80, 'all-time high': 70, 'ATH': 70,
                'halving': 75, 'hard fork': 60, 'network upgrade': 55,
                
                # Aziende Fortune 500 e crypto
                'Tesla': 65, 'MicroStrategy': 70, 'Square': 60, 'PayPal': 60,
                'Coinbase': 65, 'Binance': 60, 'Kraken': 55,
                
                # Hack e sicurezza
                'hack': 75, 'exploit': 70, 'stolen': 65, 'breach': 65
        }
        
        FINANCIAL_ENTITIES = {
                # Istituzioni finanziarie
                'Federal Reserve': 75, 'ECB': 70, 'Bank of England': 65,
                'JPMorgan': 60, 'Goldman Sachs': 65, 'Morgan Stanley': 60,
                
                # Autorità regolamentazione
                'SEC': 80, 'CFTC': 70, 'FinCEN': 65, 'OCC': 60,
                
                # Tech companies
                'Apple': 60, 'Microsoft': 55, 'Nvidia': 60,
                
                # Crypto exchanges
                'Coinbase': 65, 'Binance': 60, 'Kraken': 55
        }
        
        CRYPTO_ASSETS = {
                'Bitcoin': 40, 'BTC': 40, 'Ethereum': 35, 'ETH': 35,
                'Solana': 25, 'SOL': 25, 'XRP': 25, 'Cardano': 20
        }
        
        EXCLUSION_KEYWORDS = [
                'airdrop', 'giveaway', 'contest', 'technical analysis', 
                'price prediction', 'meme coin', 'not financial advice', 'DYOR'
        ]
        
        def is_financial_relevant(self, text: str) -> Tuple[bool, int]:
                text_lower = text.lower()
                
                # Check esclusioni
                for exclusion in self.EXCLUSION_KEYWORDS:
                        if exclusion in text_lower:
                                return False, 0
                
                score = 0
                
                # Score keywords finanziarie
                for keyword, points in self.FINANCIAL_IMPACT_KEYWORDS.items():
                        if keyword.lower() in text_lower:
                                score += points
                                
                # Score entità finanziarie
                for entity, points in self.FINANCIAL_ENTITIES.items():
                        if entity.lower() in text_lower:
                                score += points
                                
                # Score crypto assets
                for crypto, points in self.CRYPTO_ASSETS.items():
                        if crypto.lower() in text_lower:
                                score += points
                
                # Bonus dati quantitativi
                score += self._calculate_data_bonus(text)
                
                return score >= 50, score
        
        def _calculate_data_bonus(self, text: str) -> int:
                bonus = 0
                
                # Prezzi significativi
                if re.search(r'\$[\d,]+[KMB]?', text):
                        bonus += 15
                        
                # Percentuali significative
                percentages = re.findall(r'(\d+(?:\.\d+)?)%', text)
                for perc in percentages:
                        if float(perc) >= 10:
                                bonus += 20
                        elif float(perc) >= 5:
                                bonus += 10
                                
                return min(bonus, 50)

# =============================================================================
# SISTEMA SCORING E DATABASE
# =============================================================================

class NewsScorer:
        def __init__(self):
                self.filter = FinancialNewsFilter()
                
        def calculate_score(self, text: str, source_name: str) -> int:
                is_relevant, base_score = self.filter.is_financial_relevant(text)
                
                if not is_relevant:
                        return 0
                        
                text_lower = text.lower()
                
                # Bonus urgenza
                urgency_bonus = 25 if any(word in text_lower for word in ['breaking', 'urgent', 'alert']) else 0
                
                # Bonus ufficialità    
                official_bonus = 20 if any(word in text_lower for word in ['announces', 'confirmed', 'official']) else 0
                
                # Bonus emoji
                emoji_bonus = 15 if any(emoji in text for emoji in ['🚨', '⚠️', '🔥']) else 0
                
                # Moltiplicatore fonte
                source_config = SOURCE_CHANNELS.get(source_name, {})
                reliability = source_config.get('reliability_score', 1.0)
                
                total_score = (base_score + urgency_bonus + official_bonus + emoji_bonus) * reliability
                
                return min(int(total_score), 100)

class NewsDatabase:
        def __init__(self, db_path: str):
                self.db_path = db_path
                self.init_database()
        
        def init_database(self):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS news_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                original_text TEXT NOT NULL,
                                translated_text TEXT,
                                text_hash TEXT UNIQUE,
                                source_name TEXT NOT NULL,
                                score INTEGER NOT NULL,
                                is_relevant BOOLEAN NOT NULL,
                                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                published BOOLEAN DEFAULT FALSE,
                                published_at TIMESTAMP,
                                telegram_message_id INTEGER
                        )
                ''')
                
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS processed_messages (
                                source_name TEXT,
                                message_id INTEGER,
                                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                PRIMARY KEY (source_name, message_id)
                        )
                ''')
                
                conn.commit()
                conn.close()
        
        def save_news_candidate(self, news_data: Dict) -> Optional[int]:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                text_hash = hashlib.md5(news_data['original_text'].encode()).hexdigest()
                
                try:
                        cursor.execute('''
                                INSERT INTO news_items 
                                (original_text, text_hash, source_name, score, is_relevant, telegram_message_id)
                                VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                                news_data['original_text'], text_hash, news_data['source_name'],
                                news_data['score'], news_data['is_relevant'], news_data.get('message_id')
                        ))
                        
                        news_id = cursor.lastrowid
                        conn.commit()
                        return news_id
                        
                except sqlite3.IntegrityError:
                        return None
                finally:
                        conn.close()
        
        def mark_as_published(self, news_id: int, translated_text: str = None):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                        UPDATE news_items 
                        SET published = TRUE, published_at = CURRENT_TIMESTAMP, translated_text = ?
                        WHERE id = ?
                ''', (translated_text, news_id))
                
                conn.commit()
                conn.close()
        
        def get_daily_published_count(self) -> int:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                        SELECT COUNT(*) FROM news_items 
                        WHERE published = TRUE AND DATE(published_at) = DATE('now')
                ''')
                
                count = cursor.fetchone()[0]
                conn.close()
                return count
        
        def is_message_processed(self, source_name: str, message_id: int) -> bool:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                        SELECT 1 FROM processed_messages 
                        WHERE source_name = ? AND message_id = ?
                ''', (source_name, message_id))
                
                exists = cursor.fetchone() is not None
                conn.close()
                return exists
        
        def mark_message_processed(self, source_name: str, message_id: int):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                        INSERT OR IGNORE INTO processed_messages (source_name, message_id)
                        VALUES (?, ?)
                ''', (source_name, message_id))
                
                conn.commit()
                conn.close()

# =============================================================================
# TRADUZIONE E FORMATTING
# =============================================================================

class NewsFormatter:
        def __init__(self):
                self.translator = Translator()
        
        async def translate_text(self, text: str) -> str:
                try:
                        translated = self.translator.translate(text, src='en', dest='it')
                        return translated.text
                except Exception as e:
                        logger.error(f"Errore traduzione: {e}")
                        return text
        
        def format_for_channel(self, original_text: str, translated_text: str, 
                                                    source_name: str, score: int, priority: str = 'NORMAL') -> str:
                
                content_emoji = self._get_content_emoji(translated_text)
                
                if priority == 'CRITICAL':
                        prefix = "🚨🔥 **ULTRA BREAKING CRYPTO** 🔥🚨"
                elif priority == 'HIGH':
                        prefix = f"{content_emoji} **BREAKING FINANZIARIO**"
                else:
                        prefix = f"{content_emoji} **CRYPTO BREAKING**"
                
                source_credit = self._get_source_credit(source_name)
                
                formatted_message = f"""
{prefix}

{translated_text}

📊 *Score: {score}/100* | 🔗 *{source_credit}*

💎 **[Criptovaluta.it](https://t.me/criptovalutait)** | *#1 Community Crypto Italia*
"""
                
                return formatted_message.strip()
        
        def _get_content_emoji(self, text: str) -> str:
                text_lower = text.lower()
                
                if any(word in text_lower for word in ['sec', 'regolament', 'etf']):
                        return "⚖️"
                elif any(word in text_lower for word in ['fed', 'tassi', 'inflazione']):
                        return "🏦"
                elif any(word in text_lower for word in ['prezzo', 'ath', 'record']):
                        return "🚀"
                elif any(word in text_lower for word in ['crollo', 'crash']):
                        return "📉"
                elif any(word in text_lower for word in ['hack', 'violazione']):
                        return "🔴"
                else:
                        return "💰"
        
        def _get_source_credit(self, source_name: str) -> str:
                credits = {
                        'phoenix_news': 'Phoenix News',
                        'wu_blockchain': 'Wu Blockchain',
                        'unfolded': 'Unfolded',
                        'coingraph_news': 'Coingraph'
                }
                return credits.get(source_name, 'Fonte Internazionale')

# =============================================================================
# SISTEMA PUBBLICAZIONE REATTIVA
# =============================================================================

class ReactivePublisher:
        def __init__(self, bot: Bot, db: NewsDatabase, formatter: NewsFormatter):
                self.bot = bot
                self.db = db
                self.formatter = formatter
                self.scorer = NewsScorer()
                
                # Config da ADVANCED_CONFIG
                self.daily_targets = ADVANCED_CONFIG['daily_target_range']
                self.min_interval_minutes = ADVANCED_CONFIG['min_interval_minutes']
                self.max_posts_per_hour = ADVANCED_CONFIG['max_posts_per_hour']
                self.night_pause_hours = ADVANCED_CONFIG['night_pause_hours']
                
                self.last_post_time = None
                self.posts_this_hour = 0
                self.hour_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        async def process_incoming_message(self, message, source_name: str) -> bool:
                # Check se già processato
                if self.db.is_message_processed(source_name, message.message_id):
                        return False
                        
                # Calcola score
                score = self.scorer.calculate_score(message.text, source_name)
                is_relevant, _ = self.scorer.filter.is_financial_relevant(message.text)
                
                # Salva nel database
                news_data = {
                        'original_text': message.text,
                        'source_name': source_name,
                        'score': score,
                        'is_relevant': is_relevant,
                        'message_id': message.message_id
                }
                
                news_id = self.db.save_news_candidate(news_data)
                self.db.mark_message_processed(source_name, message.message_id)
                
                if news_id is None:
                        return False
                
                # Decide pubblicazione
                if is_relevant and score >= ADVANCED_CONFIG['normal_score_threshold']:
                        return await self._attempt_publication(news_data, news_id)
                        
                return False
        
        async def _attempt_publication(self, news_data: Dict, news_id: int) -> bool:
                score = news_data['score']
                
                if not self._can_publish_now(score):
                        return False
                
                # Determina priorità
                if score >= ADVANCED_CONFIG['critical_score_threshold']:
                        priority = 'CRITICAL'
                elif score >= ADVANCED_CONFIG['high_score_threshold']:
                        priority = 'HIGH'
                else:
                        priority = 'NORMAL'
                        
                return await self._publish_immediately(news_data, news_id, priority)
        
        async def _publish_immediately(self, news_data: Dict, news_id: int, priority: str) -> bool:
                try:
                        # Traduci
                        translated_text = await self.formatter.translate_text(news_data['original_text'])
                        
                        # Formatta
                        formatted_message = self.formatter.format_for_channel(
                                news_data['original_text'], translated_text,
                                news_data['source_name'], news_data['score'], priority
                        )
                        
                        # Pubblica
                        await self.bot.send_message(
                                chat_id=BOT_CONFIG['target_channel'],
                                text=formatted_message,
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                        )
                        
                        # Aggiorna database e contatori
                        self.db.mark_as_published(news_id, translated_text)
                        self._update_publication_counters()
                        
                        logger.info(f"📰 Pubblicata news {news_id} - Score: {news_data['score']} - Priorità: {priority}")
                        
                        # Notifica admin per score alti
                        if news_data['score'] >= ADVANCED_CONFIG['admin_notify_threshold']:
                                await self._notify_admin_publication(news_data, priority)
                        
                        return True
                        
                except Exception as e:
                        logger.error(f"❌ Errore pubblicazione news {news_id}: {e}")
                        return False
        
        def _can_publish_now(self, score: int = 0) -> bool:
                now = datetime.now()
                
                # Emergency override
                if score >= ADVANCED_CONFIG['emergency_override_score']:
                        return True
                
                # Pausa notturna
                if now.hour in self.night_pause_hours:
                        return False
                
                # Limite giornaliero
                daily_published = self.db.get_daily_published_count()
                if daily_published >= self.daily_targets['max']:
                        return False
                
                # Intervallo minimo
                if self.last_post_time:
                        time_since_last = (now - self.last_post_time).total_seconds() / 60
                        if time_since_last < self.min_interval_minutes:
                                return False
                
                # Limite orario
                self._reset_hourly_counter_if_needed()
                if self.posts_this_hour >= self.max_posts_per_hour:
                        return False
                        
                return True
        
        def _update_publication_counters(self):
                self.last_post_time = datetime.now()
                self.posts_this_hour += 1
        
        def _reset_hourly_counter_if_needed(self):
                now = datetime.now()
                current_hour = now.replace(minute=0, second=0, microsecond=0)
                
                if current_hour > self.hour_reset_time:
                        self.posts_this_hour = 0
                        self.hour_reset_time = current_hour
        
        async def _notify_admin_publication(self, news_data: Dict, priority: str):
                try:
                        admin_message = f"""
🔔 **NEWS PUBBLICATA** - {priority}

📊 Score: {news_data['score']}/100
🔗 Fonte: {news_data['source_name']}
📝 Testo: {news_data['original_text'][:150]}...

✅ Pubblicata automaticamente su @criptovalutait
                        """
                        
                        await self.bot.send_message(
                                chat_id=BOT_CONFIG['admin_chat_id'],
                                text=admin_message,
                                parse_mode='Markdown'
                        )
                except Exception as e:
                        logger.error(f"Errore notifica admin: {e}")

# =============================================================================
# BOT MANAGER PRINCIPALE
# =============================================================================

class CryptoBotManager:
        def __init__(self):
                self.bot = None
                self.application = None
                self.db = NewsDatabase(BOT_CONFIG['database_path'])
                self.formatter = NewsFormatter()
                self.publisher = None
                
        async def initialize(self):
                # Verifica configurazione
                if BOT_CONFIG['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
                        logger.error("❌ ERRORE: Configura BOT_TOKEN in config.py!")
                        sys.exit(1)
                        
                self.bot = Bot(token=BOT_CONFIG['bot_token'])
                self.application = Application.builder().token(BOT_CONFIG['bot_token']).build()
                self.publisher = ReactivePublisher(self.bot, self.db, self.formatter)
                
                self._setup_handlers()
                logger.info("✅ Bot inizializzato correttamente")
        
        def _setup_handlers(self):
                # Handler messaggi da fonti
                message_handler = MessageHandler(
                        filters.Chat(chat_id=list(ch['telegram_id'] for ch in SOURCE_CHANNELS.values())),
                        self._handle_source_message
                )
                self.application.add_handler(message_handler)
                
                # Comandi admin
                self.application.add_handler(CommandHandler("stats", self._cmd_stats))
                self.application.add_handler(CommandHandler("status", self._cmd_status))
                
        async def _handle_source_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
                message = update.message
                
                if not message or not message.text:
                        return
                        
                # Identifica fonte
                source_name = None
                for name, config in SOURCE_CHANNELS.items():
                        if message.chat_id == config['telegram_id']:
                                source_name = name
                                break
                
                if not source_name:
                        return
                        
                try:
                        await self.publisher.process_incoming_message(message, source_name)
                except Exception as e:
                        logger.error(f"❌ Errore processing messaggio da {source_name}: {e}")
        
        async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
                if str(update.effective_chat.id) != BOT_CONFIG['admin_chat_id']:
                        return
                        
                daily_published = self.db.get_daily_published_count()
                
                stats_message = f"""
📊 **STATISTICHE BOT OGGI**

✅ News pubblicate: {daily_published}/{self.publisher.daily_targets['max']}
⏰ Ultimo post: {self.publisher.last_post_time or 'Nessuno oggi'}
📈 Post ultima ora: {self.publisher.posts_this_hour}/{self.publisher.max_posts_per_hour}

🎯 Target: {BOT_CONFIG['target_channel']}
💾 Database: {BOT_CONFIG['database_path']}
                """
                
                await update.message.reply_text(stats_message, parse_mode='Markdown')
        
        async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
                if str(update.effective_chat.id) != BOT_CONFIG['admin_chat_id']:
                        return
                        
                can_publish = self.publisher._can_publish_now()
                
                status_message = f"""
🤖 **STATUS SISTEMA**

✅ Bot attivo: Sì
📡 Monitoraggio: {len(SOURCE_CHANNELS)} fonti
🚦 Può pubblicare: {'✅ Sì' if can_publish else '❌ No'}

🔍 **Fonti monitorate:**
{chr(10).join(f"• {config['username']}" for config in SOURCE_CHANNELS.values())}
                """
                
                await update.message.reply_text(status_message, parse_mode='Markdown')
        
        async def start_monitoring(self):
                logger.info("🚀 Avvio monitoraggio fonti...")
                
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling()
                
                logger.info("📡 Bot avviato e in ascolto!")
                
                try:
                        while True:
                                await asyncio.sleep(60)
                except KeyboardInterrupt:
                        logger.info("🛑 Interruzione ricevuta, chiusura bot...")
                        await self.application.stop()

# =============================================================================
# SCRIPT SETUP IDS CANALI
# =============================================================================

async def get_channel_ids_script():
        print("🔧 Script per ottenere IDs canali Telegram")
        print("=========================================")
        print("1. Crea un bot con @BotFather")
        print("2. Aggiungi il bot ai 4 canali fonte come amministratore")
        print("3. Inserisci il token qui sotto")
        
        token = input("\n🤖 Token bot: ")
        
        if not token:
                print("❌ Token richiesto!")
                return
                
        bot = Bot(token=token)
        
        channels = [
                "@PhoenixNewsImportant",
                "@unfolded", 
                "@wublockchainenglish",
                "@CoingraphNews"
        ]
        
        print("\n📡 Recupero IDs canali...")
        
        for channel in channels:
                try:
                        chat = await bot.get_chat(channel)
                        print(f"✅ {channel}: ID = {chat.id}")
                except Exception as e:
                        print(f"❌ {channel}: Errore = {e}")
        
        print("\n✅ Copia questi IDs in config.py nella sezione SOURCE_CHANNELS!")
        print("📝 Esempio: 'telegram_id': -1001234567890,")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
        # Verifica configurazione base
        if BOT_CONFIG['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
                print("❌ ERRORE: Configura BOT_TOKEN in config.py!")
                print("📝 1. Vai su @BotFather e crea un bot")
                print("📝 2. Copia il token in config.py")
                print("📝 3. Esegui: python crypto_bot.py --setup-ids")
                return
        
        # Inizializza e avvia bot
        bot_manager = CryptoBotManager()
        await bot_manager.initialize()
        
        print("🚀 Avvio Bot Criptovaluta.it - News Finanziarie")
        print("=" * 50)
        print(f"📡 Monitoraggio {len(SOURCE_CHANNELS)} fonti premium")
        print(f"🎯 Pubblicazione: {BOT_CONFIG['target_channel']}")
        print(f"💎 Target: {ADVANCED_CONFIG['daily_target_range']['min']}-{ADVANCED_CONFIG['daily_target_range']['max']} news/giorno")
        print("🔍 Focus: News finanziarie/macroeconomiche ultra-rilevanti")
        print("=" * 50)
        
        await bot_manager.start_monitoring()

if __name__ == "__main__":
        if len(sys.argv) > 1 and sys.argv[1] == '--setup-ids':
                asyncio.run(get_channel_ids_script())
        else:
                asyncio.run(main())
EOF

# ==============================================================================
# 📄 FILE 5: install.sh (Installazione automatica)
# ==============================================================================
cat > install.sh << 'EOF'
#!/bin/bash

echo "🚀 Setup Bot Criptovaluta.it - News Finanziarie"
echo "==============================================="

# Verifica Python
if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 non trovato. Installa Python 3.8+"
        exit 1
fi

echo "✅ Python trovato: $(python3 --version)"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 non trovato. Installa pip3"
        exit 1
fi

# Crea virtual environment
echo "📦 Creazione virtual environment..."
python3 -m venv venv

# Attiva virtual environment
echo "🔧 Attivazione virtual environment..."
source venv/bin/activate

# Aggiorna pip
echo "⬆️    Aggiornamento pip..."
pip install --upgrade pip

# Installa dipendenze
echo "📚 Installazione dipendenze..."
pip install -r requirements.txt

echo ""
echo "✅ Installazione completata!"
echo ""
echo "📋 Prossimi passi:"
echo "1. 🤖 Crea bot: @BotFather → /newbot"
echo "2. 📝 Configura: nano config.py"
echo "3. 🔍 IDs canali: python crypto_bot.py --setup-ids"
echo "4. ✅ Test: python test_config.py"
echo "5. 🚀 Avvio: ./start.sh"
echo ""
echo "💎 Bot pronto per @criptovalutait!"
EOF

# ==============================================================================
# 📄 FILE 6: start.sh (Avvio rapido)
# ==============================================================================
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Avvio Bot Criptovaluta.it"
echo "============================="

# Controlla se virtual environment esiste
if [ ! -d "venv" ]; then
        echo "❌ Virtual environment non trovato. Esegui prima ./install.sh"
        exit 1
fi

# Attiva virtual environment
source venv/bin/activate

# Controlla configurazione
if grep -q "YOUR_BOT_TOKEN_HERE" config.py; then
        echo "❌ ERRORE: Configura BOT_TOKEN in config.py"
        echo "📝 Modifica config.py con il tuo token da @BotFather"
        exit 1
fi

echo "✅ Configurazione OK"
echo "🤖 Avvio bot..."

# Avvia bot
python crypto_bot.py
EOF

# ==============================================================================
# 📄 FILE 7: test_config.py (Test configurazione)
# ==============================================================================
cat > test_config.py << 'EOF'
#!/usr/bin/env python3
"""
Script per testare la configurazione del bot
"""

import asyncio
import sys
from telegram import Bot

async def test_configuration():
        print("🔍 Test Configurazione Bot Criptovaluta.it")
        print("==========================================")
        
        try:
                from config import BOT_CONFIG, SOURCE_CHANNELS
        except ImportError:
                print("❌ File config.py non trovato!")
                return False
        
        # Test token bot
        print("🤖 Test token bot...")
        if BOT_CONFIG['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
                print("❌ Token non configurato! Modifica config.py")
                return False
                
        try:
                bot = Bot(token=BOT_CONFIG['bot_token'])
                bot_info = await bot.get_me()
                print(f"✅ Bot OK: @{bot_info.username}")
        except Exception as e:
                print(f"❌ Errore token bot: {e}")
                return False
        
        # Test canali fonte
        print("\n📡 Test canali fonte...")
        success_count = 0
        for name, config in SOURCE_CHANNELS.items():
                try:
                        if config['telegram_id'] == -1001234567890:    # ID placeholder
                                print(f"⚠️    {config['username']}: Aggiorna con ID reale (usa --setup-ids)")
                                continue
                                
                        chat = await bot.get_chat(config['telegram_id'])
                        print(f"✅ {config['username']}: {chat.title}")
                        success_count += 1
                except Exception as e:
                        print(f"❌ {config['username']}: {e}")
        
        # Test canale target
        print(f"\n🎯 Test canale target: {BOT_CONFIG['target_channel']}...")
        try:
                target_chat = await bot.get_chat(BOT_CONFIG['target_channel'])
                print(f"✅ Target OK: {target_chat.title}")
                
                # Verifica permessi
                try:
                        bot_member = await bot.get_chat_member(BOT_CONFIG['target_channel'], bot_info.id)
                        if bot_member.can_post_messages:
                                print("✅ Permessi pubblicazione OK")
                        else:
                                print("⚠️    Aggiungi bot come admin con permessi posting")
                except:
                        print("⚠️    Aggiungi bot al canale come amministratore")
                        
        except Exception as e:
                print(f"❌ Errore canale target: {e}")
        
        print("\n" + "="*50)
        if success_count >= 2:
                print("✅ Configurazione PRONTA per avvio!")
                print("🚀 Esegui: ./start.sh")
        else:
                print("⚠️    Completa configurazione prima dell'avvio")
                print("📝 1. Aggiorna IDs in config.py")
                print("📝 2. Aggiungi bot ai canali come admin")
        
        return True

if __name__ == "__main__":
        asyncio.run(test_configuration())
EOF

# ==============================================================================
# 📄 FILE 8: deploy.sh (Deploy produzione)
# ==============================================================================
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploy Bot Criptovaluta.it su Server"
echo "======================================="

# Verifica sudo
if [ "$EUID" -ne 0 ]; then
        echo "❌ Esegui con sudo per deploy su server"
        exit 1
fi

# Crea directory deploy
mkdir -p /opt/criptovaluta-bot
cp -r * /opt/criptovaluta-bot/
cd /opt/criptovaluta-bot

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Crea servizio systemd
tee /etc/systemd/system/crypto-bot.service > /dev/null <<SYSTEMD_EOF
[Unit]
Description=Criptovaluta.it News Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/criptovaluta-bot
Environment=PATH=/opt/criptovaluta-bot/venv/bin
ExecStart=/opt/criptovaluta-bot/venv/bin/python crypto_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

# Reload systemd e abilita servizio
systemctl daemon-reload
systemctl enable crypto-bot.service

echo "✅ Bot deployato come servizio systemd"
echo ""
echo "📋 Comandi gestione:"
echo "• Avvio:      sudo systemctl start crypto-bot"
echo "• Stop:        sudo systemctl stop crypto-bot"
echo "• Restart: sudo systemctl restart crypto-bot"
echo "• Status:    sudo systemctl status crypto-bot"
echo "• Logs:        sudo journalctl -u crypto-bot -f"
echo ""
echo "⚠️    Configura config.py prima di avviare!"
EOF

# ==============================================================================
# 📄 FILE 9: monitor.sh (Monitoraggio sistema)
# ==============================================================================
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Monitoraggio Bot Criptovaluta.it"
echo "==================================="

# Status servizio
echo "🤖 Status Servizio:"
if systemctl is-active --quiet crypto-bot; then
        echo "✅ ATTIVO"
        systemctl status crypto-bot --no-pager -l | head -5
else
        echo "❌ INATTIVO"
fi

echo ""
echo "📋 Ultimi 10 log importanti:"
journalctl -u crypto-bot --no-pager -n 10 | grep -E "(ERROR|INFO.*Published|WARN)" || echo "Nessun log recente"

echo ""
echo "💾 Statistiche Database:"
if [ -f "criptovaluta_news.db" ]; then
        echo "✅ Database trovato"
        echo -n "📰 News raccolte oggi: "
        sqlite3 criptovaluta_news.db "SELECT COUNT(*) FROM news_items WHERE DATE(collected_at) = DATE('now');" 2>/dev/null || echo "Errore DB"
        echo -n "📤 News pubblicate oggi: "
        sqlite3 criptovaluta_news.db "SELECT COUNT(*) FROM news_items WHERE published = 1 AND DATE(published_at) = DATE('now');" 2>/dev/null || echo "Errore DB"
        echo -n "📊 Score medio news oggi: "
        sqlite3 criptovaluta_news.db "SELECT ROUND(AVG(score),1) FROM news_items WHERE DATE(collected_at) = DATE('now') AND is_relevant = 1;" 2>/dev/null || echo "N/A"
else
        echo "❌ Database non trovato"
fi

echo ""
echo "🔄 Comandi utili:"
echo "• Restart bot:    sudo systemctl restart crypto-bot"
echo "• Logs live:        sudo journalctl -u crypto-bot -f"
echo "• Stop bot:          sudo systemctl stop crypto-bot"
echo "• Start bot:        sudo systemctl start crypto-bot"
echo "• Edit config:    nano /opt/criptovaluta-bot/config.py"
EOF

# ==============================================================================
# 📄 FILE 10: Makefile per automazione
# ==============================================================================
cat > Makefile << 'EOF'
.PHONY: install test start deploy monitor clean

# Installazione rapida
install:
	chmod +x *.sh
	./install.sh

# Test configurazione
test:
	python test_config.py

# Avvio bot locale
start:
	./start.sh

# Deploy su server
deploy:
	sudo ./deploy.sh

# Monitoraggio
monitor:
	./monitor.sh

# Setup IDs canali
setup-ids:
	python crypto_bot.py --setup-ids

# Pulizia
clean:
	rm -rf venv/
	rm -f *.log
	rm -f *.db

# Backup database
backup:
	cp criptovaluta_news.db backup_$(shell date +%Y%m%d_%H%M%S).db

# Help
help:
	@echo "📋 Comandi disponibili:"
	@echo "    make install        - Installazione automatica"
	@echo "    make test              - Test configurazione"
	@echo "    make setup-ids    - Ottieni IDs canali"
	@echo "    make start            - Avvia bot locale"
	@echo "    make deploy          - Deploy su server"
	@echo "    make monitor        - Monitoraggio sistema"
	@echo "    make backup          - Backup database"
	@echo "    make clean            - Pulizia file temporanei"
EOF

# ==============================================================================
# FINALIZZAZIONE PACCHETTO
# ==============================================================================

# Rendi eseguibili gli script
chmod +x *.sh

echo ""
echo "✅ PACCHETTO COMPLETO CREATO!"
echo "==============================="
echo ""
echo "📁 File creati:"
echo "• crypto_bot.py            - Bot principale (production-ready)"
echo "• config.py                    - Configurazione (MODIFICA PRIMA DELL'USO)"
echo "• requirements.txt      - Dipendenze Python"
echo "• install.sh                  - Installazione automatica"
echo "• start.sh                      - Avvio rapido"
echo "• test_config.py          - Test configurazione"
echo "• deploy.sh                    - Deploy produzione"
echo "• monitor.sh                  - Monitoraggio sistema"
echo "• README.md                    - Documentazione completa"
echo "• Makefile                      - Automazione comandi"
echo ""
echo "🚀 SETUP RAPIDO (5 minuti):"
echo "1. ./install.sh                                        # Installazione"
echo "2. nano config.py                                    # Configura token"
echo "3. python crypto_bot.py --setup-ids # Ottieni IDs"
echo "4. python test_config.py                      # Test"
echo "5. ./start.sh                                            # Avvio!"
echo ""
echo "💎 Bot pronto per @criptovalutait!"
echo "🎯 Focus: 5-8 news finanziarie ultra-rilevanti/giorno"
