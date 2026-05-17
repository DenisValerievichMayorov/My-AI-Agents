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

# ── Letter body ────────────────────────────────────────────────────────────────
BODY = """Geachte mevrouw Speleman, geachte heer/mevrouw,

Ik verwijs naar uw brief van 11 maart 2026 (kenmerk DBRDC5F104A2B1C), waarin u de verdeling van de gemeenschappelijke belastingschuld AJ 2025 bepaalde als volgt:
- Maiorov Denys: € 965,58
- Maiorova Olena: € 0,00

Hierbij dien ik een aanvullend en formeel bezwaar in, gebaseerd op een fundamentele inconsistentie in de handelwijze van de FOD Financiën: terwijl de volledige belastingschuld AJ 2025 op mijn naam werd geplaatst, werd de belastingteruggave van het voorgaande aanslagjaar integraal uitbetaald aan de bankrekening van mijn ex-echtgenote — inclusief mijn persoonlijk aandeel in bedrijfsvoorheffing en belastingkredieten.

══════════════════════════════════════════════════
1. VASTGESTELD PROBLEEM: ASYMMETRIE TUSSEN INVORDERING EN TERUGBETALING
══════════════════════════════════════════════════

Volgens het aanslagbiljet aanslagjaar 2024 (inkomsten 2023), artikelnummer 240.180.292, vastgesteld op 25 februari 2025, bedroeg de gezamenlijke belastingteruggave:

€ 3.158,27

Deze teruggave werd door de FOD Financiën op 30 april 2025 volledig uitbetaald op rekeningnummer BE33 9501 8732 7846 — de bankrekening van mijn ex-echtgenote, mevrouw Maiorova Olena.

Uit de berekening op dat aanslagbiljet blijkt duidelijk — via de kolommen titularis/partner — dat dit bedrag als volgt is samengesteld:

  Component                              Bedrag       Op naam van
  ─────────────────────────────────────────────────────────────────
  BV titularis (code 1286)              €  889,99    Dudko Olena
  BV partner (code 2286)                €1.425,65    MAIOROV DENYS
  Werkbonus                             €  281,00    MAIOROV DENYS
  Belastingkrediet kinderen             €  530,00    MAIOROV DENYS
                                                     (kind: Anton, geb. 09.02.2017)
  ─────────────────────────────────────────────────────────────────
  TOTAAL AANDEEL PARTNER (DENIS)        €2.236,65    → rekening ex-echtgenote
  Totaal titularis (Olena)              €  889,99    → rekening ex-echtgenote
  BZSV-correctie                        €   31,63
  ─────────────────────────────────────────────────────────────────
  TOTAAL TERUGBETAALD                   €3.158,27    BE33 9501 8732 7846

Dit is verifieerbaar: de rechterkolom (partner = Denis) bedraagt exact €2.236,65
= BV €1.425,65 + Werkbonus €281,00 + Kinderkrediet €530,00.

Mijn persoonlijk aandeel van € 2.236,65 werd integraal uitbetaald aan de rekening
van mijn ex-echtgenote, terwijl ik de volledige bedrijfsvoorheffing via mijn
werkgever heb betaald en het belastingkrediet voor mijn afhankelijk kind aan mij
toebehoort.

Ik heb hier bezwaar tegen aangetekend. De FOD deelde mij mee dat dit beleid niet
kon worden herzien.

Dit leidt tot de volgende onrechtvaardige situatie:

  Handeling                                    Begunstigde
  ──────────────────────────────────────────────────────────────────
  Belastingteruggave AJ 2024 (€3.158,27)  → volledig rekening ex-echtgenote
  Mijn aandeel teruggave (€2.236,65)      → NIET aan mij uitbetaald
  Belastingschuld AJ 2025 (€965,58)       → volledig ingevorderd bij MIJ

══════════════════════════════════════════════════
2. JURIDISCHE GRONDSLAG: GELIJKHEIDSBEGINSEL EN ONGERECHTVAARDIGDE VERRIJKING
══════════════════════════════════════════════════

Ik betwist niet de formele bevoegdheid van de FOD Financiën om de belastingschuld
bij mij in te vorderen op grond van het wettelijk stelsel (gemeenschap van goederen).
Ons huwelijk werd voltrokken in Oekraïne, zonder Belgisch huwelijkscontract,
waardoor het Belgisch wettelijk stelsel van toepassing is.

Mijn bezwaar betreft echter de flagrante asymmetrie in de toepassing van dit principe:

• De FOD Financiën past het principe van de "laatste gekende rekening" toe en betaalt
  de volledige teruggave van €3.158,27 uit aan de rekening van mijn ex-echtgenote —
  ook al bedraagt mijn persoonlijk aandeel daarin €2.236,65.
• Tegelijkertijd wordt de volledige belastingschuld van €965,58 (AJ 2025) uitsluitend
  bij mij ingevorderd.

Dit is een schending van het gelijkheidsbeginsel (art. 10-11 Grondwet): dezelfde
regels worden inconsistent toegepast — in het voordeel van mijn ex-echtgenote bij
terugbetalingen, en in mijn nadeel bij invordering.

Bovendien heeft mijn ex-echtgenote hierdoor €2.236,65 ontvangen waarop zij geen recht
had. Dit vormt een ongerechtvaardigde verrijking ten hare laste (art. 1235 BW).

De familierechtbank te Antwerpen behandelt reeds de echtscheiding
(AR 25/3256/A en AR 25/3083/A). Ik verzoek u de uitkomst van deze procedure mee
te nemen in uw beslissing.

══════════════════════════════════════════════════
3. CONCRETE VERZOEKEN
══════════════════════════════════════════════════

1. VERREKENING: Mijn persoonlijk aandeel in de belastingteruggave AJ 2024
   (art. 240.180.292) bedraagt €2.236,65 (BV €1.425,65 + werkbonus €281,00 +
   kinderkrediet €530,00), uitbetaald op 30.04.2025 aan de rekening van mijn
   ex-echtgenote. Na verrekening met de huidige schuld van €965,58 bedraagt
   het saldo €1.271,07 in mijn voordeel.

2. MOTIVERING TERUGBETALING: Op welke rechtsgrondslag werd de volledige teruggave
   van €3.158,27 uitbetaald op rekening BE33 9501 8732 7846 (ex-echtgenote),
   terwijl €2.236,65 daarvan het persoonlijk aandeel van de partner (Maiorov Denys)
   betreft?

3. OPSCHORTING INVORDERING: Schort de invorderingsprocedure 203 855 179 990 op
   in afwachting van de inhoudelijke behandeling van dit bezwaar.

4. AFBETALINGSPLAN: Bevestig de ontvangst van mijn aanvraag voor een afbetalingsplan
   van ~€200/maand via MyMinfin (ingediend op 15 mei 2026).

══════════════════════════════════════════════════
BIJLAGEN
══════════════════════════════════════════════════

1. Brief FOD Financiën 11 maart 2026 (kenmerk DBRDC5F104A2B1C)
2. Aanslagbiljet AJ 2025 (art. 248.037.001) — schuld €965,58
3. Aanslagbiljet AJ 2024 (art. 240.180.292) — teruggave €3.158,27
4. Aanmaning 4 mei 2026 (schulddossier 203 855 179 990)
5. Bezwaarschrift 16 april 2026

Ik verzoek u dit bezwaar dringend en inhoudelijk te behandelen en mij binnen
15 werkdagen een gemotiveerd antwoord te bezorgen.

Met vriendelijke groeten,

Denys Maiorov
Rijksregisternummer: 82.11.02-629.43
Engelselei 81 bus 5, 2140 Borgerhout
denisvalerievichmayorov1@gmail.com
Tel.: 0479 280 165
"""

# ── Attachments ────────────────────────────────────────────────────────────────
BASE = r"c:\Users\anton\Sync\Werkraports"
ATTACHMENTS = [
    (os.path.join(BASE, "Brieven (2).pdf"),
     "FOD_Brief_11maart2026_DBRDC5F104A2B1C.pdf"),
    (os.path.join(BASE, "Aanslagbiljet 2025 (3).pdf"),
     "Aanslagbiljet_AJ2025_art248037001.pdf"),
    (os.path.join(BASE, "LawyerDocs", "Aanslagbiljet 2024 (1).pdf"),
     "Aanslagbiljet_AJ2024_art240180292_teruggave3158.pdf"),
    (os.path.join(BASE, "IMG_20260515_085236827.jpg"),
     "Aanmaning_4mei2026_schulddossier203855179990.jpg"),
]

def build_message():
    msg = MIMEMultipart()
    msg["From"]    = EMAIL
    msg["To"]      = "teaminv.antwerpen3@minfin.fed.be"
    msg["Subject"] = (
        "Aanvullend bezwaar – schulddossier 203 855 179 990 – "
        "AJ 2025 art. 248.037.001 – verrekening terugbetaling AJ 2024 "
        "(kenmerk DBRDC5F104A2B1C)"
    )
    msg.attach(MIMEText(BODY, "plain", "utf-8"))

    for filepath, display_name in ATTACHMENTS:
        if not os.path.exists(filepath):
            print(f"  ⚠ File not found, skipping: {filepath}")
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
        print(f"  ✓ Attached: {display_name}  ({len(data)//1024} KB)")

    return msg

def save_to_drafts(msg):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)

    raw = msg.as_bytes()
    status, data = mail.append(
        f'"{DRAFTS_FOLDER}"',
        r"\Draft",
        imaplib.Time2Internaldate(time.time()),
        raw,
    )
    mail.logout()
    return status

if __name__ == "__main__":
    print("Building email...")
    msg = build_message()
    print(f"\nSaving to Drafts folder: {DRAFTS_FOLDER}")
    status = save_to_drafts(msg)
    if status == "OK":
        print("\n✅ Draft saved successfully!")
        print(f"   To     : {msg['To']}")
        print(f"   Subject: {msg['Subject']}")
        print("   Open Gmail > Drafts to review before sending.")
    else:
        print(f"\n❌ Failed to save draft: {status}")
