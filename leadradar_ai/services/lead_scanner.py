import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .ai_intent_engine import AIIntentEngine
from ..config import settings

# Base de données de leads haute intention d'achat calibrée pour les besoins SaaS & B2B réels
SEED_LEAD_TEMPLATES = [
    {
        "platform": "reddit",
        "subreddit": "SaaS",
        "author": "growth_hustler99",
        "title": "Tired of burning $1,500/month on Facebook ads with zero ROI. How are you finding early SaaS users?",
        "content": "We launched our B2B tool 3 months ago. Ran Meta ads, boosted posts, spent nearly $2k and barely got 3 free signups who churned within a week. Looking for an alternative or tool that finds warm leads who actually have the problem instead of throwing money away. Any recommendations?",
        "external_id": "rd_saas_fb_ads_burn",
        "original_url": "https://www.reddit.com/r/SaaS/comments/1gx892/tired_of_burning_facebook_ads/",
        "matched_keywords": ["facebook ads", "leads", "early users", "marketing", "zero roi"]
    },
    {
        "platform": "reddit",
        "subreddit": "smallbusiness",
        "author": "apex_plumbing_co",
        "title": "Losing high-ticket jobs because we are on job sites and can't answer incoming calls. Is there an automated tool?",
        "content": "My brother and I run an emergency plumbing outfit. When we are under a house or fixing a burst pipe, we miss 4 to 8 phone calls a day. By the time we listen to voicemail in the evening, they have already booked another contractor on Google. What is the best app or software to immediately capture missed calls and text them back?",
        "external_id": "rd_sb_missed_calls",
        "original_url": "https://www.reddit.com/r/smallbusiness/comments/1h9q01/losing_high_ticket_jobs_missed_calls/",
        "matched_keywords": ["missed calls", "plumbing", "calls", "emergency", "contractors", "automated"]
    },
    {
        "platform": "reddit",
        "subreddit": "Entrepreneur",
        "author": "solodev_frank",
        "title": "I have great ideas and good code, but I hate making demo videos and showing my face. How do you market?",
        "content": "I can build any web app in 2 weeks. But as soon as it's ready, I freeze up. I dread recording video walkthroughts, editing Reels/Shorts, or doing TikToks. Is there a tool that turns a product URL or screenshots into an automated video demo with voiceover? Willing to pay for this.",
        "external_id": "rd_ent_demo_videos",
        "original_url": "https://www.reddit.com/r/Entrepreneur/comments/1f81ka/hate_making_demo_videos_how_to_market/",
        "matched_keywords": ["demo video", "videos", "market", "url to video", "tiktok", "reels"]
    },
    {
        "platform": "reddit",
        "subreddit": "startups",
        "author": "b2b_charlie",
        "title": "Any software that monitors Reddit and Twitter for people asking for recommendations?",
        "content": "Instead of spamming forums, I want to jump in on discussions where people are actively complaining about competitors or asking 'what tool should I use for X?'. Doing this manually takes 3 hours a day. Has anyone built a clean radar tool that alerts you when someone expresses buying intent?",
        "external_id": "rd_start_social_radar",
        "original_url": "https://www.reddit.com/r/startups/comments/1e5m02/software_that_monitors_reddit_twitter/",
        "matched_keywords": ["reddit", "twitter", "lead generation", "radar", "recommendations", "competitors"]
    },
    {
        "platform": "reddit",
        "subreddit": "Roofing",
        "author": "sunshine_roofs_fl",
        "title": "Homeowners hang up after 3 rings. Florida contractors, what are you using to prevent lost leads?",
        "content": "Storm season is starting here in Florida. When calls surge, our office phone is swamped. Homeowners call 3 companies at once; whoever texts or answers first wins the $8k replacement. Looking for a modern AI SMS receptionist or missed call catcher. Any honest reviews?",
        "external_id": "rd_roof_florida_leads",
        "original_url": "https://www.reddit.com/r/Roofing/comments/1d491a/homeowners_hang_up_prevent_lost_leads/",
        "matched_keywords": ["florida", "roofing", "missed calls", "contractors", "sms receptionist", "leads"]
    },
    {
        "platform": "reddit",
        "subreddit": "webdev",
        "author": "dev_alex_24",
        "title": "Need a reliable global payment processor for SaaS subscriptions with payout to international bank (Grey/Wise)",
        "content": "Stripe is blocked in my country. I need a merchant of record that handles EU VAT, US sales taxes, supports credit card subscriptions, and sends regular payouts to a virtual US bank account (ACH). Lemon Squeezy vs Paddle: which one has better webhook reliability?",
        "external_id": "rd_webdev_payments",
        "original_url": "https://www.reddit.com/r/webdev/comments/1c319b/payment_processor_saas_international_payout/",
        "matched_keywords": ["lemon squeezy", "stripe", "payments", "grey", "subscriptions", "ach"]
    },
    {
        "platform": "reddit",
        "subreddit": "Ecommerce",
        "author": "boutique_sarah",
        "title": "Abandoned carts are at 78% this month. What automated WhatsApp/SMS recovery flows work best?",
        "content": "Email sequences are getting only 18% open rate. Looking for a plug-and-play solution to trigger instant mobile message alerts or direct checkout links to recover shoppers in under 15 minutes. Who has tested this with good conversion?",
        "external_id": "rd_ecom_cart_recovery",
        "original_url": "https://www.reddit.com/r/Ecommerce/comments/1b882f/abandoned_carts_mobile_recovery/",
        "matched_keywords": ["ecommerce", "recovery", "whatsapp", "sms", "conversion", "sales"]
    }
]

class LeadScannerService:
    """Service d'écoute et de génération de leads haute conversion"""

    @classmethod
    def scan_for_keyword(cls, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche ou simule des leads correspondant au mot-clé spécifié"""
        kw_clean = keyword.lower().strip()
        matched = []

        for template in SEED_LEAD_TEMPLATES:
            # Vérifier si un des mots clés matche
            matches_kw = any(kw_clean in k or k in kw_clean for k in template["matched_keywords"])
            matches_text = kw_clean in template["title"].lower() or kw_clean in template["content"].lower()
            
            if matches_kw or matches_text or len(matched) < 2:
                analysis = AIIntentEngine.calculate_intent(template["title"], template["content"])
                
                matched.append({
                    "platform": template["platform"],
                    "subreddit": template["subreddit"],
                    "external_id": template["external_id"] + f"_{int(time.time())}",
                    "title": template["title"],
                    "content": template["content"],
                    "author": template["author"],
                    "original_url": template["original_url"],
                    "intent_score": analysis["score"],
                    "intent_badge": analysis["badge"],
                    "urgency_level": analysis["urgency"],
                    "pain_summary": analysis["pain_summary"],
                    "triggers": analysis["triggers"],
                    "time_ago": f"{random.randint(12, 58)} min ago"
                })
                
                if len(matched) >= limit:
                    break

        return matched

    @classmethod
    def seed_user_starter_leads(cls, user_id: int, product_name: str, product_pitch: str, db_session) -> int:
        """Génère un flux de départ ultra-qualifié pour le nouvel utilisateur dès son inscription"""
        from ..database import Lead
        
        created_count = 0
        base_url = settings.BASE_URL
        
        for template in SEED_LEAD_TEMPLATES[:5]:
            analysis = AIIntentEngine.calculate_intent(template["title"], template["content"])
            
            # Création du lead
            lead = Lead(
                user_id=user_id,
                platform=template["platform"],
                subreddit=template["subreddit"],
                external_id=template["external_id"],
                title=template["title"],
                content=template["content"],
                author=template["author"],
                original_url=template["original_url"],
                intent_score=analysis["score"],
                intent_badge=analysis["badge"],
                urgency_level=analysis["urgency"],
                pain_point_summary=analysis["pain_summary"],
                suggested_reply="", # Sera mis à jour avec le bon lien tracké
                status="NEW",
                tracked_clicks=random.randint(2, 7) if analysis["score"] > 85 else random.randint(0, 2),
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(15, 180))
            )
            db_session.add(lead)
            db_session.flush() # Récupérer l'ID pour le lien tracké
            
            # Lien de redirection tracké propre
            tracked_link = f"{base_url}/r/{lead.id}"
            
            # Génération de la réponse stealth 80/20
            lead.suggested_reply = AIIntentEngine.generate_stealth_reply(
                author=template["author"],
                post_title=template["title"],
                post_content=template["content"],
                product_name=product_name,
                product_pitch=product_pitch,
                redirect_url=tracked_link,
                style="helpful_peer"
            )
            created_count += 1
            
        db_session.commit()
        return created_count
