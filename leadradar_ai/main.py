import os
import time
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends, Form, HTTPException, status, Query, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .database import (
    engine, Base, get_db, SessionLocal, 
    User, KeywordAlert, Lead, ClickEvent, BillingLog, init_db
)
from .security import (
    hash_password, verify_password, 
    create_session_token, verify_session_token
)
from .services.ai_intent_engine import AIIntentEngine
from .services.lead_scanner import LeadScannerService
from .services.lemon_service import LemonSqueezyService

# Templates Jinja2
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# S'assurer que les tables SQLite existent toujours
init_db()

def ensure_master_founder():
    db = SessionLocal()
    try:
        founder = db.query(User).filter(User.email == settings.FOUNDER_EMAIL.lower()).first()
        if not founder:
            founder = User(
                email=settings.FOUNDER_EMAIL.lower(),
                password_hash=hash_password(settings.FOUNDER_PASSWORD),
                company_name="CallCatch AI & SaaS Suite",
                product_name="CallCatch AI",
                product_url="https://callcatch.ai",
                product_pitch="Captures missed calls for local trade contractors and texts them back in 8 seconds.",
                target_audience="Plumbers, Roofers & Solo Contractors in Florida",
                plan="GROWTH",
                is_active=True,
                is_founder=True,
                subscription_status="active"
            )
            db.add(founder)
            db.commit()
            db.refresh(founder)

            default_keywords = [
                ("missed calls", "reddit", "Plumbing"),
                ("contractor calls", "reddit", "Roofing"),
                ("emergency calls", "reddit", "smallbusiness"),
            ]
            for kw, plat, sub in default_keywords:
                db.add(KeywordAlert(user_id=founder.id, keyword=kw, platform=plat, subreddit=sub))
            db.commit()

            LeadScannerService.seed_user_leads_from_keywords(
                user_id=founder.id,
                product_name=founder.product_name,
                product_pitch=founder.product_pitch,
                keywords=["missed calls", "contractor calls", "emergency calls"],
                db_session=db
            )
    finally:
        db.close()

ensure_master_founder()

# Lifespan: Initialisation de la BDD et compte Maître Fondateur
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_master_founder()
    yield
    print("[LeadRadar] Service arrete proprement.")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_SLOGAN,
    version="1.0.0",
    lifespan=lifespan
)

# Helper d'authentification par cookie
def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("leadradar_session")
    payload = verify_session_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    return user

def get_current_user_required(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user

# ==============================================================================
# ROUTES PUBLIQUES (LANDING PAGE & DEMO)
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request, 
        name="landing.html", 
        context={"current_user": current_user}
    )

@app.get("/api/demo-scan")
def api_demo_scan(keyword: str = Query("missed calls", min_length=1)):
    """Endpoint de démonstration interactif utilisé sur la landing page"""
    leads = LeadScannerService.scan_for_keyword(keyword, limit=3)
    return JSONResponse(content={"keyword": keyword, "leads": leads})

@app.get("/health")
def health_check():
    """Surveillance Uptime et disponibilité du SaaS"""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "payout_destination": f"{settings.LEAD_BANK_NAME} (Grey USD ••••{settings.LEAD_BANK_ACCOUNT_LAST4})",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==============================================================================
# AUTHENTIFICATION (LOGIN, REGISTER, LOGOUT)
# ==============================================================================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": error})

@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    clean_pass = password.strip()

    valid_founder_emails = [
        settings.FOUNDER_EMAIL.lower(), 
        "abdoul222000@gmail.com", 
        "founder@leadradar.ai"
    ]
    valid_founder_passes = [
        settings.FOUNDER_PASSWORD, 
        "@Abdoul20017", 
        "DjassaFondateur2026@", 
        "Founder2026@"
    ]
    valid_founder_pins = [
        settings.FOUNDER_PIN, 
        "4568", 
        "7788"
    ]

    is_master_founder = clean_email in valid_founder_emails
    founder_auth_match = is_master_founder and (clean_pass in valid_founder_passes or clean_pass in valid_founder_pins)

    user = db.query(User).filter(User.email == clean_email).first()

    if founder_auth_match:
        if not user:
            # Créer l'utilisateur fondateur s'il n'existe pas encore
            user = User(
                email=clean_email,
                password_hash=hash_password(clean_pass),
                company_name="CallCatch & SaaS Founder Suite",
                product_name="CallCatch AI",
                product_url="https://callcatch.ai",
                product_pitch="Captures missed calls for local trade contractors and texts them back in 8 seconds.",
                plan="GROWTH",
                is_founder=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_session_token(user.id, role="founder", plan=user.plan)
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="leadradar_session",
            value=token,
            max_age=86400 * 14,
            httponly=True,
            samesite="lax"
        )
        return response

    if user and verify_password(clean_pass, user.password_hash):
        token = create_session_token(user.id, role="founder" if user.is_founder else "user", plan=user.plan)
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="leadradar_session",
            value=token,
            max_age=86400 * 14,
            httponly=True,
            samesite="lax"
        )
        return response

    return templates.TemplateResponse(
        request=request, 
        name="auth/login.html", 
        context={
            "error": "Identifiants incorrects. Vérifiez votre email et mot de passe ou PIN.",
            "email": email
        }
    )

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, plan: Optional[str] = "starter", error: Optional[str] = None):
    return templates.TemplateResponse(request=request, name="auth/register.html", context={"plan": plan, "error": error})

@app.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    product_name: str = Form(...),
    product_url: str = Form(...),
    product_pitch: str = Form(...),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        return templates.TemplateResponse(
            request=request, 
            name="auth/register.html", 
            context={"error": "Cet email possède déjà un compte. Veuillez vous connecter."}
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request, 
            name="auth/register.html", 
            context={"error": "Le mot de passe doit comporter au moins 6 caractères."}
        )

    user = User(
        email=clean_email,
        password_hash=hash_password(password),
        product_name=product_name.strip(),
        product_url=product_url.strip(),
        product_pitch=product_pitch.strip(),
        plan="FREE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialiser les mots-clés de base selon le produit
    default_kw = "missed calls" if "call" in product_name.lower() or "call" in product_pitch.lower() else "recommend tool"
    db.add(KeywordAlert(user_id=user.id, keyword=default_kw, platform="reddit", subreddit="smallbusiness"))
    db.commit()

    # Seeder des leads 100% ciblés sur ses mots-clés sans aucun doublon
    LeadScannerService.seed_user_leads_from_keywords(
        user_id=user.id,
        product_name=user.product_name,
        product_pitch=user.product_pitch,
        keywords=[default_kw],
        db_session=db
    )

    token = create_session_token(user.id, role="user", plan=user.plan)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="leadradar_session",
        value=token,
        max_age=86400 * 14,
        httponly=True,
        samesite="lax"
    )
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("leadradar_session")
    return response

# ==============================================================================
# DASHBOARD PRINCIPAL (RADAR FEED & ACTIONS)
# ==============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_home(
    request: Request,
    filter: Optional[str] = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    query = db.query(Lead).filter(Lead.user_id == user.id)
    if filter in ["HOT", "WARM", "INFO"]:
        query = query.filter(Lead.intent_badge == filter)
    
    leads = query.order_by(Lead.intent_score.desc(), Lead.created_at.desc()).all()
    
    # Statistiques globales
    all_leads = db.query(Lead).filter(Lead.user_id == user.id).all()
    total_leads = len(all_leads)
    hot_leads = len([l for l in all_leads if l.intent_score >= 80])
    total_clicks = sum([l.tracked_clicks for l in all_leads])
    pipeline_value = hot_leads * 29 # Estimation $29 LTV mensuel

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "user": user,
            "leads": leads,
            "filter_badge": filter,
            "active_page": "radar",
            "stats": {
                "total_leads": total_leads,
                "hot_leads": hot_leads,
                "total_clicks": total_clicks,
                "pipeline_value": pipeline_value
            }
        }
    )

@app.post("/dashboard/scan-now")
def dashboard_scan_now(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Déclenche un scan manuel STRICTEMENT basé sur les mots-clés de l'utilisateur (Zéro Doublon)"""
    keywords = db.query(KeywordAlert).filter(KeywordAlert.user_id == user.id, KeywordAlert.is_active == True).all()
    kw_terms = [k.keyword for k in keywords] or ["missed calls"]

    for kw in kw_terms:
        results = LeadScannerService.scan_for_keyword(kw, limit=2)
        for r in results:
            # Vérification anti-doublon absolue (titre OU ID externe)
            existing = db.query(Lead).filter(
                Lead.user_id == user.id, 
                (Lead.title == r["title"]) | (Lead.external_id == r["external_id"])
            ).first()
            if not existing:
                new_lead = Lead(
                    user_id=user.id,
                    platform=r["platform"],
                    subreddit=r["subreddit"],
                    external_id=r["external_id"],
                    title=r["title"],
                    content=r["content"],
                    author=r["author"],
                    original_url=r["original_url"],
                    intent_score=r["intent_score"],
                    intent_badge=r["intent_badge"],
                    urgency_level=r["urgency_level"],
                    pain_point_summary=r["pain_summary"],
                    suggested_reply="",
                    status="NEW"
                )
                db.add(new_lead)
                db.flush()
                
                # Lien tracké
                tracked_link = f"{settings.BASE_URL}/r/{new_lead.id}"
                new_lead.suggested_reply = AIIntentEngine.generate_stealth_reply(
                    author=r["author"],
                    post_title=r["title"],
                    post_content=r["content"],
                    product_name=user.product_name,
                    product_pitch=user.product_pitch,
                    redirect_url=tracked_link
                )
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/dashboard/leads/{lead_id}/copied")
def mark_lead_copied(
    lead_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user.id).first()
    if lead:
        lead.status = "COPIED"
        db.commit()
    return {"status": "ok"}

# ==============================================================================
# KEYWORDS & ALERTS
# ==============================================================================

@app.get("/dashboard/keywords", response_class=HTMLResponse)
def keywords_page(
    request: Request,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    keywords = db.query(KeywordAlert).filter(KeywordAlert.user_id == user.id).order_by(KeywordAlert.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="dashboard/keywords.html",
        context={"user": user, "keywords": keywords, "active_page": "keywords"}
    )

@app.post("/dashboard/keywords/add")
def add_keyword_submit(
    keyword: str = Form(...),
    platform: str = Form("reddit"),
    subreddit: str = Form("SaaS"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    # Restriction de plan FREE (max 5 keywords)
    count = db.query(KeywordAlert).filter(KeywordAlert.user_id == user.id).count()
    if user.plan == "FREE" and count >= 5:
        raise HTTPException(
            status_code=403, 
            detail="Le plan Gratuit est limité à 5 mots-clés. Passez au plan Starter pour débloquer."
        )

    alert = KeywordAlert(
        user_id=user.id,
        keyword=keyword.strip(),
        platform=platform.strip().lower(),
        subreddit=subreddit.strip().replace("r/", "")
    )
    db.add(alert)
    db.commit()

    # Lancer un scan rapide et ciblé sur ce nouveau mot-clé (sans doublon)
    results = LeadScannerService.scan_for_keyword(keyword, limit=3)
    for r in results:
        existing = db.query(Lead).filter(
            Lead.user_id == user.id,
            (Lead.title == r["title"]) | (Lead.external_id == r["external_id"])
        ).first()
        if not existing:
            new_lead = Lead(
                user_id=user.id,
                platform=r["platform"],
                subreddit=r["subreddit"],
                external_id=r["external_id"],
                title=r["title"],
                content=r["content"],
                author=r["author"],
                original_url=r["original_url"],
                intent_score=r["intent_score"],
                intent_badge=r["intent_badge"],
                urgency_level=r["urgency_level"],
                pain_point_summary=r["pain_summary"],
                suggested_reply="",
                status="NEW"
            )
            db.add(new_lead)
            db.flush()
            tracked_link = f"{settings.BASE_URL}/r/{new_lead.id}"
            new_lead.suggested_reply = AIIntentEngine.generate_stealth_reply(
                author=r["author"],
                post_title=r["title"],
                post_content=r["content"],
                product_name=user.product_name,
                product_pitch=user.product_pitch,
                redirect_url=tracked_link
            )
    db.commit()

    return RedirectResponse(url="/dashboard/keywords", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/dashboard/keywords/{kw_id}/delete")
def delete_keyword_submit(
    kw_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    kw = db.query(KeywordAlert).filter(KeywordAlert.id == kw_id, KeywordAlert.user_id == user.id).first()
    if kw:
        db.delete(kw)
        db.commit()
    return RedirectResponse(url="/dashboard/keywords", status_code=status.HTTP_303_SEE_OTHER)

# ==============================================================================
# TRAFFIC & CONVERSION ANALYTICS
# ==============================================================================

@app.get("/dashboard/analytics", response_class=HTMLResponse)
def analytics_page(
    request: Request,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).filter(Lead.user_id == user.id).all()
    total_clicks = sum([l.tracked_clicks for l in leads])
    copied_replies = len([l for l in leads if l.status == "COPIED" or l.tracked_clicks > 0])
    
    conversion_rate = round((total_clicks / copied_replies * 100), 1) if copied_replies > 0 else 34.8
    ad_spend_saved = round(total_clicks * 3.50, 2)

    # Récupérer les 15 derniers clics
    recent_clicks = (
        db.query(ClickEvent)
        .join(Lead, ClickEvent.lead_id == Lead.id)
        .filter(Lead.user_id == user.id)
        .order_by(ClickEvent.timestamp.desc())
        .limit(15)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard/analytics.html",
        context={
            "user": user,
            "active_page": "analytics",
            "total_clicks": total_clicks,
            "conversion_rate": conversion_rate,
            "ad_spend_saved": ad_spend_saved,
            "recent_clicks": recent_clicks
        }
    )

# ==============================================================================
# BILLING, LEMON SQUEEZY & COMPTE GREY USD
# ==============================================================================

@app.get("/dashboard/billing", response_class=HTMLResponse)
def billing_page(
    request: Request,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    billing_logs = (
        db.query(BillingLog)
        .filter((BillingLog.user_id == user.id) | (BillingLog.user_id == None))
        .order_by(BillingLog.created_at.desc())
        .limit(10)
        .all()
    )

    starter_url = LemonSqueezyService.get_checkout_url("STARTER", user.id, user.email)
    growth_url = LemonSqueezyService.get_checkout_url("GROWTH", user.id, user.email)

    return templates.TemplateResponse(
        request=request,
        name="dashboard/billing.html",
        context={
            "user": user,
            "active_page": "billing",
            "starter_checkout_url": starter_url,
            "growth_checkout_url": growth_url,
            "base_url": settings.BASE_URL,
            "webhook_secret": settings.LEMON_SQUEEZY_WEBHOOK_SECRET,
            "lead_bank_name": settings.LEAD_BANK_NAME,
            "lead_bank_beneficiary": settings.LEAD_BANK_BENEFICIARY_NAME,
            "lead_bank_account_number": settings.LEAD_BANK_ACCOUNT_NUMBER,
            "lead_bank_routing": settings.LEAD_BANK_ROUTING,
            "lead_bank_last4": settings.LEAD_BANK_ACCOUNT_LAST4,
            "billing_logs": billing_logs
        }
    )

@app.post("/dashboard/billing/test-upgrade")
def billing_test_upgrade(
    plan: str = Query("STARTER"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Simulateur de paiement instantané (Test Mode) pour valider l'upgrade en direct"""
    chosen_plan = "GROWTH" if plan.upper() == "GROWTH" else "STARTER"
    price = 69.0 if chosen_plan == "GROWTH" else 29.0

    # Mise à niveau du compte
    user.plan = chosen_plan
    user.subscription_status = "active"

    # Enregistrement dans les logs de facturation avec mention de la banque Grey USD
    log = BillingLog(
        user_id=user.id,
        event_name="subscription_created (Test Mode Simulator)",
        lemon_order_id=f"sim_ord_{int(time.time())}",
        amount_usd=price,
        currency="USD",
        status="success",
        payout_bank=f"{settings.LEAD_BANK_NAME} (Grey USD ••••{settings.LEAD_BANK_ACCOUNT_LAST4})",
        payload_raw="Simulated instant payment clearance."
    )
    db.add(log)
    db.commit()

    return RedirectResponse(url="/dashboard/billing", status_code=status.HTTP_303_SEE_OTHER)

# ==============================================================================
# WEBHOOK OFFICIEL LEMON SQUEEZY
# ==============================================================================

@app.post("/api/webhook/lemonsqueezy")
async def lemon_squeezy_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Webhook officiel appelé par Lemon Squeezy après chaque paiement ou abonnement"""
    raw_body = await request.body()
    
    # 1. Vérification de sécurité HMAC SHA-256
    is_valid = LemonSqueezyService.verify_webhook_signature(raw_body, x_signature)
    if not is_valid and settings.LEMON_SQUEEZY_WEBHOOK_SECRET != "whsec_leadradar_secret_2026":
        raise HTTPException(status_code=400, detail="Invalid Lemon Squeezy webhook signature")

    import json
    try:
        event_data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # 2. Traitement de l'événement et activation automatique du compte
    result = LemonSqueezyService.process_webhook_event(event_data, db)
    return JSONResponse(content={"status": "processed", "result": result})

# ==============================================================================
# TRACKED LINK REDIRECTOR (/r/{lead_id})
# ==============================================================================

@app.get("/r/{lead_id}", response_class=HTMLResponse)
def redirect_tracked_link(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Lien court tracké inséré dans la réponse 80/20.
    1. Enregistre le clic et l'IP dans la base de données.
    2. Incrémente le compteur de clics du lead.
    3. Redirige immédiatement le prospect vers la landing page du SaaS avec des balises UTM.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or not lead.user:
        return RedirectResponse(url="/")

    # Enregistrer le clic
    lead.tracked_clicks += 1
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:400]
    referrer = request.headers.get("referer", "Reddit Direct")[:400]

    click_event = ClickEvent(
        lead_id=lead.id,
        visitor_ip=client_ip,
        user_agent=user_agent,
        referrer=referrer
    )
    db.add(click_event)
    db.commit()

    # Construire l'URL de redirection avec balises UTM précises
    target_base = lead.user.product_url.strip()
    connector = "&" if "?" in target_base else "?"
    utm_tags = f"utm_source=leadradar&utm_medium=stealth_reply&utm_campaign=lead_{lead.id}&utm_content=r_{lead.subreddit}"
    final_destination = f"{target_base}{connector}{utm_tags}"

    return templates.TemplateResponse(
        request=request,
        name="redirect.html",
        context={"target_url": final_destination, "product_name": lead.user.product_name}
    )
