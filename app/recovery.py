"""Short recovery text from the provided mock-site specification; no outbound links."""

DEFAULT = [
    "Stop. Do not reply or call numbers from the message.",
    "Contact the company using the number on your bill, card, or official app.",
    "Change the password you entered, and anywhere else you reused it.",
    "Turn on two-step verification and an account PIN where offered.",
    "Report the text by forwarding it to 7726 (SPAM).",
]
EXTRAS = {
    "payment": [
        "Call your card issuer using the number on your card. Ask about blocking the card and watch for unfamiliar charges."
    ],
    "identity": [
        "Consider a credit freeze with the credit bureaus and watch your credit reports."
    ],
    "gift_card": [
        "Contact the gift-card issuer using the number on the card. Keep your receipt."
    ],
}


def checklist(category: str) -> dict:
    normalized = (
        category
        if category in {*EXTRAS, "account_suspension", "account_security"}
        else "general"
    )
    return {"category": normalized, "steps": [*EXTRAS.get(normalized, []), *DEFAULT]}
