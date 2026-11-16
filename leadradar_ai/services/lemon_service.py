import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from ..config import settings
from ..database import User, BillingLog

class LemonSqueezyService:
    """Service d'intégration des paiements et Webhooks Lemon Squeezy"""

    @classmethod
    def verify_webhook_signature(cls, raw_payload: bytes, signature_header: Optional[str]) -> bool:
        """Vérifie l'authenticité du webhook Lemon Squeezy via HMAC SHA-256"""
        if not signature_header:
            return False
            
        secret = settings.LEMON_SQUEEZY_WEBHOOK_SECRET.encode('utf-8')
        digest = hmac.new(secret, raw_payload, hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(digest, signature_header)

    @classmethod
    def get_checkout_url(cls, plan_type: str, user_id: int, user_email: str) -> str:
        """Construit l'URL de paiement Lemon Squeezy avec les paramètres de suivi personnalisés"""
        base_url = (
            settings.LEMON_SQUEEZY_GROWTH_URL 
            if plan_type.upper() == "GROWTH" 
            else settings.LEMON_SQUEEZY_STARTER_URL
        )
        
        # Ajout du paramètre de passthrough (pour que le webhook sache qui a payé)
        params = f"?checkout[custom][user_id]={user_id}&checkout[email]={user_email}"
        return f"{base_url}{params}"

    @classmethod
    def process_webhook_event(cls, event_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """Traite l'événement Lemon Squeezy et active le compte en Premium automatiquement"""
        meta = event_data.get("meta", {})
        event_name = meta.get("event_name", "unknown")
        custom_data = meta.get("custom_data", {})
        
        data = event_data.get("data", {})
        attributes = data.get("attributes", {})
        
        user_id = custom_data.get("user_id")
        user_email = attributes.get("user_email")
        
        user = None
        if user_id:
            user = db_session.query(User).filter(User.id == int(user_id)).first()
        elif user_email:
            user = db_session.query(User).filter(User.email == user_email.lower().strip()).first()

        order_id = str(data.get("id", ""))
        total_usd = float(attributes.get("total", 0)) / 100.0 if attributes.get("total") else 29.0
        currency = attributes.get("currency", "USD")

        # Événements de paiement réussi / activation d'abonnement
        if event_name in ["order_created", "subscription_created", "subscription_payment_success"]:
            new_plan = "GROWTH" if total_usd >= 50.0 else "STARTER"
            
            if user:
                user.plan = new_plan
                user.subscription_status = "active"
                user.lemon_subscription_id = str(attributes.get("first_subscription_item", {}).get("subscription_id", order_id))
            
            # Enregistrement du log de facturation avec mention de la banque Grey USD
            log = BillingLog(
                user_id=user.id if user else None,
                event_name=event_name,
                lemon_order_id=order_id,
                amount_usd=total_usd,
                currency=currency,
                status="success",
                payout_bank=f"{settings.LEAD_BANK_NAME} (Grey USD ••••{settings.LEAD_BANK_ACCOUNT_LAST4})",
                payload_raw=json.dumps(event_data)[:2000]
            )
            db_session.add(log)
            db_session.commit()
            
            return {
                "success": True, 
                "action": "plan_upgraded", 
                "plan": new_plan, 
                "user_id": user.id if user else None,
                "amount": total_usd,
                "payout_destination": settings.LEAD_BANK_NAME
            }

        elif event_name in ["subscription_cancelled", "subscription_expired"]:
            if user:
                user.plan = "FREE"
                user.subscription_status = "cancelled"
                
            log = BillingLog(
                user_id=user.id if user else None,
                event_name=event_name,
                lemon_order_id=order_id,
                amount_usd=0.0,
                status="cancelled",
                payout_bank=f"{settings.LEAD_BANK_NAME} (Grey USD ••••{settings.LEAD_BANK_ACCOUNT_LAST4})",
                payload_raw=json.dumps(event_data)[:2000]
            )
            db_session.add(log)
            db_session.commit()
            
            return {"success": True, "action": "plan_downgraded", "user_id": user.id if user else None}

        return {"success": True, "action": "ignored_event", "event_name": event_name}
