import json
import os
import hashlib
from litellm import completion

CACHE_FILE = 'ai_cache.json'

def get_cached_ai_response(prompt, model=None, api_key=None):
    """Fetches AI response from a local JSON cache or calls the API if not found."""
    if not model:
        model = os.environ.get('AI_MODEL_NAME', 'gemini/gemini-2.5-flash-lite')
        
    cache_data = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
        except:
            pass
            
    # Generate unique hash for this prompt
    prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    
    if prompt_hash in cache_data:
        return cache_data[prompt_hash]
        
    # Call LiteLLM Api
    try:
        kwargs = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if api_key:
            kwargs["api_key"] = api_key
        response = completion(**kwargs)
        res_text = response['choices'][0]['message']['content'].strip()
        
        # Write back to cache
        cache_data[prompt_hash] = res_text
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
            
        return res_text
    except Exception as e:
        raise e
