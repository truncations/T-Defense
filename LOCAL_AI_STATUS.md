# Local AI milestone status

Implemented: offline evidence projection and strict candidate-output validation
in `app/local_ai.py`, with synthetic regression tests. This is a preparation
boundary, not an inference integration or a working website investigation button.

No model is installed or called. No free-form AI summary is generated. Candidate
outputs can select observed categories only; they cannot change a verdict, invoke
tools, introduce claims, or omit incomplete/simulated coverage labels. Quality
evaluation is still necessary before allowing model-written summaries.

Next step: benchmark a small quantized Ollama model with synthetic evidence only. Isolated
real-page inspection is not planned in this repository.

The existing mock-only investigator remains unchanged. There is no host-browser
fallback.
Do not expose Ollama's unauthenticated API to your LAN. No real-site form typing or
submission is enabled. Conversation collection remains disabled.