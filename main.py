import hashlib
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title='Guardian API', version='0.3.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORE_PATH = DATA_DIR / 'store.json'

DEFAULT_STORE = {
    'emergency_contact': {
        'name': '',
        'phone': '',
    },
    'medical_profile': {
        'first_name': '',
        'full_name': '',
        'birth_date': '',
        'primary_phone': '',
        'diabetes_type': 'Diabetes tipo 1',
        'uses_insulin': True,
        'allergies': '',
        'notes': '',
        'pin_hash': '',
    },
}

EMERGENCY_CONTENT = {
    'headline': [
        'TENHO DIABETES TIPO 1',
        'MINHA GLICOSE PODE ESTAR BAIXA',
        'PRECISO INGERIR ALGO DOCE',
    ],
    'carb_title': 'ME DÊ ALGO DOCE AGORA',
    'carb_subtitle': 'Escolha uma das opções abaixo, de preferência líquida.',
    'carb_options': [
        '3 colheres de sopa de açúcar em 1 copo de água',
        '1 copo de refrigerante normal',
        '1 copo de energético normal',
        '1 copo de suco de frutas com 1 colher de açúcar',
        '3 colheres de sopa de mel',
    ],
    'carb_fallback': 'Se não tiver nada disso: dê qualquer alimento doce que eu consiga ingerir.',
    'do_title': 'O QUE FAZER',
    'do_items': [
        'Me ajude a ficar em repouso em um lugar calmo.',
        'Se eu ainda não fiz o teste, você pode me ajudar a medir a glicose depois do açúcar.',
        'Escute o que eu pedir e observe se estou melhorando.',
        'Espere 15 minutos antes de me fazer levantar.',
    ],
    'dont_title': 'NÃO FAZER',
    'dont_items': [
        'Não me dê insulina. Minha glicose pode estar baixa.',
        'Não fale alto nem tente conversar demais comigo.',
        'Se eu parecer embriagado, lembre que posso estar em hipoglicemia.',
        'Minha pressão não está necessariamente baixa.',
        'Não me faça levantar antes de passar o tempo.',
        'Não me dê alimentos sólidos sem água, porque posso engasgar.',
        'Não me deixe sozinho.',
    ],
    'critical_button_label': 'Não estou conseguindo engolir / estou inconsciente',
    'timer': {
        'duration_seconds': 900,
        'start_label': 'Iniciar 15 minutos',
        'end_title': 'AGORA MEÇA A GLICOSE, SE POSSÍVEL',
        'end_description': 'Se eu ainda estiver mal ou abaixo de 70 mg/dL, repita e busque ajuda.',
        'bibinho_prompts': [
            {
                'at_second': 0,
                'text': 'Eu posso tentar levantar ou dizer que já estou bem. Tente me manter em repouso.',
            },
            {
                'at_second': 300,
                'text': 'Observe como estou evoluindo. Escute o que eu pedir e mantenha calma.',
            },
            {
                'at_second': 600,
                'text': 'Se eu parecer piorando ou mais confuso, me ajude e considere buscar ajuda.',
            },
            {
                'at_second': 780,
                'text': 'Já está quase no tempo. Em breve será importante medir a glicose.',
            },
        ],
    },
    'critical': {
        'title': 'EMERGÊNCIA',
        'description': 'Se eu não consigo engolir ou estou inconsciente, isso não é mais uma correção simples.',
        'do_items': [
            'Não dê comida ou bebida.',
            'Use glucagon, se houver disponível.',
            'Coloque a pessoa de lado, se necessário.',
            'Chame ajuda imediatamente.',
        ],
        'dont_items': [
            'Não force líquidos ou comida.',
            'Não espere melhorar sozinho.',
            'Não deixe a pessoa sozinha.',
        ],
        'call_label': 'Ligar para o SAMU',
        'samu_number': '192',
    },
    'public_qr_path': '/public/emergency-guide',
}

GLUCOSE_GUIDE = {
    'title': 'Como medir a glicose',
    'subtitle': 'Siga os passos abaixo.',
    'steps': [
        {
            'step': 1,
            'title': 'Separe o material',
            'text': 'Pegue o medidor, a fita e a lanceta.',
            'image_key': 'kit',
        },
        {
            'step': 2,
            'title': 'Coloque a fita',
            'text': 'Insira a fita no aparelho até ele ligar.',
            'image_key': 'strip',
        },
        {
            'step': 3,
            'title': 'Fure a ponta do dedo',
            'text': 'Use a lanceta. Se puder, use a lateral do dedo.',
            'image_key': 'lancet',
        },
        {
            'step': 4,
            'title': 'Encoste a gota na fita',
            'text': 'Encoste o sangue na ponta da fita até o aparelho reconhecer.',
            'image_key': 'blood',
        },
        {
            'step': 5,
            'title': 'Espere o resultado',
            'text': 'Aguarde o valor da glicose aparecer na tela.',
            'image_key': 'result',
        },
    ],
    'after_result': 'Se a glicose estiver abaixo de 70 mg/dL, dê açúcar novamente, espere 15 minutos e repita se necessário.',
    'video_hint': 'Aqui pode entrar um vídeo curto de demonstração depois.',
}


class EmergencyContactIn(BaseModel):
    name: str = Field(default='', max_length=120)
    phone: str = Field(default='', max_length=40)


class MedicalProfileIn(BaseModel):
    first_name: str = Field(default='', max_length=80)
    full_name: str = Field(default='', max_length=160)
    birth_date: str = Field(default='', max_length=20)
    primary_phone: str = Field(default='', max_length=40)
    diabetes_type: str = Field(default='Diabetes tipo 1', max_length=80)
    uses_insulin: bool = True
    allergies: str = Field(default='', max_length=300)
    notes: str = Field(default='', max_length=600)
    pin: Optional[str] = Field(default=None, min_length=4, max_length=12)


class PinUnlockRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=12)



def load_store() -> dict:
    if not STORE_PATH.exists():
        save_store(DEFAULT_STORE)
        return json.loads(json.dumps(DEFAULT_STORE))

    with STORE_PATH.open('r', encoding='utf-8') as file:
        return json.load(file)



def save_store(store: dict) -> None:
    with STORE_PATH.open('w', encoding='utf-8') as file:
        json.dump(store, file, ensure_ascii=False, indent=2)



def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode('utf-8')).hexdigest()



def public_medical_summary(profile: dict) -> dict:
    return {
        'first_name': profile.get('first_name', ''),
        'diabetes_type': profile.get('diabetes_type', 'Diabetes tipo 1'),
        'uses_insulin': profile.get('uses_insulin', True),
        'message': 'Pessoa com diabetes tipo 1. Pode estar em hipoglicemia.',
    }


@app.get('/health')
async def health_check():
    return {'status': 'ok'}


@app.get('/content/emergency')
async def get_emergency_content():
    store = load_store()
    return {
        **EMERGENCY_CONTENT,
        'contact_available': bool(store['emergency_contact'].get('phone')),
        'public_medical_summary': public_medical_summary(store['medical_profile']),
    }


@app.get('/content/glucose-guide')
async def get_glucose_guide():
    return GLUCOSE_GUIDE


@app.get('/public/emergency-guide')
async def get_public_emergency_guide():
    return {
        'headline': EMERGENCY_CONTENT['headline'],
        'carb_title': EMERGENCY_CONTENT['carb_title'],
        'carb_options': EMERGENCY_CONTENT['carb_options'],
        'carb_fallback': EMERGENCY_CONTENT['carb_fallback'],
        'do_items': EMERGENCY_CONTENT['do_items'],
        'dont_items': EMERGENCY_CONTENT['dont_items'],
        'timer_minutes': 15,
    }


@app.get('/user/emergency-contact')
async def get_emergency_contact():
    store = load_store()
    return store['emergency_contact']


@app.post('/user/emergency-contact')
async def save_emergency_contact(payload: EmergencyContactIn):
    store = load_store()
    store['emergency_contact'] = payload.model_dump()
    save_store(store)
    return store['emergency_contact']


@app.get('/user/medical-profile')
async def get_medical_profile():
    store = load_store()
    profile = store['medical_profile']
    return {
        'summary': public_medical_summary(profile),
        'has_pin': bool(profile.get('pin_hash')),
        'details': {
            'full_name': '',
            'birth_date': '',
            'primary_phone': '',
            'allergies': '',
            'notes': '',
        },
    }


@app.post('/user/medical-profile')
async def save_medical_profile(payload: MedicalProfileIn):
    store = load_store()
    existing_hash = store['medical_profile'].get('pin_hash', '')

    new_profile = payload.model_dump(exclude={'pin'})
    new_profile['pin_hash'] = hash_pin(payload.pin) if payload.pin else existing_hash
    store['medical_profile'] = new_profile
    save_store(store)

    return {
        'saved': True,
        'summary': public_medical_summary(new_profile),
        'has_pin': bool(new_profile['pin_hash']),
    }


@app.post('/user/medical-profile/unlock')
async def unlock_medical_profile(payload: PinUnlockRequest):
    store = load_store()
    profile = store['medical_profile']
    stored_hash = profile.get('pin_hash', '')

    if stored_hash and hash_pin(payload.pin) != stored_hash:
        raise HTTPException(status_code=401, detail='PIN incorreto.')

    return {
        'full_name': profile.get('full_name', ''),
        'birth_date': profile.get('birth_date', ''),
        'primary_phone': profile.get('primary_phone', ''),
        'allergies': profile.get('allergies', ''),
        'notes': profile.get('notes', ''),
        'diabetes_type': profile.get('diabetes_type', 'Diabetes tipo 1'),
        'uses_insulin': profile.get('uses_insulin', True),
    }
