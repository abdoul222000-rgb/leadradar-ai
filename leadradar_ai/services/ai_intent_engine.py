import re
from typing import Dict, Any, List
import httpx
from ..config import settings

class AIIntentEngine:
    """
    Moteur d'analyse psychologique d'intention d'achat et 
    générateur de réponses furtives à haute conversion (Règle 80/20).
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
        
        score = 45 # Base score
        triggers_found = []
        
        # 1. Patterns d'intention directe (+8 à +15 points chacun)
        for pattern in cls.HIGH_INTENT_PATTERNS:
            if re.search(pattern, full_text):
                score += 12
                triggers_found.append(pattern.replace(r"\b", "").replace("(?:you|i)", "you/i"))
                
        # 2. Urgence (+10 points)
        urgency = "LOW"
        for pattern in cls.URGENCY_PATTERNS:
            if re.search(pattern, full_text):
                score += 10
                urgency = "HIGH"
                triggers_found.append("Urgence détectée")
                break
                
        # 3. Frustration envers un concurrent existant (+15 points)
        for pattern in cls.NEGATIVE_COMPETITOR_PATTERNS:
            if re.search(pattern, full_text):
                score += 14
                triggers_found.append("Insatisfaction concurrent")
                break

        # Plafond et plancher
        score = min(max(score, 35), 98)
        
        # Classification
        if score >= 80:
            badge = "HOT"
            urgency = "HIGH" if urgency == "HIGH" else "MEDIUM"
        elif score >= 60:
            badge = "WARM"
            urgency = "MEDIUM"
        else:
            badge = "INFO"
            urgency = "LOW"
            
        # Résumé du problème
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
        """Extrait en 1 phrase le besoin ou le blocage"""
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
        style: str = "helpful_peer"
    ) -> str:
        """
        Génère une réponse respectant la règle 80/20 :
        80% de conseil d'expert bienveillant (valeur pure)
        20% de recommandation subtile et naturelle avec lien tracké.
        """
        author_name = f"u/{author}" if author and not author.startswith("u/") else (author or "there")
        
        if style == "helpful_peer":
            return (
                f"Hey {author_name}, this is a classic bottleneck that hit a lot of us early on.\n\n"
                f"Two quick practical tips that usually fix 80% of this without overcomplicating things:\n"
                f"1. Simplify the initial workflow: map out the exact repetitive friction before trying to patch it with 5 different tools.\n"
                f"2. Automate the follow-up or capture immediately. Most lost opportunities happen within the first 10 minutes of delayed response.\n\n"
                f"Full transparency: I ended up having this exact headache a few months ago, so I built {product_name} ({redirect_url}) "
                f"specifically to handle this automatically ({product_pitch}).\n\n"
                f"Either way, happy to share more details on how we structured the workflow if you're exploring DIY alternatives!"
            )
        elif style == "direct_solver":
            return (
                f"Totally relate to this friction. Here is the quickest fix:\n\n"
                f"Most people get stuck trying to do this manually across spreadsheets or clunky platforms, which inevitably drops the ball.\n\n"
                f"If you want to solve it permanently, check out {product_name} ({redirect_url}) — it was designed specifically for {product_pitch}.\n\n"
                f"Hope this points you in the right direction!"
            )
        else: # insight
            return (
                f"Great question. From testing this in our own stack:\n\n"
                f"The key is eliminating the manual lag between the request and the solution. "
                f"Even small delays kill conversion rates by 50%+.\n\n"
                f"We actually automated this entire loop inside {product_name} ({redirect_url}). "
                f"Feel free to grab the workflow or test the preview if you want to see how it operates!"
            )
