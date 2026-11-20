"""
Diagnostic utility: Lists active Gemini models supported by your API key.
"""
import os
import requests

api_key = os.environ.get("GEMINI_API_KEY", "")
print("Testing API Key:", api_key[:12] + "..." if api_key else "EMPTY!")

if not api_key:
    print("Please set your GEMINI_API_KEY in PowerShell before running this test:")
    print("  $env:GEMINI_API_KEY='your_key_here'")
    exit(1)

for ver in ["v1beta", "v1"]:
    url = f"https://generativelanguage.googleapis.com/{ver}/models?key={api_key}"
    print(f"\nChecking ModelService on endpoint [{ver}]...")
    try:
        r = requests.get(url, timeout=15)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            models = r.json().get("models", [])
            gen_models = [
                m["name"].replace("models/", "") 
                for m in models 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            print(f"Supported generateContent models on {ver} ({len(gen_models)}):")
            for m in gen_models:
                print(f"  • {m}")
        else:
            print(f"Error ({r.status_code}): {r.text[:300]}")
    except Exception as e:
        print(f"Connection error on {ver}: {e}")