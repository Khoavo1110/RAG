"""Read-only model profiles; credentials never leave the backend."""
import os
import asyncio
import time
import httpx
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
import yaml
from dotenv import dotenv_values
from backend.app.config import settings


@dataclass(frozen=True)
class ModelProfile:
    provider: str
    model: str
    base_url: str
    api_key: str | None = field(default=None, repr=False)
    label: str = ''

    @property
    def id(self):
        return f'{self.provider}::{self.model}'

    @property
    def mode(self):
        return 'local' if self.provider == 'ollama' else 'api'

    @property
    def configured(self):
        return self.mode == 'local' or bool(self.api_key)

    def public(self):
        return dict(id=self.id, provider=self.provider, model=self.model,
                    label=self.label or self.provider, mode=self.mode, configured=self.configured)


selected_profile = ContextVar('nori_model_profile', default=None)

PROVIDERS = {
    'gemini': ('Google Gemini', 'https://generativelanguage.googleapis.com/v1beta/openai/', 'GEMINI_API_KEY', 'gemini-2.5-flash'),
    'nvidia': ('NVIDIA NIM', 'https://integrate.api.nvidia.com/v1', 'NVIDIA_API_KEY', 'nvidia/nemotron-3-super-120b-a12b'),
    'groq': ('Groq', 'https://api.groq.com/openai/v1', 'GROQ_API_KEY', 'openai/gpt-oss-120b'),
    'openrouter': ('OpenRouter', 'https://openrouter.ai/api/v1', 'OPENROUTER_API_KEY', settings.OPENROUTER_MODEL),
}


def hermes_home():
    explicit = os.getenv('HERMES_HOME')
    candidates = [Path(explicit)] if explicit else [Path.home()/'.hermes', Path.home()/'AppData/Local/hermes']
    return next((p for p in candidates if (p/'config.yaml').is_file()), None)


@lru_cache(maxsize=1)
def get_profiles():
    home = hermes_home()
    config, secrets = {}, {}
    if home:
        try:
            config = yaml.safe_load((home/'config.yaml').read_text(encoding='utf-8')) or {}
            if not isinstance(config, dict):
                config = {}
            secrets = dotenv_values(home/'.env')
        except (OSError, yaml.YAMLError):
            config = {}
    configured = config.get('providers', {})
    if not isinstance(configured, dict):
        configured = {}
    profiles = {}
    local = configured.get('ollama', {})
    local_models = local.get('models', []) if isinstance(local, dict) else []
    for model in dict.fromkeys([settings.OLLAMA_MODEL] + [m for m in local_models if isinstance(m, str)]):
        p = ModelProfile('ollama', model, settings.OLLAMA_BASE_URL, 'ollama', 'Ollama Local')
        profiles[p.id] = p
    for provider, (label, default_url, key_name, default_model) in PROVIDERS.items():
        record = configured.get(provider, {})
        record = record if isinstance(record, dict) else {}
        models = record.get('models', [])
        models = [m for m in models if isinstance(m, str) and m.strip()] if isinstance(models, list) else []
        if provider == 'gemini' and settings.LLM_MODEL.startswith('gemini-'):
            models = list(dict.fromkeys([settings.LLM_MODEL] + models))
        models = models or [default_model]
        key = secrets.get(key_name) or getattr(settings, key_name, None) or os.getenv(key_name)
        # Gemini Hermes can use its native endpoint; this adapter requires compatibility URL.
        url = default_url if provider == 'gemini' else record.get('base_url', default_url)
        parsed = urlsplit(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
            url = default_url
        for model in models:
            p = ModelProfile(provider, model, url, key, label)
            profiles[p.id] = p
    return profiles


def resolve_profile(profile_id):
    profile = get_profiles().get(profile_id)
    if not profile:
        raise ValueError('Mô hình không có trong danh sách cấu hình.')
    if not profile.configured:
        raise ValueError('Provider chưa có khóa API ở backend hoặc Hermes.')
    return profile


def model_catalog():
    profiles = get_profiles()
    local_id = f'ollama::{settings.OLLAMA_MODEL}'
    available = [p for p in profiles.values() if p.mode == 'api' and p.configured]
    preferred = next((p.id for p in available if p.provider == 'gemini'), available[0].id if available else None)
    return dict(profiles=[p.public() for p in profiles.values()], local_default_id=local_id, api_default_id=preferred)


_catalog_snapshot = None
_catalog_updated = 0.0
_catalog_lock = asyncio.Lock()


async def refresh_model_catalog():
    global _catalog_snapshot, _catalog_updated
    if _catalog_snapshot is not None and time.monotonic() - _catalog_updated < 300:
        return _catalog_snapshot
    async with _catalog_lock:
        if _catalog_snapshot is not None and time.monotonic() - _catalog_updated < 300:
            return _catalog_snapshot
        profiles = get_profiles()
        async def survey(provider, items):
            p = items[0]
            if not p.configured:
                return provider, None
            try:
                async with httpx.AsyncClient(timeout=6) as client:
                    if provider == 'ollama':
                        base = p.base_url.rstrip('/').removesuffix('/v1')
                        response = await client.get(base+'/api/tags')
                        response.raise_for_status()
                        return provider, {m['name'] for m in response.json().get('models', [])}
                    response = await client.get(p.base_url.rstrip('/')+'/models', headers={'Authorization':'Bearer '+p.api_key})
                    response.raise_for_status()
                    return provider, {m['id'].removeprefix('models/') for m in response.json().get('data', [])}
            except Exception:
                return provider, None
        grouped = {name:[p for p in profiles.values() if p.provider == name] for name in {p.provider for p in profiles.values()}}
        surveyed = dict(await asyncio.gather(*(survey(name, items) for name, items in grouped.items())))
        result = model_catalog()
        for public in result['profiles']:
            ids = surveyed[public['provider']]
            public['available'] = (public['model'] in ids or public['model']+':latest' in ids) if ids is not None else None
            public['status'] = 'missing_credentials' if not public['configured'] else 'unverified' if ids is None else 'listed' if public['available'] else 'unlisted'
        cloud = [p for p in result['profiles'] if p['mode']=='api' and p['configured'] and p['available'] is not False]
        result['api_default_id'] = next((p['id'] for p in cloud if p['provider']=='gemini'), cloud[0]['id'] if cloud else None)
        _catalog_snapshot, _catalog_updated = result, time.monotonic()
        return result
