import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import time

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"
DRAFTS_FOLDER = "[Gmail]/&BCcENQRABD0EPgQyBDgEOgQ4-"

BASE_DIR = r"c:\Users\anton\Sync\Werkraports"

# ══════════════════════════════════════════════════════════════════════════════
# DRAFT 1: Centrum Particulieren Antwerpen (Team 78)
# ══════════════════════════════════════════════════════════════════════════════
BODY_PARTICULIEREN = """Geachte heer/mevrouw van Centrum Particulieren Antwerpen (Team 78),

Hierbij dien ik een aanvullend bezwaarschrift in tegen het aanslagbiljet personenbelasting aanslagjaar 2025 (inkomsten 2024), artikelnummer 248.037.001.

Dit bezwaar betreft een fundamentele inconsistentie en ongelijke behandeling in de verwerking van onze gezamenlijke belastingaangiften door de FOD Financiën. Terwijl de volledige belastingschuld voor het aanslagjaar 2025 ten bedrage van € 965,58 uitsluitend bij mij (Maiorov Denys) wordt ingevorderd, werd de belastingteruggave van het voorgaande aanslagjaar 2024 (art. 240.180.292) volledig uitbetaald aan de bankrekening van mijn ex-echtgenote — inclusief mijn persoonlijk aandeel daarin.

1. BEREKENING PERSOONLIJK AANDEEL (AJ 2024)
Volgens het aanslagbiljet AJ 2024 (inkomsten 2023), vastgesteld op 25 februari 2025, bedroeg de gezamenlijke belastingteruggave € 3.158,27. Dit bedrag werd op 30 april 2025 volledig uitbetaald op rekeningnummer BE33 9501 8732 7846 (rekening van ex-echtgenote Dudko Olena).

Uit de kolommen titularis/partner blijkt dat mijn persoonlijk aandeel in deze teruggave exact € 2.236,65 bedraagt:
- Bedrijfsvoorheffing partner (code 2286): € 1.425,65
- Werkbonus partner: € 281,00
- Belastingkrediet kinderen (kind: Anton Maiorov, geb. 09.02.2017): € 530,00
Totaal partner-aandeel (Denis): € 2.236,65.

Mijn persoonlijk aandeel van € 2.236,65 werd dus integraal uitbetaald aan de rekening van mijn ex-echtgenote, waardoor ik dit geld nooit heb ontvangen, terwijl ik de bedrijfsvoorheffing zelf via mijn werkgever heb afgedragen.

2. SCHENDING GELIJKHEIDSBEGINSEL
Ons huwelijk werd voltrokken in Oekraïne zonder Belgisch contract, waardoor het Belgische wettelijke stelsel (gemeenschap van goederen) van toepassing is. 

De FOD Financiën past de regels van het gemeenschappelijk vermogen echter asymmetrisch toe:
- Bij terugbetaling (AJ 2024) hanteert de FOD de regel van de "laatste bekende rekening" en keert de volledige teruggave (€3.158,27) uit aan mijn ex-echtgenote, waardoor zij onrechtmatig werd verrijkt met mijn aandeel van € 2.236,65 (ongerechtvaardigde verrijking art. 1235 BW).
- Bij invordering (AJ 2025) eist de FOD de volledige belastingschuld (€965,58) uitsluitend bij mij op.

Dit is een flagrante schending van het gelijkheidsbeginsel (art. 10-11 Grondwet): de administratie handelt inconsistent door gemeenschappelijke belangen in mijn nadeel uit te leggen bij invordering, maar te negeren bij teruggave.

3. CONCRETE VERZOEKEN
- VERREKENING: Ik verzoek formeel om mijn onbetaalde aandeel in de belastingteruggave AJ 2024 ten bedrage van € 2.236,65 te verrekenen met de belastingschuld AJ 2025 van € 965,58. Na deze interne verrekening resteert een saldo van € 1.271,07 in mijn voordeel.
- OPSCHORTING: Schort de invorderingsmaatregelen (dossier 203 855 179 990) op in afwachting van de inhoudelijke beslissing over dit bezwaar.

De echtscheidingsprocedure is aanhangig bij de familierechtbank te Antwerpen (AR 25/3256/A en AR 25/3083/A).

In bijlage vindt u alle bewijsstukken.

Met vriendelijke groeten,

Denys Maiorov
Rijksregisternummer: 82.11.02-629.43
Engelselei 81 bus 5, 2140 Borgerhout
denisvalerievichmayorov1@gmail.com
Tel.: 0479 280 165
"""

# ══════════════════════════════════════════════════════════════════════════════
# DRAFT 2: Advocaat (Julie Franssens)
# ══════════════════════════════════════════════════════════════════════════════
BODY_LAWYER = """Beste Meester Franssens,

In het kader van de lopende echtscheidingsprocedure (AR 25/3256/A en AR 25/3083/A) wil ik u informeren over een belangrijk financieel-fiscaal geschil met de FOD Financiën dat invloed heeft op de uiteindelijke vereffening-verdeling van ons huwelijksvermogen.

Het geschil betreft de onrechtmatige toeëigening van mijn belastingteruggave door mijn ex-partner, mevrouw Olena Dudko:

1. BELASTINGTERUGGAVE AJ 2024 (INKOMSTEN 2023)
Volgens het aanslagbiljet AJ 2024 (artikelnummer 240.180.292), vastgesteld op 25 februari 2025, bedroeg de gezamenlijke belastingteruggave € 3.158,27. De FOD Financiën heeft dit volledige bedrag op 30 april 2025 uitbetaald op de persoonlijke bankrekening van mijn ex-echtgenote (rekening BE33 9501 8732 7846).

Uit de kolommen titularis/partner op de berekening blijkt echter dat mijn persoonlijk aandeel in deze teruggave exact € 2.236,65 bedraagt:
- Mijn bedrijfsvoorheffing (code 2286): € 1.425,65
- Mijn werkbonus: € 281,00
- Het belastingkrediet voor ons afhankelijk kind Anton (geb. 09.02.2017): € 530,00
Totaal persoonlijk aandeel (Denis): € 2.236,65.

Mevrouw Dudko weigert dit bedrag aan mij over te dragen. Dit vormt een ongerechtvaardigde verrijking in haar hoofde (art. 1235 BW) ten koste van mijn vermogen.

2. BELASTINGSCHULD AJ 2025 (INKOMSTEN 2024)
Tegelijkertijd vordert de FOD Financiën nu een belastingschuld voor het aanslagjaar 2025 ten bedrage van € 965,58 uitsluitend bij mij in (dossier 203 855 179 990).

3. INGEDIEND BEZWAARSCHRIFT
Ik heb inmiddels een formeel en aanvullend bezwaarschrift ingediend bij de FOD Financiën (zowel bij het Centrum Particulieren als Invordering Antwerpen 3). Hierin betwist ik de asymmetrische behandeling en eis ik een interne verrekening van mijn onbetaalde tegoed AJ 2024 (€ 2.236,65) met de schuld AJ 2025 (€ 965,58). Indien dit wordt goedgekeurd, moet de FOD Financiën mij nog € 1.271,07 uitbetalen.

4. VERZOEK AAN U
Mocht de belastingadministratie deze verrekening weigeren op grond van hun interne administratieve richtlijnen, dan verzoek ik u vriendelijk om deze vordering van € 2.236,65 wegens ongerechtvaardigde verrijking formeel op te nemen in onze conclusies voor de familierechtbank. Dit bedrag moet integraal worden verrekend in mijn voordeel bij de uiteindelijke vereffening-verdeling van de gemeenschap.

Als bijlage voeg ik het aanslagbiljet AJ 2024 en AJ 2025, de aanmaning en mijn formeel bezwaarschrift toe.

Met vriendelijke groeten,

Denys Maiorov
Rijksregisternummer: 82.11.02-629.43
Engelselei 81 bus 5, 2140 Borgerhout
"""

# ══════════════════════════════════════════════════════════════════════════════
# DRAFT 3: Fiscale Bemiddelingsdienst
# ══════════════════════════════════════════════════════════════════════════════
BODY_BEMIDDELING = """Geachte bemiddelaar,

Hierbij dien ik een aanvraag tot bemiddeling in met betrekking tot een fiscaal geschil met de Centra Particulieren en Invordering Antwerpen van de FOD Financiën (schulddossier 203 855 179 990).

Het geschil betreft de onrechtvaardige en asymmetrische behandeling van terugbetalingen en invorderingen onder ons huwelijksstelsel (wettelijk stelsel - gemeenschap van goederen):

1. FEITEN
- Voor aanslagjaar 2024 (art. 240.180.292) bedroeg de teruggave € 3.158,27. Dit werd op 30 april 2025 volledig uitbetaald aan de persoonlijke rekening van mijn ex-echtgenote (rekening BE33 9501 8732 7846). Mijn persoonlijk aandeel daarin bedraagt € 2.236,65 (bedrijfsvoorheffing code 2286: € 1.425,65, werkbonus € 281,00, kinderkrediet € 530,00). De administratie weigerde mijn aandeel apart uit te betalen op grond van de 'laatste gekende rekening'.
- Voor aanslagjaar 2025 (art. 248.037.001) vordert dezelfde administratie nu een belastingschuld van € 965,58 uitsluitend bij mij (Maiorov Denys) in.

2. SCHENDING GELIJKHEIDSBEGINSEL
Dit leidt tot een situatie waarin de FOD Financiën de regels van het gemeenschappelijk vermogen in mijn nadeel toepast bij invordering (volledige schuld bij mij eisen), maar in mijn nadeel negeert bij terugbetaling (mijn aandeel volledig naar de ex-echtgenote laten gaan). Dit schendt het grondwettelijk gelijkheidsbeginsel (art. 10-11 Grondwet). Mijn ex-echtgenote heeft hierdoor € 2.236,65 ontvangen die rechtstreeks uit mijn beroepsinkomen voortvloeide, wat een ongerechtvaardigde verrijking (art. 1235 BW) vormt.

3. REEDS ONDERNOMEN STAPPEN
Ik heb op 17 mei 2026 formele bezwaarschriften ingediend bij zowel Centrum Particulieren (Team 78 - p78.nl@minfin.fed.be) als Centrum Invordering Antwerpen 3 (teaminv.antwerpen3@minfin.fed.be). Hierin vraag ik een interne verrekening tussen mijn tegoed AJ 2024 (€ 2.236,65) en de schuld AJ 2025 (€ 965,58), met uitbetaling van het saldo (€ 1.271,07) in mijn voordeel.

4. DOEL VAN BEMIDDELING
Ik verzoek uw tussenkomst om:
1. De belastingadministratie te bewegen tot een pragmatische en rechtvaardige interne verrekening tussen deze twee aanslagjaren.
2. De lopende invorderingsmaatregelen (dossier 203 855 179 990) op te schorten in afwachting van de uitkomst van deze bemiddeling.

In bijlage vindt u alle relevante stukken, waaronder de aanslagbiljetten en de bezwaarschriften.

Met vriendelijke groeten,

Denys Maiorov
Rijksregisternummer: 82.11.02-629.43
Engelselei 81 bus 5, 2140 Borgerhout
denisvalerievichmayorov1@gmail.com
Tel.: 0479 280 165
"""

# ── Attachments definition ───────────────────────────────────────────────────
ATTACHMENTS_ALL = [
    (os.path.join(BASE_DIR, "Brieven (2).pdf"),
     "FOD_Brief_11maart2026_DBRDC5F104A2B1C.pdf"),
    (os.path.join(BASE_DIR, "Aanslagbiljet 2025 (3).pdf"),
     "Aanslagbiljet_AJ2025_art248037001.pdf"),
    (os.path.join(BASE_DIR, "LawyerDocs", "Aanslagbiljet 2024 (1).pdf"),
     "Aanslagbiljet_AJ2024_art240180292_teruggave3158.pdf"),
    (os.path.join(BASE_DIR, "IMG_20260515_085236827.jpg"),
     "Aanmaning_4mei2026_schulddossier203855179990.jpg"),
]

ATTACHMENTS_LAWYER = [
    (os.path.join(BASE_DIR, "Aanslagbiljet 2025 (3).pdf"),
     "Aanslagbiljet_AJ2025_art248037001.pdf"),
    (os.path.join(BASE_DIR, "LawyerDocs", "Aanslagbiljet 2024 (1).pdf"),
     "Aanslagbiljet_AJ2024_art240180292_teruggave3158.pdf"),
    (os.path.join(BASE_DIR, "IMG_20260515_085236827.jpg"),
     "Aanmaning_4mei2026_schulddossier203855179990.jpg"),
]

def create_draft(mail, to, subject, body, attachments):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for filepath, display_name in attachments:
        if not os.path.exists(filepath):
            print(f"  ⚠ Attachment not found: {filepath}")
            continue
        with open(filepath, "rb") as f:
            data = f.read()
        part = MIMEBase("application", "octet-stream")
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=display_name,
        )
        msg.attach(part)
        print(f"  ✓ Attached: {display_name}")

    raw = msg.as_bytes()
    status, data = mail.append(
        f'"{DRAFTS_FOLDER}"',
        r"\Draft",
        imaplib.Time2Internaldate(time.time()),
        raw,
    )
    return status

def main():
    print("Connecting to Gmail IMAP...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)

    # 1. Draft to Centrum Particulieren Antwerpen (Team 78)
    print("\nCreating Draft 1: Centrum Particulieren Antwerpen (p78)...")
    st1 = create_draft(
        mail,
        "p78.nl@minfin.fed.be",
        "Aanvullend bezwaarschrift – AJ 2025 art. 248.037.001 & AJ 2024 art. 240.180.292 – RRN 82.11.02-629.43",
        BODY_PARTICULIEREN,
        ATTACHMENTS_ALL
    )
    print(f"Draft 1 Status: {st1}")

    # 2. Draft to Julie Franssens (Lawyer)
    print("\nCreating Draft 2: Advocaat Meester Julie Franssens...")
    st2 = create_draft(
        mail,
        "julie.franssens@advocaat.be",
        "Fiscale vordering echtscheiding – onrechtmatige uitbetaling AJ 2024 aan ex-partner – Dossier MAIOROV / DUDKO",
        BODY_LAWYER,
        ATTACHMENTS_LAWYER
    )
    print(f"Draft 2 Status: {st2}")

    # 3. Draft to Fiscale Bemiddelingsdienst (Mediation)
    print("\nCreating Draft 3: Fiscale Bemiddelingsdienst...")
    st3 = create_draft(
        mail,
        "fiscale.bemiddeling@minfin.fed.be",
        "Aanvraag tot bemiddeling – asymmetrische invordering en uitbetaling – schulddossier 203 855 179 990 – RRN 82.11.02-629.43",
        BODY_BEMIDDELING,
        ATTACHMENTS_ALL
    )
    print(f"Draft 3 Status: {st3}")

    mail.logout()
    print("\n✅ All drafts created successfully!")

if __name__ == "__main__":
    main()
