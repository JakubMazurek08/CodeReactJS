from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
import random
import json
import os
import logging
import time
import re
import uuid
from datetime import datetime
from functools import wraps
import pathlib

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

# Stały adres serwera AI z backupami
OLLAMA_SERVERS = [
    "https://ollama1.kkhost.pl",  # Główny  # Zapasowy 1
    "https://ollama3.kkhost.pl"  # Zapasowy 2 # Zapasowy 3
]
CURRENT_SERVER = OLLAMA_SERVERS[0]  # Domyślnie używamy pierwszego serwera

# Model używany dla rozmów kwalifikacyjnych
AI_MODEL = "qwen3:30b-a3b"  # Domyślny model

# Firebase configuration
try:
    # Odczytanie danych uwierzytelniających z pliku lub zmiennej środowiskowej
    if os.path.exists('firebase-credentials.json'):
        cred = credentials.Certificate('firebase-credentials.json')
    else:
        # Alternatywnie, używamy zmiennych środowiskowych
        firebase_config = json.loads(os.environ.get('FIREBASE_CONFIG', '{}'))
        cred = credentials.Certificate(firebase_config)
    
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', 'jobprepai.appspot.com')
    })
    
    db = firestore.client()
    bucket = storage.bucket()
    logger.info("Połączono z Firebase")
    FIREBASE_ENABLED = True
except Exception as e:
    logger.error(f"Błąd podczas inicjalizacji Firebase: {e}")
    FIREBASE_ENABLED = False
    # Implementujemy lokalny storage jako alternatywę
    if not os.path.exists('data'):
        os.makedirs('data/interviews')
        os.makedirs('data/cv')
        os.makedirs('data/jobs')
    
    # Przykładowe dane ofert pracy - załadowane tylko jeśli Firebase nie jest dostępne
    from sample_jobs import SAMPLE_JOBS
    logger.info("Używam lokalnego storage zamiast Firebase")

# Status serwera AI
ai_server_status = {
    'last_checked': None,
    'is_online': False,
    'ping_time': 0,
    'available_models': [],
    'current_server': CURRENT_SERVER
}

# Heartbeat sprawdzający status serwerów AI
last_server_switch_time = time.time()

def check_ai_server_health(force_check=False):
    """
    Sprawdza status serwera AI i przełącza na inny, jeśli bieżący jest niedostępny
    """
    global CURRENT_SERVER, ai_server_status, last_server_switch_time
    
    # Sprawdzamy tylko co 5 minut, chyba że wymuszono sprawdzenie
    current_time = time.time()
    if not force_check and ai_server_status['last_checked'] and current_time - ai_server_status['last_checked'] < 300:
        return ai_server_status
    
    # Potrzebne do śledzenia, czy znaleźliśmy działający serwer
    found_working_server = False
    best_server = None
    best_ping = float('inf')
    
    # Sprawdź wszystkie serwery, zaczynając od aktualnego
    current_index = OLLAMA_SERVERS.index(CURRENT_SERVER)
    server_order = OLLAMA_SERVERS[current_index:] + OLLAMA_SERVERS[:current_index]
    
    # Najpierw sprawdzamy aktualny serwer
    try:
        start_time = time.time()
        response = requests.get(f"{CURRENT_SERVER}/api/tags", timeout=3)
        ping_time = time.time() - start_time
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [model.get("name") for model in models]
            ai_server_status = {
                'last_checked': current_time,
                'is_online': True,
                'ping_time': round(ping_time, 3),
                'available_models': available_models,
                'current_server': CURRENT_SERVER
            }
            logger.info(f"Serwer AI jest dostępny: {CURRENT_SERVER}, ping: {ping_time:.3f}s")
            found_working_server = True
            return ai_server_status
    except Exception as e:
        logger.warning(f"Główny serwer AI niedostępny: {e}")
    
    # Jeśli aktualny serwer nie działa, sprawdzamy pozostałe
    # Ale tylko jeśli minęło co najmniej 30 sekund od ostatniego przełączenia
    if not found_working_server and current_time - last_server_switch_time > 30:
        for server in server_order[1:]:  # Pomijamy pierwszy, bo to aktualny serwer
            try:
                start_time = time.time()
                response = requests.get(f"{server}/api/tags", timeout=3)
                ping_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Serwer działa, zapisujemy jego dane
                    found_working_server = True
                    
                    # Jeśli ma lepszy ping niż poprzedni, zapisujemy jako najlepszy
                    if ping_time < best_ping:
                        best_ping = ping_time
                        best_server = server
                    models = response.json().get("models", [])
                        best_models = [model.get("name") for model in models]
            except Exception as e:
                logger.warning(f"Alternatywny serwer {server} niedostępny: {e}")
        
        # Jeśli znaleźliśmy działający serwer, przełączamy na najlepszy
        if found_working_server and best_server:
            CURRENT_SERVER = best_server
            last_server_switch_time = current_time
                    ai_server_status = {
                        'last_checked': current_time,
                        'is_online': True,
                'ping_time': round(best_ping, 3),
                'available_models': best_models,
                        'current_server': CURRENT_SERVER
                    }
            logger.info(f"Przełączono na serwer: {CURRENT_SERVER}, ping: {best_ping:.3f}s")
                    return ai_server_status
    
    # Jeśli wszystkie serwery nie odpowiadają
    ai_server_status = {
        'last_checked': current_time,
        'is_online': False,
        'ping_time': 0,
        'available_models': [],
        'current_server': CURRENT_SERVER,
        'error_message': "Wszystkie serwery AI są niedostępne!"
    }
    logger.error("Wszystkie serwery AI są niedostępne!")
    return ai_server_status

# Middleware do sprawdzania stanu serwera AI przy każdym zapytaniu
@app.before_request
def check_server_before_request():
    # Sprawdzamy tylko dla zapytań do API
    if request.path.startswith('/api/') and not request.path.startswith('/api/model/health'):
        check_ai_server_health()

def get_ai_response(prompt, system_prompt=None, context=None, stream=False):
    """
    Wysyła zapytanie do API Ollama i zwraca odpowiedź.
    
    Args:
        prompt (str): Zapytanie użytkownika
        system_prompt (str, optional): Instrukcja systemowa dla modelu
        context (list, optional): Kontekst konwersacji
        stream (bool, optional): Czy zwracać odpowiedź jako stream
        
    Returns:
        str or generator: Odpowiedź od modelu AI lub generator dla stream
    """
    # Sprawdź, czy serwer AI jest dostępny i używaj najbardziej odpowiedniego
    server_status = check_ai_server_health()
    if not server_status['is_online']:
        return "Przepraszamy, wszyscy asystenci AI są obecnie niedostępni. Prosimy spróbować ponownie za chwilę."
    
    api_url = f"{CURRENT_SERVER}/api/chat"
    
    # Domyślny system prompt jeśli nie podano
    if not system_prompt:
        system_prompt = """You are an expert recruiter conducting interviews in Polish. 
        You must respond in Polish, with natural Polish phrasing.
        Be professional but personable, and help the candidates prepare for job interviews.
        NEVER include <think> tags in your responses.
        """
    else:
        # Add instruction to never use <think> tags to existing system prompt
        system_prompt += "\nNEVER include <think> tags in your responses. Always respond ONLY in Polish."
    
    # Przygotuj wiadomości dla modelu
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Dodaj kontekst jeśli istnieje
    if context and isinstance(context, list):
        messages.extend(context)
    
    # Dodaj aktualne zapytanie
    messages.append({"role": "user", "content": prompt})
    
    # Parametry dla API Ollama
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        }
    }
    
    max_retries = 2
    retries = 0
    
    while retries <= max_retries:
    try:
        # Wykonaj zapytanie do API
            logger.info(f"Wysyłanie zapytania do API: {api_url} (próba {retries+1}/{max_retries+1})")
        
        if stream:
            # Zwróć generator dla odpowiedzi streamowanej
            def generate():
                    try:
                response = requests.post(api_url, json=payload, stream=True, timeout=60)
                if response.status_code == 200:
                    buffer = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8').strip())
                                if 'message' in data and 'content' in data['message']:
                                    content = data['message']['content']
                                            # Remove <think> tags from streamed content
                                            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                                    buffer += content
                                    yield content
                            except json.JSONDecodeError:
                                logger.error(f"Błąd przetwarzania odpowiedzi JSON: {line}")
                else:
                    logger.error(f"Błąd API Ollama: {response.status_code}")
                            yield f"Błąd podczas generowania odpowiedzi: {response.status_code}"
                    except Exception as e:
                        logger.error(f"Wyjątek podczas streamowania odpowiedzi: {e}")
                        yield f"Błąd podczas generowania odpowiedzi: {str(e)}"
            
            return generate()
        else:
            # Standardowa odpowiedź
            response = requests.post(api_url, json=payload, timeout=60)
            
            # Sprawdź czy zapytanie było udane
            if response.status_code == 200:
                result = response.json()
                    content = result.get("message", {}).get("content", "Nie udało się uzyskać odpowiedzi.")
                    # Remove <think> tags from response
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                    return content
            else:
                logger.error(f"Błąd API Ollama: {response.status_code}, {response.text}")
                    # Jeśli występuje błąd, spróbuj ponownie z innym serwerem
                    retries += 1
                    if retries <= max_retries:
                        # Zmieniamy serwer i próbujemy ponownie
                        check_ai_server_health(force_check=True)
                        api_url = f"{CURRENT_SERVER}/api/chat"
                        logger.info(f"Próba ponowna z serwerem: {CURRENT_SERVER}")
                        continue
                    return f"Przepraszamy, wystąpił błąd podczas komunikacji z asystentem AI (kod {response.status_code}). Prosimy spróbować ponownie."
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout podczas komunikacji z API Ollama")
            retries += 1
            if retries <= max_retries:
                # Zmieniamy serwer i próbujemy ponownie
                check_ai_server_health(force_check=True)
                api_url = f"{CURRENT_SERVER}/api/chat"
                logger.info(f"Próba ponowna z serwerem: {CURRENT_SERVER}")
                continue
            return "Przepraszamy, wystąpił timeout podczas komunikacji z asystentem AI. Prosimy spróbować ponownie za chwilę."
                
    except Exception as e:
        logger.error(f"Wyjątek podczas komunikacji z API Ollama: {e}")
            retries += 1
            if retries <= max_retries:
                # Zmieniamy serwer i próbujemy ponownie
                check_ai_server_health(force_check=True)
                api_url = f"{CURRENT_SERVER}/api/chat"
                logger.info(f"Próba ponowna z serwerem: {CURRENT_SERVER}")
                continue
            return f"Przepraszamy, wystąpił błąd podczas komunikacji z asystentem AI: {str(e)}. Prosimy spróbować ponownie."

# Lista zakazanych tematów do filtrowania
FORBIDDEN_TOPICS = [
    "żart", "dowcip", "śmieszne", "zabawne", "memy", "śmiech", "hehehe", "haha",
    "nieprzyzwoite", "seks", "erotyka", "alkohol", "narkotyki", "wojna", "polityka",
    "religia", "kontrowersje", "obraza"
]

def filter_inappropriate_content(text):
    """
    Filtruje nieodpowiednie treści z zapytania użytkownika
    
    Args:
        text (str): Tekst do filtrowania
        
    Returns:
        bool: True jeśli tekst zawiera nieodpowiednie treści, False w przeciwnym razie
    """
    text_lower = text.lower()
    for topic in FORBIDDEN_TOPICS:
        if topic in text_lower:
            return True
    return False

def create_safe_prompt_for_interview(job_title, skills, experience_level):
    """
    Tworzy bezpieczny prompt systemowy dla modelu AI do przeprowadzenia rozmowy kwalifikacyjnej
    
    Args:
        job_title (str): Tytuł stanowiska
        skills (list): Lista umiejętności
        experience_level (str): Poziom doświadczenia
        
    Returns:
        str: Systemowy prompt dla modelu AI
    """
    system_prompt = f"""
    You are a professional recruiter conducting a job interview for the position: {job_title}.
    
    Candidate information:
    - Skills: {', '.join(skills)}
    - Experience level: {experience_level}
    
    Your task:
    1. Conduct a professional job interview asking questions related to the position and skills.
    2. Avoid political, religious, controversial topics and jokes.
    3. Ask one question at a time, waiting for the candidate's response.
    4. You can ask technical questions related to the job.
    5. After 5-7 questions, end the interview, evaluate the candidate's skills and provide improvement suggestions.
    6. Maintain a professional tone throughout the interview.
    7. Stay focused on the job interview context.
    8. IMPORTANT: Always respond in Polish. Do not use English or any other language in your responses.
    9. NEVER include <think> tags in your responses.
    10. NEVER respond in Chinese characters.
    11. NEVER switch to English during the interview.
    
    Start the interview with a brief introduction as a recruiter and ask the first question about the candidate's experience.
    """
    return system_prompt

def get_jobs(keyword=None, skills=None, experience=None):
    """Pobiera oferty pracy z bazy danych z opcjonalnym filtrowaniem"""
    print(f"[DEBUG] get_jobs wywołane z parametrami: keyword={keyword}, skills={skills}, experience={experience}")
    
    if FIREBASE_ENABLED:
        jobs_ref = db.collection('jobs')
        query = jobs_ref
        
        # Dodaj filtry jeśli podano
        if keyword:
            keyword = keyword.lower()
            # Firestore nie wspiera wyszukiwania pełnotekstowego,
            # więc pobieramy wszystko i filtrujemy po stronie serwera
        
        # Wykonaj zapytanie
        jobs = [doc.to_dict() for doc in query.get()]
        print(f"[DEBUG] Pobrano {len(jobs)} ofert z Firebase")
        
        # Dodatkowe filtrowanie po stronie serwera
        if keyword:
            filtered_jobs = []
            for job in jobs:
                if (keyword in job.get('title', '').lower() or 
                    keyword in job.get('description', '').lower() or
                    any(keyword in skill.lower() for skill in job.get('required_skills', []))):
                    filtered_jobs.append(job)
            
            print(f"[DEBUG] Po filtrowaniu słowa kluczowego '{keyword}' pozostało {len(filtered_jobs)} ofert")
            return filtered_jobs
        
        return jobs
    else:
        # Używamy lokalnych danych
        print(f"[DEBUG] Firebase wyłączone, używam SAMPLE_JOBS, liczba ofert: {len(SAMPLE_JOBS)}")
        
        # Testowe dane
        sample_jobs = SAMPLE_JOBS
        
        # Dodatkowe filtrowanie po stronie serwera
        if keyword:
            keyword = keyword.lower()
            filtered_jobs = []
            for job in sample_jobs:
                if (keyword in job.get('title', '').lower() or 
                    keyword in job.get('description', '').lower() or
                    any(keyword in skill.lower() for skill in job.get('required_skills', []))):
                    filtered_jobs.append(job)
            
            print(f"[DEBUG] Po filtrowaniu słowa kluczowego '{keyword}' pozostało {len(filtered_jobs)} ofert z SAMPLE_JOBS")
            return filtered_jobs
            
        return sample_jobs

def match_job_to_skills(job_offer, user_skills, experience):
    """
    Oblicza dopasowanie oferty pracy do umiejętności i doświadczenia użytkownika
    
    Args:
        job_offer (dict): Oferta pracy
        user_skills (list): Lista umiejętności użytkownika
        experience (str): Doświadczenie użytkownika
        
    Returns:
        float: Procentowe dopasowanie (0-100)
    """
    print(f"[DEBUG] Dopasowuję ofertę: {job_offer.get('title')}")
    print(f"[DEBUG] - Wymagane umiejętności: {job_offer.get('required_skills', [])}")
    print(f"[DEBUG] - Umiejętności użytkownika: {user_skills}")
    print(f"[DEBUG] - Doświadczenie: {experience} vs {job_offer.get('experience_level', 'nie określono')}")
    
    # Sprawdź, czy required_skills istnieje i jest listą
    if not isinstance(job_offer.get("required_skills"), list):
        print(f"[DEBUG] BŁĄD: 'required_skills' nie jest listą lub nie istnieje w ofercie: {job_offer.get('id')}")
        return 30  # Minimalne dopasowanie
    
    # Konwersja wszystkich umiejętności na małe litery dla lepszego porównania
    user_skills_lower = [skill.lower() for skill in user_skills]
    job_skills_lower = [skill.lower() for skill in job_offer.get("required_skills", [])]
    
    # Definiowanie kategorii zawodowych dla lepszego dopasowania dziedzin
    job_categories = {
        "tech": ["developer", "software", "programmer", "engineer", "devops", "data", "it", "web", "frontend", "backend", "fullstack", 
                "architect", "admin", "analyst", "tech", "computer", "system", "network", "security", "cloud", "database", "qa", "tester"],
        "healthcare": ["doctor", "nurse", "therapist", "physician", "medical", "health", "clinical", "caregiver", "healthcare", 
                      "patient", "physio", "rehab", "pharmacy", "dental", "surgeon"],
        "finance": ["accountant", "financial", "finance", "banking", "investment", "trading", "broker", "auditor", "tax", "accounting"],
        "education": ["teacher", "professor", "educator", "tutor", "lecturer", "instructor", "coach", "teaching", "education", "training"],
        "hospitality": ["chef", "cook", "hotel", "restaurant", "catering", "hospitality", "tourism", "travel", "kitchen"],
        "retail": ["sales", "retail", "cashier", "store", "shop", "customer", "seller", "vendor", "merchandiser"],
        "logistics": ["driver", "transport", "delivery", "logistics", "warehouse", "shipping", "supply", "inventory", "fleet"]
    }
    
    # Określ kategorię oferty pracy na podstawie tytułu i wymaganych umiejętności
    job_title_lower = job_offer.get('title', '').lower()
    job_category = None
    job_category_score = 0
    
    for category, keywords in job_categories.items():
        score = 0
        # Sprawdź słowa kluczowe w tytule
        for keyword in keywords:
            if keyword in job_title_lower:
                score += 3  # Wyższy wagowo wynik za dopasowanie w tytule
                
        # Sprawdź słowa kluczowe w wymaganych umiejętnościach
        for skill in job_skills_lower:
            for keyword in keywords:
                if keyword in skill:
                    score += 1
        
        if score > job_category_score:
            job_category_score = score
            job_category = category
    
    print(f"[DEBUG] Wykryta kategoria oferty: {job_category or 'nieokreślona'} (wynik: {job_category_score})")
    
    # Określ kategorię użytkownika na podstawie jego umiejętności
    user_category = None
    user_category_score = 0
    
    for category, keywords in job_categories.items():
        score = 0
        for skill in user_skills_lower:
            for keyword in keywords:
                if keyword in skill:
                    score += 1
        
        if score > user_category_score:
            user_category_score = score
            user_category = category
    
    print(f"[DEBUG] Wykryta kategoria użytkownika: {user_category or 'nieokreślona'} (wynik: {user_category_score})")
    
    # Jeśli kategorie są określone, ale różne, znacznie obniż wynik dopasowania
    category_penalty = 0
    if job_category and user_category and job_category != user_category:
        category_penalty = 50  # Znaczna kara za dopasowanie między różnymi kategoriami
        print(f"[DEBUG] Kara za różne kategorie: {category_penalty}% (praca: {job_category}, użytkownik: {user_category})")
    
    # Jeśli brak umiejętności w ofercie, przyjmij domyślne dopasowanie 70%
    if not job_skills_lower:
        print(f"[DEBUG] Brak wymaganych umiejętności w ofercie, przyznano 70% dopasowania")
        skills_match = 70
    else:
        # Liczenie pasujących umiejętności z różnymi poziomami dopasowania
        exact_matches = 0
        partial_matches = 0
        
        # Słownik synonimów umiejętności (np. js = javascript)
        skill_synonyms = {
            "js": "javascript",
            "typescript": "javascript",
            "ts": "typescript",
            "react": "reactjs",
            "reactjs": "react",
            "vue": "vuejs",
            "vuejs": "vue",
            "node": "nodejs",
            "nodejs": "node",
            "angular": "angularjs",
            "angularjs": "angular",
            "postgres": "postgresql",
            "postgresql": "postgres",
            "mongo": "mongodb",
            "mongodb": "mongo",
            "py": "python",
            "golang": "go",
            "c#": "csharp",
            "c++": "cpp",
            "dotnet": ".net",
            ".net": "dotnet",
            "aws": "amazon web services",
            "amazon web services": "aws",
            "gcp": "google cloud",
            "google cloud": "gcp",
            "azure": "microsoft azure",
            "microsoft azure": "azure",
            "ux": "user experience",
            "ui": "user interface"
        }
        
        print("[DEBUG] Sprawdzam dopasowania umiejętności:")
        # Sprawdź każdą umiejętność użytkownika z każdą umiejętnością w ofercie
        for user_skill in user_skills_lower:
            matched = False
            
            # Najpierw szukaj dokładnych dopasowań
            if user_skill in job_skills_lower:
                exact_matches += 1
                matched = True
                print(f"[DEBUG] - Dokładne dopasowanie: {user_skill}")
                continue
                
            # Sprawdź synonimy
            user_skill_synonym = skill_synonyms.get(user_skill, user_skill)
            if user_skill_synonym != user_skill and user_skill_synonym in job_skills_lower:
                exact_matches += 1
                matched = True
                print(f"[DEBUG] - Dopasowanie przez synonim: {user_skill} -> {user_skill_synonym}")
                continue
            
            # Jeśli nie znaleźliśmy dokładnego dopasowania, szukaj częściowych
            if not matched:
            for job_skill in job_skills_lower:
                    # Sprawdź, czy umiejętność użytkownika jest częścią umiejętności z oferty
                    # lub odwrotnie - np. "javascript" pasuje do "javascript (es6)"
                    job_skill_synonym = skill_synonyms.get(job_skill, job_skill)
                    
                    if (user_skill in job_skill or job_skill in user_skill or 
                        user_skill_synonym in job_skill or job_skill_synonym in user_skill):
                        partial_matches += 1
                        matched = True
                        print(f"[DEBUG] - Częściowe dopasowanie: {user_skill} ~ {job_skill}")
                    break
        
            if not matched:
                print(f"[DEBUG] - Brak dopasowania: {user_skill}")
        
        # Oblicz wynik dopasowania umiejętności
        if len(job_skills_lower) > 0:
            # Dokładne dopasowania mają większą wagę niż częściowe
            skill_match_score = (exact_matches * 1.0 + partial_matches * 0.5) / len(job_skills_lower)
            
            # Normalizuj wynik do skali procentowej (0-100)
            # Minimum 30% dla jakiegokolwiek dopasowania, maksimum 80% za umiejętności
            skills_match = 30 + (skill_match_score * 50)
            print(f"[DEBUG] Dopasowanie umiejętności: {skills_match:.1f}% (dokładne: {exact_matches}, częściowe: {partial_matches}, wymaga: {len(job_skills_lower)})")
        else:
            skills_match = 50  # Domyślne 50% jeśli nie ma wymaganych umiejętności
            print(f"[DEBUG] Brak wymaganych umiejętności w ofercie, przyznano domyślnie: {skills_match}%")
    
    # Dopasowanie doświadczenia (20% całości)
    experience_mapping = {
        "junior": 0,
        "mid": 1,
        "senior": 2,
        "expert": 3
    }
    
    user_exp = experience_mapping.get(experience.lower(), 0)
    job_exp = experience_mapping.get(job_offer.get("experience_level", "").lower(), 0)
    
    if user_exp == job_exp:
        # Idealne dopasowanie
        experience_match = 20
        print(f"[DEBUG] Idealne dopasowanie doświadczenia: {experience} ({user_exp}) = {job_offer.get('experience_level', '')} ({job_exp}), przyznano: {experience_match}%")
    elif user_exp < job_exp:
        # Użytkownik ma mniejsze doświadczenie niż wymagane
        # Im większa różnica, tym niższy wynik, ale zawsze minimum 5%
        exp_diff = job_exp - user_exp
        experience_match = max(5, 20 - (exp_diff * 5))
        print(f"[DEBUG] Użytkownik ma mniejsze doświadczenie: {experience} ({user_exp}) < {job_offer.get('experience_level', '')} ({job_exp}), przyznano: {experience_match}%")
    else:
        # Użytkownik ma większe doświadczenie niż wymagane
        # Nadal dobre dopasowanie, ale lekko obniżone (może być nadkwalifikowany)
        exp_diff = user_exp - job_exp
        experience_match = max(15, 20 - (exp_diff * 1.5))
        print(f"[DEBUG] Użytkownik ma większe doświadczenie: {experience} ({user_exp}) > {job_offer.get('experience_level', '')} ({job_exp}), przyznano: {experience_match}%")
    
    # Dodatkowe punkty za lokalizację i typ zatrudnienia - zawsze 10% całości
    additional_match = 10
    print(f"[DEBUG] Dodatkowe punkty za lokalizację/typ zatrudnienia: {additional_match}%")
    
    # Oblicz całkowite dopasowanie
    total_match = skills_match + experience_match + additional_match
    
    # Zastosuj karę za różne kategorie
    if category_penalty > 0:
        # Przeskaluj karę w zależności od pierwotnego wyniku
        applied_penalty = category_penalty * (total_match / 100)
        total_match -= applied_penalty
        print(f"[DEBUG] Zastosowano karę za różne kategorie: -{applied_penalty:.1f}% (z {category_penalty}%)")
    
    # Normalizacja wyników do 0-100
    total_match = min(100, max(10, round(total_match, 1)))
    
    print(f"[DEBUG] Całkowite dopasowanie: {total_match}% (umiejętności: {skills_match:.1f}%, doświadczenie: {experience_match}%, dodatkowe: {additional_match}%)")
    
    return total_match

def analyze_interview_responses(responses, job_title):
    """
    Analizuje odpowiedzi z rozmowy kwalifikacyjnej, aby ocenić wydajność kandydata
    """
    # Przygotuj prompt dla AI
    prompt = f"""
    Here are all responses from a candidate during a job interview for {job_title} position:
    
    {' '.join([f'Response {i+1}: "{response}"' for i, response in enumerate(responses)])}
    
    Based on these responses, analyze the candidate's performance in the following format:
    
    1. Overall score (1-10)
    2. Confidence score (1-10)
    3. Positive attitude score (1-10)
    4. Expertise score (1-10)
    5. List of 3-5 candidate's strengths
    6. List of 3-5 areas to improve
    7. List of 3-5 tips for a real-life interview
    8. Emotion analysis (dominant emotions in the responses)
    
    Answer in JSON format with these keys: overall_score, confidence_score, positivity_score, expertise_score, strengths, areas_to_improve, irl_tips, emotion_analysis.
    For emotion_analysis, use a nested object with emotion_scores containing emotion names as keys and percentage scores (0-100) as values.
    
    IMPORTANT: Create this analysis in Polish language for all text fields.
    NEVER include <think> tags in your response.
    NEVER use Chinese characters in your response.
    """
    
    system_prompt = """You are an expert HR professional evaluating candidates in job interviews.
    Your analyses are professional, detailed, and constructive.
    Follow the instructions precisely and create the response in the exact format requested.
    Always respond in Polish for all text fields in the JSON.
    NEVER include <think> tags in your response.
    NEVER use Chinese or English in your response, only POLISH.
    """
    
    ai_analysis = get_ai_response(prompt, system_prompt)
    
    # Próba przetworzenia odpowiedzi jako JSON
    try:
        # Znajdź dane JSON w odpowiedzi
        json_match = re.search(r'\{[\s\S]*\}', ai_analysis)
        if json_match:
            json_data = json_match.group(0)
            analysis = json.loads(json_data)
            return analysis
    except json.JSONDecodeError:
        logger.error("Nie udało się przetworzyć analizy jako JSON")
        
    # Jeśli przetwarzanie JSON nie powiodło się, zwróć podstawową analizę
    return {
        "overall_score": 7,
        "confidence_score": 7,
        "positivity_score": 7,
        "expertise_score": 7,
        "strengths": ["Komunikatywność", "Zrozumienie technologii", "Przekazywanie informacji"],
        "areas_to_improve": ["Konkretne przykłady doświadczeń", "Podkreślanie osiągnięć"],
        "irl_tips": ["Utrzymuj kontakt wzrokowy", "Przygotuj pytania do rekrutera", "Ubieraj się stosownie"],
        "emotion_analysis": {
            "emotion_scores": {
                "entuzjazm": 80,
                "pewność": 70,
                "zaangażowanie": 75
            }
        }
    }

# Funkcje interakcji z bazą danych

def get_job_by_id(job_id):
    """Pobiera ofertę pracy po identyfikatorze"""
    if FIREBASE_ENABLED:
        doc_ref = db.collection('jobs').document(job_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    else:
        # Używamy lokalnych danych
        job = next((job for job in SAMPLE_JOBS if job.get('id') == job_id), None)
        return job
    return None

def save_interview(interview_data):
    """Zapisuje dane rozmowy w bazie danych"""
    interview_id = interview_data.get('id', str(uuid.uuid4()))
    interview_data['id'] = interview_id
    
    if FIREBASE_ENABLED:
        doc_ref = db.collection('interviews').document(interview_id)
        doc_ref.set(interview_data)
    else:
        # Zapisujemy lokalnie
        with open(f'data/interviews/{interview_id}.json', 'w', encoding='utf-8') as f:
            json.dump(interview_data, f, ensure_ascii=False, indent=2)
    
    return interview_id

def get_interview(interview_id):
    """Pobiera dane rozmowy z bazy danych"""
    if FIREBASE_ENABLED:
        doc_ref = db.collection('interviews').document(interview_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    else:
        # Pobieramy z lokalnego storage
        try:
            with open(f'data/interviews/{interview_id}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    return None

def update_interview(interview_id, update_data):
    """Aktualizuje dane rozmowy w bazie danych"""
    if FIREBASE_ENABLED:
        doc_ref = db.collection('interviews').document(interview_id)
        doc_ref.update(update_data)
    else:
        # Aktualizujemy lokalnie
        try:
            with open(f'data/interviews/{interview_id}.json', 'r', encoding='utf-8') as f:
                interview_data = json.load(f)
            
            # Aktualizuj dane
            interview_data.update(update_data)
            
            # Zapisz zaktualizowane dane
            with open(f'data/interviews/{interview_id}.json', 'w', encoding='utf-8') as f:
                json.dump(interview_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji rozmowy: {e}")
            return False
    
    return True

def save_cv_analysis(analysis_data):
    """Zapisuje analizę CV w bazie danych"""
    analysis_id = analysis_data.get('id', str(uuid.uuid4()))
    analysis_data['id'] = analysis_id
    analysis_data['created_at'] = datetime.now().isoformat()
    
    if FIREBASE_ENABLED:
        doc_ref = db.collection('cv_analyses').document(analysis_id)
        doc_ref.set(analysis_data)
    else:
        # Zapisujemy lokalnie
        with open(f'data/cv/{analysis_id}.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    return analysis_id

# Wymagane autentykacja dla ścieżek API (opcjonalne)
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sprawdź czy żądanie zawiera token uwierzytelniający
        auth_header = request.headers.get('Authorization')
        
        # W wersji deweloperskiej, pomijamy uwierzytelnianie
        if os.environ.get('ENVIRONMENT') == 'development':
            return f(*args, **kwargs)
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Brak autoryzacji"}), 401
        
        token = auth_header.split('Bearer ')[1]
        
        try:
            if FIREBASE_ENABLED:
                # Weryfikuj token przez Firebase Auth
                decoded_token = auth.verify_id_token(token)
                # Dodaj informacje o użytkowniku do żądania
                request.user = decoded_token
            else:
                # W trybie lokalnym sprawdzamy tylko czy token jest niepusty
                if not token:
                    return jsonify({"error": "Nieprawidłowy token"}), 401
                request.user = {"uid": "local_user"}
                
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Błąd uwierzytelniania: {e}")
            return jsonify({"error": "Nieprawidłowy token uwierzytelniający"}), 401
            
    return decorated_function

# Endpointy API

@app.route('/api/search', methods=['POST'])
def search_jobs():
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    job_keyword = data.get('job_keyword', '')
    profile_text = data.get('profile_text', '')
    
    print(f"[DEBUG] Otrzymano zapytanie o wyszukiwanie ofert:")
    print(f"[DEBUG] - Słowo kluczowe: {job_keyword}")
    print(f"[DEBUG] - Profil użytkownika: {profile_text[:100]}...")
    
    if not job_keyword or not profile_text:
        print("[DEBUG] Brak wymaganych pól (słowo kluczowe lub profil)")
        return jsonify({"error": "Brak wymaganych pól"}), 400
    
    try:
        # Wyodrębnij umiejętności i poziom doświadczenia z tekstu
        extracted_data = extract_skills_from_text(profile_text)
        skills = extracted_data.get('skills', [])
        experience = extracted_data.get('experience_level', 'junior')
        
        # Dodaj informację o wyodrębnionych umiejętnościach i poziomie doświadczenia
        print(f"[DEBUG] Wyodrębnione umiejętności: {skills}")
        print(f"[DEBUG] Poziom doświadczenia: {experience}")
        logger.info(f"Wyodrębnione umiejętności: {skills}")
        logger.info(f"Poziom doświadczenia: {experience}")
        
        # Jeśli nie znaleziono umiejętności, zwróć błąd
        if not skills:
            print("[DEBUG] Nie udało się wyodrębnić umiejętności z tekstu")
            return jsonify({
                "error": "Nie udało się wyodrębnić umiejętności z podanego tekstu",
                "suggestion": "Spróbuj podać więcej szczegółów na temat twoich umiejętności technicznych"
            }), 400
        
        # Pobierz oferty z bazy danych
        all_jobs = get_jobs(keyword=job_keyword)
        print(f"[DEBUG] Znaleziono {len(all_jobs)} ofert w bazie danych dla słowa kluczowego: {job_keyword}")
        
        # Sprawdź, czy pobrane oferty mają odpowiednią strukturę
        for i, job in enumerate(all_jobs[:5]):  # Loguj tylko pierwsze 5 ofert
            print(f"[DEBUG] Struktura oferty {i+1}: id={job.get('id')}, title={job.get('title')}")
            print(f"[DEBUG] - required_skills: {job.get('required_skills', 'BRAK')}")
            print(f"[DEBUG] - experience_level: {job.get('experience_level', 'BRAK')}")
        
        results = []
        for i, job in enumerate(all_jobs):
            try:
                # Sprawdź, czy oferta ma wszystkie wymagane pola
                if not isinstance(job, dict):
                    print(f"[DEBUG] Oferta {i+1} nie jest słownikiem: {type(job)}")
                    continue
                
                if not job.get('id') or not job.get('title'):
                    print(f"[DEBUG] Oferta {i+1} nie ma ID lub tytułu: {job}")
                    continue
                
            # Oblicz dopasowanie
            match_percentage = match_job_to_skills(job, skills, experience)
                print(f"[DEBUG] Oferta {i+1}: {job.get('title')} - Dopasowanie: {match_percentage}%")
            
            # Akceptuj oferty z dopasowaniem powyżej 30%
            if match_percentage >= 30:
                job_data = job.copy()
                job_data['match_percentage'] = match_percentage
                results.append(job_data)
            except Exception as job_error:
                print(f"[DEBUG] Błąd podczas przetwarzania oferty {i+1}: {job_error}")
                continue
        
        # Sortuj wyniki po procencie dopasowania (malejąco)
        results.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        print(f"[DEBUG] Znaleziono {len(results)} dopasowanych ofert z wynikiem powyżej 30%")
        
        return jsonify({
            "results": results,
            "extracted_skills": skills,
            "experience_level": experience
        })
        
    except Exception as e:
        print(f"[DEBUG] Błąd podczas wyszukiwania ofert: {e}")
        logger.error(f"Błąd podczas wyszukiwania ofert: {e}")
        import traceback
        print(f"[DEBUG] Szczegóły błędu: {traceback.format_exc()}")
        return jsonify({"error": f"Wystąpił błąd podczas wyszukiwania ofert: {str(e)}"}), 500

@app.route('/api/interview/start', methods=['POST'])
def start_interview():
    """
    Endpoint do rozpoczęcia rozmowy kwalifikacyjnej
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    job_id = data.get('job_id')
    profile_text = data.get('profile_text', '')
    
    if not job_id:
        return jsonify({"error": "Brak identyfikatora oferty pracy"}), 400
    
    try:
        # Pobierz dane oferty pracy
        job_data = get_job_by_id(job_id)
        
        if not job_data:
            return jsonify({"error": "Nie znaleziono oferty pracy"}), 404
        
        job_title = job_data.get('title', 'Nieznane stanowisko')
        
        # Wyodrębnij umiejętności i poziom doświadczenia z tekstu
        extracted_data = extract_skills_from_text(profile_text)
        user_skills = extracted_data.get('skills', [])
        experience_level = extracted_data.get('experience_level', 'junior')
        
        # Utwórz sesję rozmowy kwalifikacyjnej
        interview_id = f"interview_{int(time.time())}_{job_id}"
        
        # Przygotuj system prompt dla modelu AI
        system_prompt = create_safe_prompt_for_interview(job_title, user_skills, experience_level)
        
        # Pobierz odpowiedź od modelu AI
        ai_response = get_ai_response("Rozpocznij rozmowę kwalifikacyjną", system_prompt)
        
        # Zapisz sesję w bazie danych
        interview_data = {
            'id': interview_id,
            'job_id': job_id,
            'job_title': job_title,
            'user_skills': user_skills,
            'experience_level': experience_level,
            'profile_text': profile_text,
            'status': 'in_progress',
            'created_at': datetime.now().isoformat(),
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'assistant',
                    'content': ai_response
                }
            ],
            'user_responses': []
        }
        
        save_interview(interview_data)
        
        return jsonify({
            'interview_id': interview_id,
            'job_title': job_title,
            'message': ai_response,
            'extracted_skills': user_skills,
            'experience_level': experience_level,
            'thinking_message': 'JobMatchAI myśli...'  # Add this for frontend to use when starting
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas rozpoczynania rozmowy kwalifikacyjnej: {e}")
        return jsonify({"error": f"Wystąpił błąd podczas rozpoczynania rozmowy: {str(e)}"}), 500

@app.route('/api/interview/respond', methods=['POST'])
def respond_to_interview():
    """
    Endpoint do odpowiadania na pytania podczas rozmowy kwalifikacyjnej (przestarzały)
    Ten endpoint przekierowuje do stream_respond_to_interview dla kompatybilności
    """
    try:
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    interview_id = data.get('interview_id')
    user_response = data.get('response', '')
    
    if not interview_id or not user_response:
        return jsonify({"error": "Brak wymaganych pól"}), 400
        
        # Przekieruj do endpoint'u streamowego
        return Response(stream_respond_to_interview(), mimetype='application/json')
    
    except Exception as e:
        logger.error(f"Błąd w endpoincie respond_to_interview: {e}")
        return jsonify({"error": f"Wystąpił błąd: {str(e)}"}), 500

@app.route('/api/interview/stream-respond', methods=['POST'])
def stream_respond_to_interview():
    """
    Endpoint do streamowanego odpowiadania na pytania podczas rozmowy kwalifikacyjnej
    """
    def generate():
        try:
            data = request.json
            
            if not data:
                yield json.dumps({"status": "error", "error": "Brak danych wejściowych"})
                return
            
            interview_id = data.get('interview_id')
            user_response = data.get('response', '')
            
            if not interview_id or not user_response:
                yield json.dumps({"status": "error", "error": "Brak wymaganych pól"})
                return
    
    # Sprawdź, czy odpowiedź nie zawiera nieodpowiednich treści
    if filter_inappropriate_content(user_response):
                yield json.dumps({
                    "status": "error", 
            "error": "Twoja odpowiedź zawiera nieodpowiednie treści. Proszę skupić się na kontekście rozmowy kwalifikacyjnej."
                })
                return
    
        # Pobierz dane rozmowy
        interview_data = get_interview(interview_id)
        
        if not interview_data:
                yield json.dumps({"status": "error", "error": "Nie znaleziono rozmowy kwalifikacyjnej"})
                return
            
        if interview_data.get('status') == 'completed':
                yield json.dumps({"status": "error", "error": "Ta rozmowa kwalifikacyjna została już zakończona"})
                return
        
        # Dodaj odpowiedź użytkownika do kontekstu
        messages = interview_data.get('messages', [])
        user_responses = interview_data.get('user_responses', [])
        
        messages.append({
            'role': 'user',
            'content': user_response
        })
        
        user_responses.append(user_response)
        
            # Dodaj komunikat "JobMatchAI myśli..." przed rozpoczęciem generowania odpowiedzi
        yield json.dumps({
            'status': 'thinking',
                'message': 'JobMatchAI myśli...'
        })
        
        # Przygotuj kontekst dla modelu AI (bez wiadomości systemowej)
        context_messages = [msg for msg in messages if msg['role'] != 'system']
        
        # Pobierz system prompt
        system_prompt = next((msg['content'] for msg in messages if msg['role'] == 'system'), None)
        
        # Pobierz odpowiedź od modelu AI z włączoną opcją streamowania
        ai_response_stream = get_ai_response(user_response, system_prompt, context_messages, stream=True)
        
        # Bufor na kompletną odpowiedź
        complete_response = ""
        
        # Stream odpowiedzi AI
        for chunk in ai_response_stream:
            complete_response += chunk
            yield json.dumps({
                'status': 'in_progress',
                'message': complete_response
            })
        
        # Dodaj kompletną odpowiedź asystenta do kontekstu
        messages.append({
            'role': 'assistant',
            'content': complete_response
        })
        
        # Sprawdź, czy to koniec rozmowy
        is_interview_end = False
        if "koniec rozmowy" in complete_response.lower() or \
           "dziękuję za rozmowę" in complete_response.lower() or \
           "ocena twoich umiejętności" in complete_response.lower() or \
           "oceniam twoje umiejętności" in complete_response.lower() or \
           len(user_responses) >= 5:  # Minimum 5 wymian przed zakończeniem
            is_interview_end = True
            
        # Aktualizuj dane rozmowy
        interview_data['messages'] = messages
        interview_data['user_responses'] = user_responses
        
        response_data = {
            'status': 'completed',
            'message': complete_response
        }
        
        if is_interview_end:
            interview_data['status'] = 'completed'
            # Użyj AI do analizy odpowiedzi
            yield json.dumps({
                'status': 'analyzing',
                'message': 'Analizuję Twoje odpowiedzi...'
            })
            
            performance_analysis = analyze_interview_responses(user_responses, interview_data['job_title'])
            interview_data['performance_analysis'] = performance_analysis
            
            response_data['interview_completed'] = True
            response_data['performance_analysis'] = performance_analysis
        
        # Zapisz zaktualizowane dane
        update_interview(interview_id, interview_data)
        
        # Zwróć ostateczną odpowiedź
        yield json.dumps(response_data)
    
    except Exception as e:
        logger.error(f"Błąd podczas odpowiadania na pytanie: {e}")
            yield json.dumps({"status": "error", "error": f"Wystąpił błąd podczas odpowiadania na pytanie: {str(e)}"})
    
    return Response(generate(), mimetype='application/json')

@app.route('/api/interview/end', methods=['POST'])
def end_interview():
    """
    Endpoint do zakończenia rozmowy kwalifikacyjnej i uzyskania oceny
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    interview_id = data.get('interview_id')
    
    if not interview_id:
        return jsonify({"error": "Brak identyfikatora rozmowy"}), 400
    
    try:
        # Pobierz dane rozmowy kwalifikacyjnej
        interview_data = get_interview(interview_id)
        
        if not interview_data:
            return jsonify({"error": "Nie znaleziono rozmowy kwalifikacyjnej"}), 404
            
        if interview_data.get('status') == 'completed':
            # Jeśli rozmowa już zakończona, zwróć istniejącą analizę
            return jsonify({
                'performance_analysis': interview_data.get('performance_analysis', {})
            })
        
        # Przeanalizuj wyniki rozmowy za pomocą AI
        user_responses = interview_data.get('user_responses', [])
        performance_analysis = analyze_interview_responses(user_responses, interview_data.get('job_title', ''))
        
        # Aktualizuj dane rozmowy
        interview_data['status'] = 'completed'
        interview_data['performance_analysis'] = performance_analysis
        update_interview(interview_id, interview_data)
        
        return jsonify({
            'performance_analysis': performance_analysis
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas kończenia rozmowy: {e}")
        return jsonify({"error": f"Wystąpił błąd podczas kończenia rozmowy: {str(e)}"}), 500

@app.route('/api/cv/analyze', methods=['POST'])
def analyze_cv():
    """
    Endpoint do analizy CV użytkownika i optymalizacji pod kątem ATS
    """
    if 'cv_file' not in request.files:
        return jsonify({"error": "Brak pliku CV"}), 400
    
    cv_file = request.files['cv_file']
    job_id = request.form.get('job_id')
    profile_text = request.form.get('profile_text', '')
    
    if not job_id:
        return jsonify({"error": "Brak identyfikatora oferty pracy"}), 400
    
    try:
        # Pobierz dane oferty pracy
        job_data = get_job_by_id(job_id)
        
        if not job_data:
            return jsonify({"error": "Nie znaleziono oferty pracy"}), 404
        
        # Odczytaj zawartość CV
        cv_content = cv_file.read().decode('utf-8', errors='ignore')
        
        # Wyodrębnij umiejętności z opisu profilu, jeśli podano
        extracted_data = {"skills": [], "experience_level": "junior"}
        if profile_text:
            extracted_data = extract_skills_from_text(profile_text)
        
        # Zapisz plik CV w Firebase Storage (lub lokalnie)
        cv_filename = f"cv_{int(time.time())}_{job_id}.txt"
        
        if FIREBASE_ENABLED:
            blob = bucket.blob(f"cv/{cv_filename}")
            blob.upload_from_string(cv_content)
            cv_url = blob.public_url
        else:
            # Zapisz lokalnie
            with open(f"data/cv/{cv_filename}", "w", encoding="utf-8") as f:
                f.write(cv_content)
            cv_url = f"/data/cv/{cv_filename}"
        
        # Analizuj CV za pomocą modelu AI
        prompt = f"""
        Analyze the following CV for the job position: {job_data.get('title')}
        
        Job description:
        {job_data.get('description')}
        
        Required skills:
        {', '.join(job_data.get('required_skills', []))}
        
        Experience level: {job_data.get('experience_level', 'junior')}
        
        User profile description:
        {profile_text}
        
        CV to analyze:
        {cv_content}
        
        Perform analysis in the following format:
        1. Skills match percentage (0-100)
        2. List of found skills matching the job offer
        3. List of missing skills
        4. Experience match percentage (0-100)
        5. CV structure score (0-100)
        6. Suggestions for improving CV structure
        7. Suggestions for ATS optimization
        
        Answer in JSON format and ensure ALL text fields are in Polish.
        """
        
        # Użyj modelu AI do analizy CV
        system_prompt = """You are an HR expert analyzing candidate CVs for job offers.
        Your analyses are professional, detailed, and constructive.
        Remember to provide all textual responses in Polish language.
        """
        
        ai_response = get_ai_response(prompt, system_prompt)
        
        # Próba przetworzenia odpowiedzi jako JSON
        try:
            # Znajdź dane JSON w odpowiedzi
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_data = json_match.group(0)
                cv_analysis = json.loads(json_data)
                
                # Dodaj metadane analizy
                cv_analysis['job_id'] = job_id
                cv_analysis['job_title'] = job_data.get('title')
                cv_analysis['cv_url'] = cv_url
                cv_analysis['extracted_skills'] = extracted_data.get('skills', [])
                cv_analysis['experience_level'] = extracted_data.get('experience_level', 'junior')
                
                # Zapisz analizę w bazie danych
                analysis_id = save_cv_analysis(cv_analysis)
                cv_analysis['id'] = analysis_id
                
                return jsonify(cv_analysis)
            else:
                # Jeśli nie znaleziono JSON, przygotuj zamiast tego analizę w postaci strukturyzowanej
                prompt_structured = f"""
                Analyze the CV for the job position: {job_data.get('title')}. 
                Provide the analysis in the following structured format:
                
                Overall match percentage (0-100): 
                Skills match percentage (0-100):
                Found skills (list separated by commas):
                Missing skills (list separated by commas):
                Experience match percentage (0-100):
                CV structure score (0-100):
                Structure improvement suggestions (list):
                ATS optimization suggestions (list):
                
                Remember to respond in Polish language for all fields.
                """
                
                structured_response = get_ai_response(prompt_structured, system_prompt)
                
                # Sparsuj strukturyzowaną odpowiedź
                overall_match = re.search(r'Overall match percentage.*?(\d+)', structured_response)
                skills_match = re.search(r'Skills match percentage.*?(\d+)', structured_response)
                skills_found = re.search(r'Found skills.*?:(.*?)(?=Missing skills)', structured_response, re.DOTALL)
                skills_missing = re.search(r'Missing skills.*?:(.*?)(?=Experience match)', structured_response, re.DOTALL)
                experience_match = re.search(r'Experience match percentage.*?(\d+)', structured_response)
                structure_score = re.search(r'CV structure score.*?(\d+)', structured_response)
                structure_suggestions = re.search(r'Structure improvement suggestions.*?:(.*?)(?=ATS optimization)', structured_response, re.DOTALL)
                ats_suggestions = re.search(r'ATS optimization suggestions.*?:(.*?)$', structured_response, re.DOTALL)
                
                # Przygotuj odpowiedź
                cv_analysis = {
                    "overall_match_percentage": int(overall_match.group(1)) if overall_match else 50,
                    "skills_match_percentage": int(skills_match.group(1)) if skills_match else 50,
                    "skills_found": [s.strip() for s in skills_found.group(1).split(',')] if skills_found else ["Brak danych"],
                    "skills_missing": [s.strip() for s in skills_missing.group(1).split(',')] if skills_missing else ["Brak danych"],
                    "experience_match_percentage": int(experience_match.group(1)) if experience_match else 50,
                    "cv_structure_score": int(structure_score.group(1)) if structure_score else 50,
                    "structure_suggestions": [s.strip() for s in structure_suggestions.group(1).replace('-', '').split('\n') if s.strip()] if structure_suggestions else ["Brak sugestii"],
                    "ats_optimization_suggestions": [s.strip() for s in ats_suggestions.group(1).replace('-', '').split('\n') if s.strip()] if ats_suggestions else ["Brak sugestii"],
                    "job_id": job_id,
                    "job_title": job_data.get('title'),
                    "cv_url": cv_url,
                    "extracted_skills": extracted_data.get('skills', []),
                    "experience_level": extracted_data.get('experience_level', 'junior')
                }
                
                # Zapisz analizę w bazie danych
                analysis_id = save_cv_analysis(cv_analysis)
                cv_analysis['id'] = analysis_id
                
                return jsonify(cv_analysis)
                
        except json.JSONDecodeError:
            logger.error("Błąd dekodowania JSON z odpowiedzi AI")
            
            # W przypadku błędu dekodowania, zwróć podstawową odpowiedź
            cv_analysis = {
                "overall_match_percentage": 50,
                "skills_match_percentage": 50,
                "skills_found": ["Brak danych - błąd analizy"],
                "skills_missing": ["Brak danych - błąd analizy"],
                "experience_match_percentage": 50,
                "cv_structure_score": 50,
                "structure_suggestions": ["Przeprowadź profesjonalną analizę CV"],
                "ats_optimization_suggestions": ["Dodaj słowa kluczowe związane z ofertą pracy"],
                "job_id": job_id,
                "job_title": job_data.get('title'),
                "cv_url": cv_url,
                "extracted_skills": extracted_data.get('skills', []),
                "experience_level": extracted_data.get('experience_level', 'junior')
            }
            
            analysis_id = save_cv_analysis(cv_analysis)
            cv_analysis['id'] = analysis_id
            
            return jsonify(cv_analysis)
        
    except Exception as e:
        logger.error(f"Błąd podczas analizy CV: {e}")
        return jsonify({"error": f"Wystąpił błąd podczas analizy CV: {str(e)}"}), 500

@app.route('/api/model/health', methods=['GET'])
def check_models_health():
    """
    Endpoint do sprawdzenia stanu serwerów Ollama
    """
    # Wymuś sprawdzenie stanu serwera
    server_status = check_ai_server_health(force_check=True)
    
    # Sprawdź wszystkie serwery
    all_servers_status = []
    
    for server_url in OLLAMA_SERVERS:
        try:
            start_time = time.time()
            response = requests.get(f"{server_url}/api/tags", timeout=3)
            ping_time = time.time() - start_time
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model.get("name") for model in models]
                
                all_servers_status.append({
                    "server": server_url,
                    "status": "online",
                    "response_time": round(ping_time, 3),
                    "available_models": available_models,
                    "last_checked": time.time()
                })
            else:
                all_servers_status.append({
                    "server": server_url,
                    "status": "error",
                    "error": f"HTTP Error: {response.status_code}",
                    "response_time": round(ping_time, 3),
                    "available_models": [],
                    "last_checked": time.time()
                })
        except Exception as e:
            all_servers_status.append({
                "server": server_url,
                "status": "offline",
                "error": str(e),
                "response_time": 0,
                "available_models": [],
                "last_checked": time.time()
            })
    
    # Oblicz statystyki
    online_servers = sum(1 for s in all_servers_status if s["status"] == "online")
    
    return jsonify({
        "current_server": server_status['current_server'],
        "current_server_status": server_status,
        "servers": all_servers_status,
        "online_servers": online_servers,
        "total_servers": len(OLLAMA_SERVERS),
        "availability_percentage": round((online_servers / len(OLLAMA_SERVERS)) * 100, 1),
        "timestamp": time.time()
    })

@app.route('/api/interview/generate_questions', methods=['POST'])
def generate_interview_questions():
    """
    Generuje unikalne pytania do rozmowy kwalifikacyjnej na podstawie oferty pracy i poziomu trudności
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    job_id = data.get('job_id')
    difficulty = data.get('difficulty', 'medium')  # easy, medium, hard
    profile_text = data.get('profile_text', '')
    
    if not job_id:
        return jsonify({"error": "Brak identyfikatora oferty pracy"}), 400
    
    try:
        # Pobierz dane oferty pracy
        job_data = get_job_by_id(job_id)
        
        if not job_data:
            return jsonify({"error": "Nie znaleziono oferty pracy"}), 404
        
        # Wyodrębnij umiejętności z opisu profilu, jeśli podano
        extracted_data = {"skills": [], "experience_level": "junior"}
        if profile_text:
            extracted_data = extract_skills_from_text(profile_text)
        
        # Przygotuj prompt dla modelu AI
        system_prompt = """You are an experienced technical recruiter. Your task is to generate interview questions
        that are unique, practical, and test the candidate's real knowledge, not just ability to
        reproduce knowledge from the internet. Generate questions in JSON list format.
        All questions text should be in Polish language."""
        
        prompt = f"""
        Generate 10 unique job interview questions for the position: {job_data.get('title')}
        
        Position information:
        - Description: {job_data.get('description')}
        - Required skills: {', '.join(job_data.get('required_skills', []))}
        - Experience level: {job_data.get('experience_level', 'junior')}
        - Question difficulty level: {difficulty}
        
        Candidate information:
        - Skills: {', '.join(extracted_data.get('skills', []))}
        - Experience level: {extracted_data.get('experience_level', 'junior')}
        - Profile description: {profile_text[:200] + '...' if len(profile_text) > 200 else profile_text}
        
        Generate questions that:
        1. Include practical problems instead of theoretical ones
        2. Test real understanding of technologies, not just knowledge of definitions
        3. Require critical thinking and problem solving
        4. Allow assessing candidate's experience with technologies
        5. May include tricky elements appropriate for the position level
        6. Focus on skills that match between required job skills and candidate skills
        
        Return questions in JSON format, where each question has fields:
        - question: the question text
        - category: question category (e.g. technical, behavioral, problem-solving)
        - purpose: purpose of the question (what we want to test)
        
        Remember that all question texts, category names and purposes should be in Polish language.
        Answer only in JSON format.
        """
        
        # Pobierz odpowiedź od modelu AI
        ai_response = get_ai_response(prompt, system_prompt)
        
        # Próba przetworzenia odpowiedzi jako JSON
        try:
            # Znajdź dane JSON w odpowiedzi
            json_match = re.search(r'\[[\s\S]*\]', ai_response)
            if json_match:
                json_data = json_match.group(0)
                questions = json.loads(json_data)
                return jsonify({
                    "questions": questions,
                    "extracted_skills": extracted_data.get('skills', []),
                    "experience_level": extracted_data.get('experience_level', 'junior')
                })
            else:
                # Jeśli nie znaleziono JSON, zwróć surową odpowiedź
                return jsonify({
                    "error": "Nie udało się przetworzyć odpowiedzi jako JSON",
                    "raw_response": ai_response
                })
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania JSON z odpowiedzi AI: {e}")
            return jsonify({
                "error": "Nie udało się przetworzyć odpowiedzi jako JSON",
                "raw_response": ai_response
            })
    
    except Exception as e:
        logger.error(f"Błąd podczas generowania pytań: {e}")
        return jsonify({"error": f"Wystąpił błąd podczas generowania pytań: {str(e)}"}), 500

@app.route('/api/ai/thinking-status')
def ai_thinking_status():
    """
    Endpoint sprawdzający czy AI jest dostępne i działa
    """
    status = check_ai_server_health()
    return jsonify({
        "is_available": status['is_online'],
        "current_server": status['current_server'],
        "response_time": status['ping_time'],
        "thinking_message": "JobMatchAI myśli..."
    })

@app.route('/api/match-jobs', methods=['GET', 'POST'])
def match_jobs_with_ai():
    """
    Endpoint dopasowujący oferty pracy bezpośrednio do tekstu wprowadzonego przez użytkownika
    za pomocą AI, bez wyodrębniania umiejętności.
    
    Przyjmuje dane zarówno w formacie GET (query parameters) jak i POST (JSON w body).
    
    Query params / JSON fields:
    - profile_text: Opis profilu użytkownika, doświadczenia, umiejętności, itd.
    - job_keyword: (opcjonalne) Słowo kluczowe do filtrowania ofert
    - limit: (opcjonalne) Maksymalna liczba zwracanych ofert (domyślnie 10)
    
    Returns:
        JSON z listą dopasowanych ofert pracy wraz z procentem dopasowania
    """
    # Logowanie rozpoczęcia zapytania
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[MATCH-JOBS:{request_id}] Rozpoczęto nowe zapytanie")
    
    # Obsługa danych z GET lub POST
    if request.method == 'POST':
        data = request.json or {}
    else:  # GET
        data = request.args.to_dict()
    
    profile_text = data.get('profile_text', '')
    job_keyword = data.get('job_keyword', '')
    limit = int(data.get('limit', 10))
    
    if not profile_text:
        logger.warning(f"[MATCH-JOBS:{request_id}] Brak profilu użytkownika w zapytaniu")
        return jsonify({"error": "Brak opisu profilu użytkownika (profile_text)"}), 400
    
    # Walidacja profilu - zbyt krótki tekst może powodować problemy
    if len(profile_text) < 10:
        logger.warning(f"[MATCH-JOBS:{request_id}] Profil użytkownika zbyt krótki: {len(profile_text)} znaków")
        return jsonify({"error": "Profil użytkownika jest zbyt krótki. Proszę podać więcej informacji."}), 400
        
    try:
        # Debugowanie - sprawdź parametry wejściowe
        logger.info(f"[MATCH-JOBS:{request_id}] Wyszukiwanie dla: keyword='{job_keyword}', profile_length={len(profile_text)}")
        
        # WAŻNE: Nie używamy filtru keyword w get_jobs, aby AI mogło dopasować wszystko
        # Pobierz WSZYSTKIE oferty z bazy danych bez filtrowania
        all_jobs = get_jobs()
        
        if not all_jobs:
            logger.warning("[MATCH-JOBS] Nie znaleziono żadnych ofert w bazie danych")
            return jsonify({
                "message": "Nie znaleziono żadnych ofert pracy w bazie danych",
                "matches": []
            })
        
        logger.info(f"[MATCH-JOBS] Znaleziono {len(all_jobs)} ofert pracy w bazie danych")
        
        # Przekształć słowo kluczowe na formę do dopasowania przez AI
        # Dodaj synonimy i tłumaczenia popularnych zawodów
        job_keyword_context = ""
        if job_keyword:
            # Dodaj kontekst dla słowa kluczowego
            job_synonyms = {
                "szef kuchni": ["chef", "cook", "head chef", "kucharz"],
                "kucharz": ["chef", "cook", "culinary"],
                "kierowca": ["driver", "chauffeur"],
                "programista": ["developer", "software engineer", "coder", "programmer"],
                "nauczyciel": ["teacher", "educator", "instructor"],
                "opiekunka": ["caregiver", "nanny", "babysitter"],
                "sprzedawca": ["sales", "salesman", "retail associate"],
                "mechanik": ["mechanic", "technician"]
            }
            
            # Znajdź synonimy dla słowa kluczowego (case-insensitive)
            job_keyword_lower = job_keyword.lower()
            synonyms = []
            
            # Sprawdź, czy słowo kluczowe ma synonimy
            for key, values in job_synonyms.items():
                if job_keyword_lower in key or any(job_keyword_lower in value.lower() for value in values):
                    synonyms.extend(values)
                    synonyms.append(key)
            
            # Usuń duplikaty i dodaj kontekst
            synonyms = list(set(synonyms))
            if synonyms:
                job_keyword_context = f"Użytkownik szuka pracy jako '{job_keyword}', co może oznaczać również: {', '.join(synonyms)}"
            else:
                job_keyword_context = f"Użytkownik szuka pracy jako '{job_keyword}'"
            
            logger.info(f"[MATCH-JOBS] Kontekst słowa kluczowego: {job_keyword_context}")
        
        # Ogranicz liczbę ofert do analizy przez AI (aby nie przeciążyć modelu)
        # UWAGA: Pobieramy więcej ofert, nawet do 30, aby zwiększyć szansę znalezienia dopasowania
        max_jobs_to_analyze = min(30, len(all_jobs))
        jobs_to_analyze = all_jobs[:max_jobs_to_analyze]
        
        # Debugowanie - wypisz pierwsze kilka ofert
        for i, job in enumerate(jobs_to_analyze[:5]):
            logger.info(f"[MATCH-JOBS] Oferta {i}: ID={job.get('id')}, tytuł={job.get('title')}, firma={job.get('company')}")
        
        # Przygotuj dane ofert w formacie odpowiednim do analizy przez AI
        jobs_data = []
        for i, job in enumerate(jobs_to_analyze):
            job_summary = {
                "id": job.get("id"),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "description": job.get("description", ""),
                "required_skills": ", ".join(job.get("required_skills", [])),
                "experience_level": job.get("experience_level", ""),
                "index": i  # Pozycja w oryginalnej liście
            }
            jobs_data.append(job_summary)
        
        # Przygotuj prompt dla modelu AI
        system_prompt = """Jesteś zaawansowanym systemem dopasowującym kandydatów do ofert pracy.
        Twoim zadaniem jest przeanalizować profil kandydata i znaleźć najlepiej pasujące oferty pracy.
        
        BARDZO WAŻNE:
        1. Zwracaj uwagę na semantyczne znaczenie, nie tylko dokładne dopasowania słów
        2. Uwzględniaj synonimy i różne terminy (np. 'programista' = 'developer')
        3. Obsługuj opisy w różnych językach (głównie polski i angielski)
        4. Gdy kandydat wspomina konkretną firmę, ZAWSZE uwzględnij oferty z tej firmy
        5. Dopasowuj termin "Szef Kuchni" (polski) do "Chef" (angielski) i podobne wielojęzyczne odpowiedniki
        
        Analizując dopasowanie, weź pod uwagę następujące czynniki:
        1. Umiejętności wymienione w profilu kandydata vs. wymagane w ofercie
        2. Doświadczenie zawodowe - ilość lat, rodzaj stanowisk
        3. Zainteresowanie konkretną firmą lub branżą
        4. Wszystkie sygnały świadczące o dopasowaniu, nawet jeśli nie są wprost wymienione
        
        NAJWAŻNIEJSZE: Jeśli kandydat wymienia NAZWĘ FIRMY która występuje w ofercie, ZAWSZE zwróć tę ofertę z wysokim dopasowaniem (min. 80%).
        
        Obowiązkowo uwzględniaj tłumaczenia między językami, np.:
        - Szef Kuchni (PL) = Chef (EN)
        - Kucharz (PL) = Chef, Cook (EN)
        - Programista (PL) = Developer, Software Engineer (EN)
        - Nauczyciel (PL) = Teacher (EN)
        - Kierowca (PL) = Driver (EN)
        
        Wynik podaj w formacie JSON z kluczami: job_id oraz match_percentage (0-100).
        """
        
        jobs_text = "\n\n".join([
            f"Oferta {i+1}:\nID: {job['id']}\nTytuł: {job['title']}\nFirma: {job['company']}\nOpis: {job['description']}\n" +
            f"Wymagane umiejętności: {job['required_skills']}\nPoziom doświadczenia: {job['experience_level']}"
            for i, job in enumerate(jobs_data)
        ])
        
        prompt = f"""
        Dopasuj profil kandydata do następujących ofert pracy. Zwróć wyniki jako tablicę obiektów JSON, gdzie każdy obiekt zawiera:
        - "job_id": ID oferty pracy
        - "match_percentage": Procent dopasowania (od 0 do 100)
        
        Profil kandydata:
        {profile_text}
        
        {job_keyword_context}
        
        Dostępne oferty pracy:
        {jobs_text}
        
        Wykonaj szczegółową analizę dopasowania z następującymi priorytetami:
        1. NAJWYŻSZY PRIORYTET: Jeśli kandydat wspomina konkretną firmę z listy ofert - zwróć wszystkie oferty tej firmy z wysokim dopasowaniem (min. 80%)
        2. WYSOKI PRIORYTET: Dopasowanie między słowami kluczowymi (np. "Kucharz" / "Szef Kuchni") a tytułem oferty (np. "Chef")
        3. Semantyczne dopasowanie między profilem kandydata a opisem oferty
        
        Jeśli znajdziesz dopasowanie między słowami kluczowymi (np. "Kucharz" / "Szef Kuchni") a tytułem oferty (np. "Chef"),
        nawet jeśli są w różnych językach, przyznaj wysoki procent dopasowania (minimum 70%).
        
        Zwróć wyniki TYLKO w formacie JSON jako tablica obiektów:
        [
          {{"job_id": "id_oferty_1", "match_percentage": 85}},
          {{"job_id": "id_oferty_2", "match_percentage": 70}},
          ...
        ]
        """
        
        # Pobierz odpowiedź od modelu AI
        logger.info("[MATCH-JOBS] Wysyłam zapytanie do AI")
        ai_response = get_ai_response(prompt, system_prompt)
        logger.debug(f"[MATCH-JOBS] Otrzymano odpowiedź od AI: {ai_response[:200]}...")
        
        # Próba przetworzenia odpowiedzi jako JSON
        try:
            # Spróbuj najpierw znaleźć tablicę JSON w odpowiedzi
            json_match = re.search(r'\[[\s\S]*?\]', ai_response)
            
            # Jeśli nie znaleziono, sprawdź, czy w ogóle jest jakiś JSON
            if not json_match:
                json_match = re.search(r'\{[\s\S]*?\}', ai_response)
                
                # Jeśli znaleziono pojedynczy obiekt JSON, opakuj go w tablicę
                if json_match:
                    json_data = "[" + json_match.group(0) + "]"
                else:
                    # Ostatnia próba - wyciągnij cokolwiek, co wygląda jak JSON
                    possible_json = re.findall(r'\{[^{}]*"job_id"[^{}]*"match_percentage"[^{}]*\}', ai_response)
                    if possible_json:
                        json_data = "[" + ",".join(possible_json) + "]"
                    else:
                        raise ValueError("Nie znaleziono odpowiedzi JSON w formacie tablicy ani obiektu")
            else:
                json_data = json_match.group(0)
                
            # Usuń ewentualne dodatkowe znaki, które mogą zakłócać JSON
            json_data = re.sub(r'```json|```', '', json_data)
            json_data = json_data.strip()
            
            logger.info(f"[MATCH-JOBS] Wyodrębniony JSON: {json_data[:200]}...")
            matches_data = json.loads(json_data)
            
            # Weryfikacja formatu dopasowań
            if not isinstance(matches_data, list):
                raise ValueError("Odpowiedź AI nie zawiera tablicy dopasowań")
            
            # Mapuj wyniki dopasowania do pełnych danych ofert
            job_id_map = {job.get('id'): job for job in all_jobs}
            
            matches = []
            for match in matches_data:
                job_id = match.get('job_id')
                match_percentage = match.get('match_percentage', 0)
                
                if job_id in job_id_map:
                    job_data = job_id_map[job_id].copy()
                    job_data['match_percentage'] = match_percentage
                    matches.append(job_data)
                    logger.info(f"[MATCH-JOBS] Dopasowano ofertę: {job_id} - {job_data.get('title')} ({match_percentage}%)")
                else:
                    logger.warning(f"[MATCH-JOBS] Nie znaleziono oferty o ID: {job_id}")
            
            # Jeśli podano słowo kluczowe, ale nie znaleziono dopasowań,
            # spróbuj bardziej ogólnego podejścia
            if job_keyword and (not matches or len(matches) < 2):
                logger.warning(f"[MATCH-JOBS] Znaleziono tylko {len(matches)} dopasowań dla słowa '{job_keyword}', próbuję dodatkowych metod")
                
                # 1. Sprawdź, czy w profilu kandydata wymieniona jest konkretna firma
                mentioned_companies = []
                for job in all_jobs:
                    company_name = job.get('company', '').lower()
                    if company_name and len(company_name) > 3 and company_name in profile_text.lower():
                        mentioned_companies.append(job.get('id'))
                        # Jeśli firma jest wymieniona, ale oferta nie została dopasowana, dodaj ją
                        if job.get('id') not in [m.get('id') for m in matches]:
                            logger.info(f"[MATCH-JOBS] Znaleziono wzmiankę o firmie '{company_name}' w profilu")
                            job_data = job.copy()
                            job_data['match_percentage'] = 85  # Wysoki priorytet dla ofert z wymienioną firmą
                            matches.append(job_data)
                
                # 2. Bezpośrednie dopasowanie tytułu stanowiska
                for job in all_jobs:
                    if job.get('id') not in [m.get('id') for m in matches]:
                        # Sprawdź czy tytuł stanowiska pasuje do słowa kluczowego bezpośrednio lub przez synonimy
                        job_title = job.get('title', '').lower()
                        
                        # Wyszukiwanie wśród synonimów
                        if job_keyword.lower() in job_title or job_title in job_keyword.lower():
                            logger.info(f"[MATCH-JOBS] Bezpośrednie dopasowanie tytułu: '{job_title}' dla '{job_keyword}'")
                            job_data = job.copy()
                            job_data['match_percentage'] = 75
                            matches.append(job_data)
                            continue
                        
                        # Sprawdź synonimy
                        if job_keyword.lower() in job_synonyms:
                            synonyms = job_synonyms[job_keyword.lower()]
                            for synonym in synonyms:
                                if synonym.lower() in job_title or job_title in synonym.lower():
                                    logger.info(f"[MATCH-JOBS] Dopasowanie przez synonim: '{job_title}' dla '{job_keyword}' poprzez '{synonym}'")
                                    job_data = job.copy()
                                    job_data['match_percentage'] = 70
                                    matches.append(job_data)
                                    break
                
                # 3. Jeśli nadal brak dopasowań, przygotuj dodatkowy prompt dla AI
                if not matches:
                    logger.warning(f"[MATCH-JOBS] Nie znaleziono dopasowań dla słowa '{job_keyword}', próbuję szerszego wyszukiwania")
                    
                    broader_prompt = f"""
                    Kandydat szuka pracy jako '{job_keyword}'. 
                    
                    Przeanalizuj poniższe oferty pracy i zwróć ID tych, które mogą być odpowiednie dla kogoś szukającego pracy jako '{job_keyword}',
                    nawet jeśli tytuł stanowiska jest nieco inny lub w innym języku (np. 'kucharz' vs 'chef').
                    
                    Dostępne oferty pracy:
                    {jobs_text}
                    
                    Zwróć wyniki jako listę obiektów JSON:
                    [
                      {{"job_id": "id_oferty_1", "match_percentage": 75}},
                      {{"job_id": "id_oferty_2", "match_percentage": 60}}
                    ]
                    
                    Uwzględnij synonimy i tłumaczenia między językami.
                    """
                    
                    # Pobierz odpowiedź dla szerszego wyszukiwania
                    broader_response = get_ai_response(broader_prompt, system_prompt)
                    
                    # Próba przetworzenia szerszej odpowiedzi
                    broader_json_match = re.search(r'\[[\s\S]*?\]', broader_response)
                    if broader_json_match:
                        broader_json_data = broader_json_match.group(0)
                        broader_json_data = re.sub(r'```json|```', '', broader_json_data).strip()
                        broader_matches = json.loads(broader_json_data)
                        
                        for match in broader_matches:
                            job_id = match.get('job_id')
                            match_percentage = match.get('match_percentage', 0)
                            
                            if job_id in job_id_map and job_id not in [m.get('id') for m in matches]:
                                job_data = job_id_map[job_id].copy()
                                job_data['match_percentage'] = match_percentage
                                matches.append(job_data)
                                logger.info(f"[MATCH-JOBS] Dodatkowe dopasowanie: {job_id} - {job_data.get('title')} ({match_percentage}%)")
            
            # Sortuj według procentu dopasowania (malejąco)
            matches.sort(key=lambda x: x.get('match_percentage', 0), reverse=True)
            
            # Filtruj wyniki z niskim procentem dopasowania (usuń oferty poniżej 30%)
            matches = [match for match in matches if match.get('match_percentage', 0) >= 30]
            
            # Ogranicz liczbę wyników
            matches = matches[:limit]
            
            return jsonify({
                "matches": matches,
                "total_matches": len(matches),
                "message": f"Znaleziono {len(matches)} dopasowanych ofert"
            })
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[MATCH-JOBS:{request_id}] Błąd przetwarzania odpowiedzi AI: {e}")
            logger.error(f"[MATCH-JOBS:{request_id}] Surowa odpowiedź: {ai_response}")
            
            # Dodajmy awaryjny mechanizm wyszukiwania oparty na prostym dopasowaniu słów kluczowych
            try:
                emergency_matches = []
                profile_lower = profile_text.lower()
                keyword_lower = job_keyword.lower() if job_keyword else ""
                
                # Awaryjne dopasowanie na podstawie firmy i słów kluczowych
                for job in all_jobs:
                    match_score = 0
                    company = job.get('company', '').lower()
                    title = job.get('title', '').lower()
                    
                    # Sprawdź czy firma jest wymieniona
                    if company and len(company) > 3 and company in profile_lower:
                        match_score += 50
                        logger.info(f"[MATCH-JOBS:{request_id}] Awaryjne dopasowanie firmy: {company}")
                    
                    # Sprawdź tytuł stanowiska
                    if keyword_lower and keyword_lower in title:
                        match_score += 40
                        logger.info(f"[MATCH-JOBS:{request_id}] Awaryjne dopasowanie tytułu: {title}")
                    
                    # Sprawdź czy wymagane umiejętności występują w profilu
                    for skill in job.get('required_skills', []):
                        if skill.lower() in profile_lower:
                            match_score += 5
                    
                    # Dodaj ofertę jeśli ma wystarczająco wysoki wynik
                    if match_score > 30:
                        job_data = job.copy()
                        job_data['match_percentage'] = min(95, match_score)
                        emergency_matches.append(job_data)
                
                # Posortuj i zwróć wyniki awaryjne
                if emergency_matches:
                    emergency_matches.sort(key=lambda x: x.get('match_percentage', 0), reverse=True)
                    emergency_matches = emergency_matches[:limit]
                    
                    logger.info(f"[MATCH-JOBS:{request_id}] Zwracam {len(emergency_matches)} awaryjnie dopasowanych ofert")
                    return jsonify({
                        "matches": emergency_matches,
                        "total_matches": len(emergency_matches),
                        "message": f"Znaleziono {len(emergency_matches)} dopasowanych ofert (tryb awaryjny)"
                    })
            except Exception as emergency_error:
                logger.error(f"[MATCH-JOBS:{request_id}] Błąd w awaryjnym dopasowaniu: {emergency_error}")
            
            # Jeśli wszystko zawiedzie, zwróć błąd
            return jsonify({
                "error": f"Błąd przetwarzania odpowiedzi AI: {str(e)}",
                "raw_response": ai_response[:300] if ai_response else "Brak odpowiedzi"
            }), 500
    
    except Exception as e:
        logger.error(f"[MATCH-JOBS:{request_id}] Błąd podczas dopasowywania ofert: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Wystąpił błąd podczas dopasowywania ofert: {str(e)}"}), 500

@app.route('/api/jobs/create', methods=['POST'])
@auth_required
def create_job():
    """
    Endpoint do tworzenia nowej oferty pracy (wymaga uwierzytelnienia)
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Brak danych wejściowych"}), 400
    
    required_fields = ['title', 'company', 'description', 'required_skills']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "error": f"Brak wymaganych pól: {', '.join(missing_fields)}"
        }), 400
    
    try:
        
        job_id = f"job_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Przygotuj dane oferty
        job_data = {
            'id': job_id,
            'title': data.get('title'),
            'company': data.get('company'),
            'location': data.get('location', 'Zdalna'),
            'description': data.get('description'),
            'required_skills': data.get('required_skills', []),
            'experience_level': data.get('experience_level', 'junior'),
            'salary_range': data.get('salary_range', 'Nieujawnione'),
            'employment_type': data.get('employment_type', 'Umowa o pracę'),
            'remote': data.get('remote', True),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Zapisz ofertę w bazie danych
        if FIREBASE_ENABLED:
            db.collection('jobs').document(job_id).set(job_data)
        else:
            # Zapisz lokalnie
            with open(f'data/jobs/{job_id}.json', 'w', encoding='utf-8') as f:
                json.dump(job_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Oferta pracy została utworzona"
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia oferty pracy: {e}")
        return jsonify({"error": f"Wystąpił błąd podczas tworzenia oferty pracy: {str(e)}"}), 500

# Serwowanie plików statycznych (HTML, CSS, JS)
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/cv/find-jobs', methods=['POST'])
def find_jobs_from_cv():
    """
    Endpoint do wyszukiwania ofert pracy na podstawie przesłanego CV
    """
    if 'cv_file' not in request.files:
        return jsonify({"error": "Brak pliku CV"}), 400
    
    cv_file = request.files['cv_file']
    job_keyword = request.form.get('job_keyword', '')
    limit = int(request.form.get('limit', 10))
    
    try:
        # Odczytaj zawartość CV
        cv_content = cv_file.read().decode('utf-8', errors='ignore')
        
        if not cv_content or len(cv_content) < 10:
            return jsonify({"error": "Plik CV jest pusty lub zbyt krótki"}), 400
        
        logger.info(f"Rozpoczynam wyszukiwanie ofert na podstawie CV, długość tekstu: {len(cv_content)}")
        
        # Wyodrębnij umiejętności z CV
        extracted_data = extract_skills_from_text(cv_content)
        skills = extracted_data.get('skills', [])
        experience = extracted_data.get('experience_level', 'junior')
        
        # Dodaj informację o wyodrębnionych umiejętnościach i poziomie doświadczenia
        logger.info(f"Wyodrębnione umiejętności: {skills}")
        logger.info(f"Poziom doświadczenia: {experience}")
        
        # Jeśli nie znaleziono umiejętności, zwróć błąd
        if not skills:
            return jsonify({
                "error": "Nie udało się wyodrębnić umiejętności z CV",
                "suggestion": "Upewnij się, że CV zawiera sekcję z umiejętnościami technicznymi"
            }), 400
        
        # Pobierz oferty z bazy danych
        all_jobs = get_jobs(keyword=job_keyword)
        logger.info(f"Znaleziono {len(all_jobs)} ofert w bazie danych dla słowa kluczowego: {job_keyword}")
        
        results = []
        for job in all_jobs:
            try:
                # Oblicz dopasowanie
                match_percentage = match_job_to_skills(job, skills, experience)
                
                # Akceptuj oferty z dopasowaniem powyżej 30%
                if match_percentage >= 30:
                    job_data = job.copy()
                    job_data['match_percentage'] = match_percentage
                    results.append(job_data)
            except Exception as job_error:
                logger.error(f"Błąd podczas przetwarzania oferty: {job_error}")
                continue
        
        # Sortuj wyniki po procencie dopasowania (malejąco)
        results.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Ogranicz liczbę wyników
        results = results[:limit]
        
        logger.info(f"Znaleziono {len(results)} dopasowanych ofert z wynikiem powyżej 30%")
        
        return jsonify({
            "results": results,
            "extracted_skills": skills,
            "experience_level": experience,
            "message": f"Znaleziono {len(results)} dopasowanych ofert na podstawie CV"
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania ofert na podstawie CV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Wystąpił błąd podczas wyszukiwania ofert: {str(e)}"}), 500

# Heartbeat sprawdzający status serwerów AI w tle
def background_server_check():
    while True:
        try:
            check_ai_server_health()
            time.sleep(300)  # Sprawdzaj co 5 minut
        except Exception as e:
            logger.error(f"Błąd w tle przy sprawdzaniu serwerów: {e}")
            time.sleep(60)  # W przypadku błędu, poczekaj minutę

def extract_skills_from_text(text):
    """
    Analizuje tekst wprowadzony przez użytkownika i wyodrębniam z niego umiejętności za pomocą AI
    
    Args:
        text (str): Tekst opisujący doświadczenie i umiejętności użytkownika
        
    Returns:
        dict: Słownik zawierający wyodrębnione umiejętności i poziom doświadczenia
    """
    # Podstawowa walidacja wejścia
    if not text or len(text) < 10:
        logger.warning("Tekst profilu jest zbyt krótki do analizy")
        return {
            "skills": [],
            "experience_level": "junior"
        }
    
    # Przygotuj prompt dla modelu AI
    system_prompt = """You are an expert recruiter who analyzes IT candidates' professional experience descriptions.
    Your task is to precisely extract specific technical skills and determine the level of experience.
    
    Experience levels:
    - junior: 0-2 years of experience, basic knowledge of technologies
    - mid: 2-4 years of experience, intermediate knowledge of technologies
    - senior: 4-8 years of experience, advanced knowledge, independence
    - expert: 8+ years of experience, deep knowledge, team leadership
    
    Focus exclusively on technical skills (programming languages, frameworks, tools, databases),
    ignoring soft skills.
    
    Respond only in JSON format with 'skills' and 'experience_level' fields.
    NEVER include <think> tags in your response.
    NEVER use Chinese characters in your response.
    Your JSON output must be valid and parseable.
    """
    
    prompt = f"""
    Analyze the following text and extract:
    1. List of specific technical skills (e.g., programming languages, frameworks, technologies, tools, databases)
    2. Determine the experience level (junior, mid, senior, expert) based on years of experience and proficiency

    Consider:
    - Junior: 0-2 years of experience
    - Mid: 2-4 years of experience
    - Senior: 4-8 years of experience
    - Expert: 8+ years of experience
    
    Text to analyze:
    {text}
    
    Respond ONLY in JSON format:
    {{
        "skills": ["skill1", "skill2", ...],
        "experience_level": "junior/mid/senior/expert"
    }}
    
    IMPORTANT: Make sure your response is valid JSON. Do not include any explanations outside the JSON.
    Do not use Chinese characters. Do not include <think> tags.
    """
    
    # Użyj modelu AI do analizy tekstu (z powtórzeniem w razie błędu)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            ai_response = get_ai_response(prompt, system_prompt)
            
            # Znajdź dane JSON w odpowiedzi
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_data = json_match.group(0)
                skills_data = json.loads(json_data)
                
                # Walidacja danych
                if not isinstance(skills_data.get("skills"), list):
                    skills_data["skills"] = []
                
                if skills_data.get("experience_level") not in ["junior", "mid", "senior", "expert"]:
                    skills_data["experience_level"] = "junior"
                
                # Mapa standaryzacji wielkości liter dla popularnych technologii
                capitalization_map = {
                    "javascript": "JavaScript",
                    "typescript": "TypeScript",
                    "python": "Python",
                    "java": "Java",
                    "c#": "C#",
                    "c++": "C++",
                    "ruby": "Ruby",
                    "php": "PHP",
                    "go": "Go",
                    "rust": "Rust",
                    "kotlin": "Kotlin",
                    "swift": "Swift",
                    "html": "HTML",
                    "css": "CSS",
                    "html5": "HTML5",
                    "css3": "CSS3",
                    "react": "React",
                    "reactjs": "React",
                    "angular": "Angular",
                    "angularjs": "AngularJS",
                    "vue": "Vue",
                    "vuejs": "Vue.js",
                    "node": "Node",
                    "nodejs": "Node.js",
                    "express": "Express",
                    "expressjs": "Express.js",
                    "django": "Django",
                    "flask": "Flask",
                    "spring": "Spring",
                    "springboot": "Spring Boot",
                    "asp.net": "ASP.NET",
                    "laravel": "Laravel",
                    "sql": "SQL",
                    "mysql": "MySQL",
                    "postgresql": "PostgreSQL",
                    "mongodb": "MongoDB",
                    "redis": "Redis",
                    "elasticsearch": "Elasticsearch",
                    "aws": "AWS",
                    "azure": "Azure",
                    "gcp": "GCP",
                    "docker": "Docker",
                    "kubernetes": "Kubernetes",
                    "git": "Git",
                    "github": "GitHub",
                    "gitlab": "GitLab",
                    "bitbucket": "Bitbucket",
                    "jenkins": "Jenkins",
                    "travis": "Travis CI",
                    "circleci": "CircleCI",
                    "flutter": "Flutter",
                    "react native": "React Native",
                    "xamarin": "Xamarin",
                    "graphql": "GraphQL",
                    "rest": "REST APIs",
                    "restful": "RESTful",
                    "soap": "SOAP",
                    "firebase": "Firebase",
                    "linux": "Linux",
                    "unix": "Unix",
                    "windows": "Windows",
                    "macos": "macOS",
                    "scrum": "Scrum",
                    "kanban": "Kanban",
                    "agile": "Agile",
                    "jira": "Jira",
                    "confluence": "Confluence",
                    "slack": "Slack",
                    "figma": "Figma",
                    "adobe xd": "Adobe XD",
                    "sketch": "Sketch",
                    "tailwind": "Tailwind",
                    "bootstrap": "Bootstrap",
                    "sass": "Sass",
                    "less": "Less",
                    "webpack": "Webpack",
                    "babel": "Babel",
                    "gulp": "Gulp",
                    "grunt": "Grunt",
                    "yarn": "Yarn",
                    "npm": "npm",
                    "redux": "Redux",
                    "mobx": "MobX",
                    "vuex": "Vuex",
                    "ngrx": "NgRx",
                    "rxjs": "RxJS",
                    "electron": "Electron",
                    "webrtc": "WebRTC",
                    "websocket": "WebSocket",
                    "pwa": "Progressive Web Apps",
                    "spa": "Single Page Applications"
                }
                
                # Usuń duplikaty i standaryzuj umiejętności
                standardized_skills = []
                original_skills = [skill.strip() for skill in skills_data.get("skills", []) if skill.strip()]
                
                for skill in original_skills:
                    # Standaryzuj wielkość liter
                    skill_lower = skill.lower()
                    standardized_skill = capitalization_map.get(skill_lower, skill)
                    
                    # Dodaj tylko jeśli nie ma już takiej umiejętności
                    if standardized_skill not in standardized_skills:
                        standardized_skills.append(standardized_skill)
                
                # Loguj znalezione umiejętności
                print(f"[DEBUG] Wyodrębnione umiejętności (po standaryzacji): {standardized_skills}")
                
                # Zwróć przetworzony wynik
                return {
                    "skills": standardized_skills,
                    "experience_level": skills_data.get("experience_level", "junior")
                }
            else:
                logger.warning(f"Nie znaleziono poprawnego JSON w odpowiedzi AI (próba {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania odpowiedzi AI: {e} (próba {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                continue
    
    # Jeśli wszystkie próby zawiodły, wykonaj podstawowe przetwarzanie tekstu
    # aby wyodrębnić najbardziej oczywiste umiejętności
    print(f"[DEBUG] Używam metody fallback do wyodrębnienia umiejętności z tekstu o długości {len(text)} znaków")
    text_lower = text.lower()
    
    # Rozszerzona lista umiejętności technicznych
    common_tech_skills = [
        "JavaScript", "Python", "Java", "C#", "C++", "Ruby", "PHP", "TypeScript",
        "Go", "Rust", "Kotlin", "Swift", "HTML", "CSS", "SQL", "NoSQL", "React", 
        "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", "ASP.NET",
        "Laravel", "Express", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
        "MongoDB", "PostgreSQL", "MySQL", "Oracle", "Redis", "Elasticsearch",
        "Git", "GitHub", "GitLab", "Bitbucket", "Jenkins", "Travis CI", "CircleCI",
        "Terraform", "Ansible", "Puppet", "Chef", "Firebase", "Heroku", "Netlify",
        "Vercel", "REST API", "GraphQL", "WebSockets", "RabbitMQ", "Kafka",
        "Redux", "Vuex", "NgRx", "Webpack", "Babel", "ESLint", "Jest", "Mocha",
        "Cypress", "Selenium", "TensorFlow", "PyTorch", "Pandas", "NumPy",
        "React Native", "Flutter", "Xamarin", "Unity", "Unreal Engine",
        "Linux", "Windows", "macOS", "Bash", "PowerShell", "Agile", "Scrum",
        "Jira", "Confluence", "Figma", "Adobe XD", "Sketch", "Photoshop",
        "Tailwind", "Bootstrap", "Material UI", "Sass", "Less", "Framer Motion"
    ]
    
    # Kategorie techniczne dla lepszej klasyfikacji
    tech_categories = {
        "frontend": ["html", "css", "javascript", "typescript", "react", "vue", "angular", "svelte", "jquery", "bootstrap", "tailwind", "sass", "less", "material-ui", "webpack", "babel", "eslint", "prettier", "framer motion"],
        "backend": ["python", "java", "c#", "php", "ruby", "go", "node.js", "express", "django", "flask", "spring", "asp.net", "laravel", "fastapi", "graphql", "rest api"],
        "database": ["sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "mariadb", "redis", "elasticsearch", "cassandra", "dynamodb", "firestore"],
        "mobile": ["react native", "flutter", "swift", "kotlin", "android", "ios", "xamarin", "ionic"],
        "devops": ["docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins", "github actions", "travis ci", "circleci", "nginx", "linux", "bash"],
        "tools": ["git", "github", "gitlab", "bitbucket", "jira", "confluence", "slack", "figma", "adobe xd", "sketch", "npm", "yarn", "gradle", "maven"]
    }
    
    skills = []
    detected_categories = set()
    
    # Wykrywanie umiejętności z listy
    for skill in common_tech_skills:
        if skill.lower() in text_lower:
            skills.append(skill)
            
            # Dodanie kategorii technicznej
            for category, category_skills in tech_categories.items():
                if skill.lower() in category_skills:
                    detected_categories.add(category)
    
    # Przeszukaj tekst pod kątem potencjalnych umiejętności technicznych, które
    # mogły zostać pominięte w liście common_tech_skills
    # Typowe wzorce nazw technologii: słowa zaczynające się wielką literą, 
    # zawierające "JS", "DB", "API", poprzedzone określeniami jak "znajomość", "umiejętność", itp.
    potential_skill_patterns = [
        r'\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*\b',  # CamelCase
        r'\b[A-Z0-9]{2,}\b',                      # UPPERCASE acronyms
        r'\b[a-z]+\.[a-zA-Z]+\b',                 # dot.notation
        r'\bumiejętność\s+([a-zA-Z0-9\s]+?)\b',   # "umiejętność X"
        r'\bznajomość\s+([a-zA-Z0-9\s]+?)\b',     # "znajomość X"
        r'\bdoświadczenie\s+[zw]\s+([a-zA-Z0-9\s]+?)\b',  # "doświadczenie z X"
        r'\bskill\s+([a-zA-Z0-9\s]+?)\b',         # "skill X"
        r'\b[a-z]+[-][a-z]+\b'                    # kebab-case
    ]
    
    for pattern in potential_skill_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            potential_skill = match.group(0).strip()
            # Filtruj typowe słowa, które nie są umiejętnościami
            if len(potential_skill) > 2 and potential_skill.lower() not in ["umiejętność", "znajomość", "doświadczenie", "skill", "oraz", "jako", "taki", "tego", "tego", "tych", "przy", "dla"]:
                skills.append(potential_skill)
    
    # Podstawowe określenie poziomu doświadczenia
    experience_level = "junior"
    years_pattern = r'(\d+)[\s-]*(rok|lat|roku|lata|letnie|letnim|years|year)'
    years_match = re.search(years_pattern, text, re.IGNORECASE)
    
    if years_match:
        try:
            years = int(years_match.group(1))
            if years >= 8:
                experience_level = "expert"
            elif years >= 4:
                experience_level = "senior"
            elif years >= 2:
                experience_level = "mid"
        except:
            pass
    
    # Sprawdź określenia stanowiska
    if re.search(r'\b(junior|młodszy|początkujący|stażysta|praktykant)\b', text_lower):
        experience_level = "junior"
    elif re.search(r'\b(mid|regular|intermediate|średni|samodzielny)\b', text_lower):
        experience_level = "mid"
    elif re.search(r'\b(senior|starszy|wiodący|lead|experienced|doświadczony)\b', text_lower):
        experience_level = "senior"
    elif re.search(r'\b(expert|architect|ekspert|główny|chief|principal|head of|dyrektor)\b', text_lower):
        experience_level = "expert"
    
    # Usuń duplikaty i ogranicz liczbę umiejętności
    skills = list(set(skills))
    
    print(f"[DEBUG] Wyodrębnione umiejętności (metoda backup): {skills}")
    print(f"[DEBUG] Wykryte kategorie techniczne: {detected_categories}")
    
    return {
        "skills": skills[:15],  # Ogranicz do 15 umiejętności
        "experience_level": experience_level
    }

# Uruchomienie aplikacji
if __name__ == '__main__':
    # Pobierz port z zmiennej środowiskowej lub użyj domyślnego
    port = int(os.environ.get('PORT', 5000))
    
    # Uruchom sprawdzanie serwerów w tle
    import threading
    background_thread = threading.Thread(target=background_server_check, daemon=True)
    background_thread.start()
    
    # Sprawdź, czy serwer AI jest dostępny przy starcie
    status = check_ai_server_health(force_check=True)
    if status['is_online']:
        logger.info(f"Serwer AI jest dostępny: {status['current_server']}")
        logger.info(f"Dostępne modele: {status['available_models']}")
    else:
        logger.warning("Serwery AI są niedostępne. Aplikacja będzie próbować ponownie w tle.")
    
    # Uruchom aplikację
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)