"""Classement des mails par l'API Claude (modèle Haiku).

Le modèle répond via un outil imposé, ce qui garantit une réponse structurée.
En cas de doute ou d'erreur, le mail reste dans la boîte de réception.
"""
from dataclasses import dataclass

import anthropic

IMPORTANT = "important"
LESS_IMPORTANT = "moins_important"
SUSPECT = "suspect"

_TOOL = {
    "name": "classer_mail",
    "description": "Enregistre le classement d'un mail.",
    "input_schema": {
        "type": "object",
        "properties": {
            "categorie": {"type": "string", "enum": [SUSPECT, IMPORTANT, LESS_IMPORTANT]},
            "raison": {"type": "string", "description": "Justification en une phrase courte, en français."},
        },
        "required": ["categorie", "raison"],
    },
}

_SYSTEM = """Tu tries les mails d'une boîte personnelle.

Première passe, sécurité : classe en « suspect » tout mail dont l'expéditeur
semble frauduleux (hameçonnage, usurpation d'identité, arnaque) : demande
urgente d'identifiants, de paiement ou de clic sur un lien, expéditeur qui
imite une banque, une administration ou un service connu sans en venir,
fautes et menaces typiques. Les signaux techniques fournis sont des indices,
pas des preuves : une newsletter légitime peut en déclencher un.

Sinon, classe en « important » ou « moins_important ». Applique les critères personnels
ci-dessous ; s'ils ne tranchent pas, un mail est important quand il demande
une action, concerne de l'argent, de l'administratif, la santé, ou vient
d'une vraie personne qui écrit directement. Les newsletters, publicités et
notifications automatiques sont moins importantes.

Critères personnels :
{criteria}"""


@dataclass
class Classification:
    category: str
    reason: str


class Classifier:
    def __init__(self, api_key: str, model: str, criteria: str):
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=3)
        self.model = model
        self.system = _SYSTEM.format(criteria=criteria.strip() or "(aucun)")

    def classify(self, sender: str, subject: str, body: str,
                 signals: list[str] = ()) -> Classification:
        hints = "; ".join(signals) or "aucun"
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            system=self.system,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": _TOOL["name"]},
            messages=[{
                "role": "user",
                "content": f"De : {sender}\nObjet : {subject}\nSignaux techniques : {hints}\n\n{body}",
            }],
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        category = block.input.get("categorie")
        if category not in (SUSPECT, IMPORTANT, LESS_IMPORTANT):
            raise ValueError(f"Catégorie inattendue : {category!r}")
        return Classification(category, str(block.input.get("raison", "")))
