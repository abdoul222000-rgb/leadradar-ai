import os
import uvicorn
from leadradar_ai.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    print("\n" + "=" * 65)
    print("🚀 DEMARRAGE DE LEADRADAR AI (Zero-Ad Reddit & X Lead Engine)")
    print(f"📍 URL de la Landing Page : http://localhost:{port}")
    print(f"📍 URL du Dashboard       : http://localhost:{port}/dashboard")
    print(f"📍 Compte Fondateur       : {settings.FOUNDER_EMAIL} (PIN: {settings.FOUNDER_PIN})")
    print(f"💳 Banque de Réception    : {settings.LEAD_BANK_NAME} (Grey USD ••••{settings.LEAD_BANK_ACCOUNT_LAST4})")
    print("=" * 65 + "\n")
    uvicorn.run("leadradar_ai.main:app", host="0.0.0.0", port=port, reload=False)
