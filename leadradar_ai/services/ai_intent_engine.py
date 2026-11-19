import re
import urllib.parse
from typing import Dict, Any, List
from ..config import settings

class AIIntentEngine:
    """
    Moteur d'analyse psychologique d'intention d'achat et 
    générateur de réponses de vente persuasives à haute conversion (Règle 80/20).
    """

    HIGH_INTENT_PATTERNS = [
        r"\blooking for\b", r"\brecommend(?:ation)?\b", r"\balternative to\b",
        r"\bhow do (?:you|i)\b", r"\bis there (?:a|any) tool\b", r"\bis there an app\b",
        r"\bany software\b", r"\bwilling to pay\b", r"\bbest tool for\b",
        r"\btired of\b", r"\bhate doing this manually\b", r"\bwasting (?:so much )?time\b",
        r"\bneed help finding\b", r"\bwhat do you use for\b", r"\bsuggestions for\b",
        r"\bcan someone recommend\b", r"\bswitch(?:ing)? from\b", r"\bexpensive\b"
    ]

    URGENCY_PATTERNS = [
        r"\basap\b", r"\burgent\b", r"\btoday\b", r"\blosing (?:money|clients|leads)\b",
        r"\bfrustrated\b", r"\bdesperate\b", r"\bcritical\b", r"\bimmediately\b"
    ]

    NEGATIVE_COMPETITOR_PATTERNS = [
        r"\bhate\b", r"\bclunky\b", r"\bslow\b", r"\bbuggy\b", r"\bhorrible support\b",
        r"\bprice hike\b", r"\btoo expensive\b", r"\bcancelled my\b", r"\bleaving\b"
    ]

    @classmethod
    def calculate_intent(cls, title: str, content: str) -> Dict[str, Any]:
        """Analyse le texte et calcule un score d'intention d'achat de 0 à 100%"""
        full_text = f"{title} {content}".lower()
        score = 55
        triggers_found = []
        
        for pattern in cls.HIGH_INTENT_PATTERNS:
            if re.search(pattern, full_text):
                score += 12
                triggers_found.append(pattern.replace(r"\b", "").replace("(?:you|i)", "you/i"))
                
        urgency = "LOW"
        for pattern in cls.URGENCY_PATTERNS:
            if re.search(pattern, full_text):
                score += 12
                urgency = "HIGH"
                triggers_found.append("Urgence critique")
                break
                
        for pattern in cls.NEGATIVE_COMPETITOR_PATTERNS:
            if re.search(pattern, full_text):
                score += 14
                triggers_found.append("Friction concurrent")
                break

        score = min(max(score, 45), 98)
        
        if score >= 80:
            badge = "HOT"
            urgency = "HIGH" if urgency == "HIGH" else "MEDIUM"
        elif score >= 60:
            badge = "WARM"
            urgency = "MEDIUM"
        else:
            badge = "INFO"
            urgency = "LOW"
            
        pain_summary = cls.extract_pain_summary(title, content)
        
        return {
            "score": score,
            "badge": badge,
            "urgency": urgency,
            "pain_summary": pain_summary,
            "triggers": triggers_found[:4]
        }

    @classmethod
    def extract_pain_summary(cls, title: str, content: str) -> str:
        clean_title = title.strip()
        if len(clean_title) <= 90:
            return clean_title
        return clean_title[:87] + "..."

    @classmethod
    def generate_stealth_reply(
        cls, 
        author: str, 
        post_title: str, 
        post_content: str, 
        product_name: str, 
        product_pitch: str, 
        redirect_url: str,
        style: str = "high_converting"
    ) -> str:
        """
        Génère une réponse psychologiquement irrésistible :
        1. Empathie profonde (vécu réel)
        2. Chiffrage de la perte financière subie par l'auteur
        3. Explication du mécanisme qui résout la douleur (SMS automatique < 8s)
        4. Recommandation transparente de l'outil avec lien direct pour tester et souscrire !
        """
        author_name = f"u/{author}" if author and not author.startswith("u/") else (author or "there")
        full_text = f"{post_title} {post_content}".lower()

        # CAS 1 : Croissance SaaS / 10 Premiers Clients / Prospection Reddit & X (LeadRadar AI Dogfooding)
        if "leadradar" in product_name.lower() or any(w in full_text for w in [
            "first 10 customers", "early saas", "find b2b", "ad spend", "facebook ads", 
            "meta ads", "cold email", "saas marketing", "get clients", "zero ad", 
            "reddit leads", "trouver clients", "warm leads", "zero roi", "apollo"
        ]):
            return (
                f"Hey {author_name}, reading your post literally feels like looking into a mirror from when we first launched.\n\n"
                f"Here is the brutal math for solo bootstrapped founders in 2026: cold outbound and paid ads are a financial bloodbath. Cold email reply rates have collapsed under 1% due to strict Google/Yahoo spam filters, and Meta/Google ads cost $40 to $90+ just to acquire a single free-trial user who churns in 4 days.\n\n"
                f"The solo founders quietly hitting $3k to $10k MRR without ad budgets don't run paid campaigns. They use intent-driven social listening:\n"
                f"Every single day on Reddit and X, hundreds of founders, freelancers, and businesses literally type: 'Is there a tool for X?', 'Tired of doing Y manually', or 'What software do you recommend for Z?'.\n\n"
                f"When you reply to those specific people within 15 minutes with 80% genuine peer help and 20% transparent tool recommendation, your conversion rate is typically 30%+ because you are solving an active, burning pain right when they feel it.\n\n"
                f"Doing this manually takes 4 hours of doom-scrolling, so we built {product_name} ({redirect_url}) to completely automate the pipeline ({product_pitch}).\n\n"
                f"It continuously listens to Reddit and Twitter, flags posts with 80%+ buying intent, and drafts anti-ban stealth replies with your tracked link ready in 1 click.\n\n"
                f"You can test a live simulation on your own SaaS keywords right here: {redirect_url}\n\n"
                f"Stop burning cash on Mark Zuckerberg's ad engine and go where buyers are already asking for your solution!"
            )

        # CAS 2 : Appels manqués / Artisans / Chantiers (CallCatch AI)
        elif any(w in full_text for w in ["call", "artisan", "plumb", "roof", "hvac", "contractor", "chantier", "travaux", "sink", "leak"]):
            return (
                f"Hey {author_name}, reading your post literally gives me flashbacks to last year.\n\n"
                f"Here is the brutal financial reality in trades: voicemail is 100% dead in 2026. Industry data shows that 84% of homeowners with an emergency repair (burst pipe, roof leak, broken AC) hang up within 3 seconds of hearing a voicemail beep and immediately call the next contractor on Google.\n\n"
                f"When you are on a roof, under a crawlspace, or driving between jobs, you cannot answer the phone. If you miss just 5 calls a week, that is $2,000 to $8,000 in high-ticket emergency repairs slipping right through your fingers every single month.\n\n"
                f"Hiring a full-time office receptionist costs $3,500/month, which makes zero sense for solo and small crews.\n\n"
                f"What completely solved this for us: an automated 8-second instant text-back trigger. The exact second a call is missed, our phone automatically shoots back:\n"
                f"\"Hey, this is Mike with the crew — currently on a job site with hands full. What emergency repair do you need help with?\"\n\n"
                f"The homeowner stops calling your competitors, texts back their address and repair issue in 30 seconds, and waits for you.\n\n"
                f"Full transparency: we packaged this exact automated workflow into {product_name} ({redirect_url}). It takes literally 2 minutes to turn on, runs in the background, and pays for itself on the very first emergency call it catches for you ({product_pitch}).\n\n"
                f"You can test a free 30-second live interactive simulation on your own phone right here: {redirect_url}\n\n"
                f"Stop letting Google competitors steal your hard-earned calls!"
            )

        # CAS 2 : E-commerce / Paniers abandonnés
        elif any(w in full_text for w in ["cart", "ecommerce", "shopify", "store", "panier", "shop"]):
            return (
                f"Hey {author_name}, totally feel your pain on this.\n\n"
                f"Standard email recovery sequences are getting decimated right now (average 14% open rates). By the time an email reaches the shopper 4 hours later, the impulse is gone and they've already bought elsewhere.\n\n"
                f"The only flow that consistently pulls 30%+ recovered revenue is an automated mobile SMS/WhatsApp notification triggered within 8 minutes of cart abandonment, offering an instant 1-click checkout link.\n\n"
                f"We actually built {product_name} ({redirect_url}) to handle this exact automation loop without custom code ({product_pitch}). It recovers 3 to 5 extra sales a week on autopilot.\n\n"
                f"You can test the preview workflow directly here: {redirect_url} — hope this helps plug the leak in your funnel!"
            )

        # CAS 3 : Vidéos démo SaaS / Créateurs timides
        elif any(w in full_text for w in ["video", "demo", "screen", "tiktok", "reels", "capcut", "record"]):
            return (
                f"Hey {author_name}, you are definitely not alone. 90% of technical builders hate recording their screen and doing voiceovers.\n\n"
                f"The issue is that video converts 4x higher on Twitter and Product Hunt than text. If you don't show the tool working in 15 seconds, people bounce.\n\n"
                f"Instead of spending 4 hours recording and editing, check out {product_name} ({redirect_url}) — you paste your landing page URL or upload 2 screenshots, and it automatically animates your app interface inside sleek 3D mockups with natural AI voiceover ({product_pitch}).\n\n"
                f"Test out a quick preview here: {redirect_url} — saves dozens of hours of awkward filming!"
            )

        # CAS GÉNÉRAL / B2B SaaS
        else:
            return (
                f"Hey {author_name}, this is a classic bottleneck that cost us months of wasted time before we figured it out.\n\n"
                f"The real problem is that doing this manually creates a delayed response lag that kills over 50% of your conversions. If a prospect has to wait more than 10 minutes for resolution, they lose interest.\n\n"
                f"We automated this entire process from scratch inside {product_name} ({redirect_url}) specifically to handle {product_pitch}.\n\n"
                f"It requires zero complex setup and pays for itself within the first week. You can test the live demo directly on the site: {redirect_url}\n\n"
                f"Hope this points you in the right direction!"
            )
